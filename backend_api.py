from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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


#In Memory Cache

DF_CACHE = None

def load_data(force_reload: bool = False) -> pd.DataFrame:
    global DF_CACHE
    if DF_CACHE is None or force_reload:
        print("🔄 Φόρτωση δεδομένων από τη MySQL στη μνήμη...")
        DF_CACHE = pd.read_sql("SELECT * FROM epl_player_stats_24_25_per90", engine)
        print(f"✅ Φορτώθηκαν επιτυχώς {len(DF_CACHE)} παίκτες.")

    return DF_CACHE.copy()


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
    df = df.reset_index(drop=True)
    features = df[metrics].values
    scaler = MinMaxScaler()
    scaled = np.nan_to_num(scaler.fit_transform(features))

    #Normalized DataFrame για radar chart
    scaled_df = pd.DataFrame(scaled, columns=metrics, index=df.index)
    scaled_df['Player_Name'] = df['Player_Name'].values

    #Θέση target παίκτη
    target_pos = df[df['Player_Name'] == target].index[0]
    target_vec = scaled[target_pos].reshape(1, -1)

    sim_scores = np.nan_to_num(cosine_similarity(target_vec, scaled)[0])
    df = df.copy()
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
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid or empty JSON request"}), 400
                
        target_player      = data.get('name')
        selected_metrics   = data.get('metrics')
        selected_positions = data.get('positions', [])
        
        if not target_player:
            return jsonify({"error": "No player name provided"}), 400

        if not selected_metrics or not isinstance(selected_metrics, list):
            return jsonify({"error": "Δεν επιλέχθηκαν έγκυρες μετρήσεις"}), 400

        if not isinstance(selected_positions, list):
            selected_positions = []

        #Φόρτωση δεδομένων
        df = load_data()

        #Φίλτρο ελάχιστων λεπτών συμμετοχής
        min_minutes = data.get('min_minutes', 270)
        mask_mins = (df['Minutes'] >= min_minutes) | (df['Player_Name'] == target_player)
        df = df[mask_mins].copy()

        if target_player not in df['Player_Name'].values:
            return jsonify({"error": "Player not found"}), 400

        #Έλεγχος αν τα metrics υπάρχουν στη βάση
        invalid_metrics = [m for m in selected_metrics if m not in df.columns]
        if invalid_metrics:
            return jsonify({"error": f"Invalid metrics: {invalid_metrics}"}), 400
        
        #Καθαρισμός
        df = clean_metrics(df, selected_metrics)

        #Inversion αρνητικών metrics
        df = invert_negative_metrics(df, selected_metrics)

        #Φίλτρο θέσεων
        df = filter_positions(df, selected_positions, target_player)

        #Similarity + normalized values για radar
        df_scored, scaled_df = compute_similarity(df, selected_metrics, target_player)

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

@app.route('/reload', methods=['POST', 'GET'])
def reload_cache():
    try:
        df = load_data(force_reload=True)
        return jsonify({
            "message": "Η μνήμη ανανεώθηκε επιτυχώς!",
            "total_players": len(df)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Entry point
if __name__ == '__main__':
    load_data()
    app.run(port=5001, debug=False)