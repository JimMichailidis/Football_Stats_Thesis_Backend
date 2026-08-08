from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, false
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity


#App & DB setup
app = Flask(__name__)
CORS(app)
engine = create_engine("mysql+pymysql://root:@localhost/footballdatabase")


#Metrics που είναι αρνητικά (όσο χαμηλότερα τόσο καλύτερα)
#Γίνεται inversion πριν το scaling ώστε το cosine similarity να λειτουργεί σωστά
NEGATIVE_METRICS = [
    'Goals_Conceded_per90',
    'Big_Chances_Missed_per90',
    'Dispossessed_per90',
    'Offsides_per90',
    'Fouls_per90',
    'Own_Goals_per90',
    'xG_Threat_Conceded',
]


#Helper functions

def load_data() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM epl_player_stats_24_25_per90", engine)


def clean_metrics(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    df[metrics] = df[metrics].replace([np.inf, -np.inf], np.nan).fillna(0)
    return df


def invert_negative_metrics(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    for col in NEGATIVE_METRICS:
        if col in metrics:
            df[col] = df[col].max() - df[col]
    return df


def filter_positions(df: pd.DataFrame, positions: list, target: str) -> pd.DataFrame:
    if not positions:
        return df.copy()
    mask = df['Position'].isin(positions) | (df['Player_Name'] == target)
    return df[mask].copy()


def compute_similarity(df: pd.DataFrame, metrics: list, target: str):
    features = df[metrics].values
    scaler   = MinMaxScaler()
    scaled   = np.nan_to_num(scaler.fit_transform(features))

    #Normalized DataFrame για radar chart
    scaled_df = pd.DataFrame(scaled, columns=metrics, index=df.index)
    scaled_df['Player_Name'] = df['Player_Name'].values

    #Θέση target παίκτη
    target_idx = df[df['Player_Name'] == target].index[0]
    target_pos = df.index.get_loc(target_idx)
    target_vec = scaled[target_pos].reshape(1, -1)

    sim_scores       = cosine_similarity(target_vec, scaled)[0]
    df               = df.copy()
    df['similarity'] = sim_scores * 100

    return df, scaled_df


def build_radar_data(scaled_df: pd.DataFrame, metrics: list,
                     target: str, top5_names: list) -> dict:
    radar = {}

    #Target player
    target_row = scaled_df[scaled_df['Player_Name'] == target]
    if not target_row.empty:
        radar[target] = [round(float(v), 3) for v in target_row[metrics].values[0]]

    #Top 5
    for name in top5_names:
        row = scaled_df[scaled_df['Player_Name'] == name]
        if not row.empty:
            radar[name] = [round(float(v), 3) for v in row[metrics].values[0]]

    return radar


#Endpoint: POST /recommend
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json

        target_player      = data.get('name')
        selected_metrics   = data.get('metrics')
        selected_positions = data.get('positions', [])

        #Φόρτωση & καθαρισμός
        df = load_data()

        if target_player not in df['Player_Name'].values:
            return jsonify({"error": "Player not found"}), 400

        if not selected_metrics:
            return jsonify({"error": "No metrics selected"}), 400

        df = clean_metrics(df, selected_metrics)

        #Φίλτρο θέσεων
        df_filtered = filter_positions(df, selected_positions, target_player)

        #Inversion αρνητικών metrics (πριν το filter για σωστό max())
        df_filtered = invert_negative_metrics(df_filtered, selected_metrics)

        #Similarity + normalized values για radar
        df_scored, scaled_df = compute_similarity(df_filtered, selected_metrics, target_player)

        #Top 5 (χωρίς τον target)
        top5 = (
            df_scored[df_scored['Player_Name'] != target_player]
            .sort_values(by='similarity', ascending=False)
            .head(5)
        )

        top5_names = top5['Player_Name'].tolist()

        results = [
            {
                "name":       row['Player_Name'],
                "team":       row['Club'],
                "position":   row['Position'],
                "similarity": round(float(row['similarity']), 2),
            }
            for _, row in top5.iterrows()
        ]

        #Radar chart data
        radar_data = build_radar_data(scaled_df, selected_metrics, target_player, top5_names)

        return jsonify({
            "results": results,
            "radar":   radar_data,
            "metrics": selected_metrics,
            "target":  target_player,
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


#Entry point
if __name__ == '__main__':
    app.run(port=5001, debug=false)