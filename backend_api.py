from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity


# App & DB setup 
app = Flask(__name__)
CORS(app)
engine = create_engine("mysql+pymysql://root:@localhost/footballdatabase")


# Helper: φόρτωση δεδομένων από DB 
def load_data() -> pd.DataFrame:
    return pd.read_sql("""
    SELECT 
        p.*,
        r.Fouls,
        r.Own_Goals,
        r.Clearances_Off_Line,
        r.Goals_Prevented,
        r.gDuels_Percentage,
        r.Aerial_Duels_Percentage,
        r.Saves_Percentage,
        r.xG_Threat_Conceded
    FROM epl_player_stats_24_25_per90 p
    LEFT JOIN epl_player_stats_24_25 r ON p.ID = r.ID
""", engine)


# Helper: καθαρισμός inf/NaN σε επιλεγμένες στήλες 
def clean_metrics(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    df[metrics] = df[metrics].replace([np.inf, -np.inf], np.nan).fillna(0)
    return df


# Helper: φιλτράρισμα θέσεων (κρατά πάντα τον target παίκτη) 
def filter_positions(df: pd.DataFrame, positions: list, target: str) -> pd.DataFrame:
    if not positions:
        return df.copy()

    mask = df['Position'].isin(positions) | (df['Player_Name'] == target)
    return df[mask].copy()


# Helper: υπολογισμός cosine similarity 
def compute_similarity(df: pd.DataFrame, metrics: list, target: str) -> pd.DataFrame:
    features = df[metrics].values
    scaler = MinMaxScaler()
    scaled_features = np.nan_to_num(scaler.fit_transform(features))

    # Θέση του target παίκτη στον πίνακα
    target_idx = df[df['Player_Name'] == target].index[0]
    target_pos = df.index.get_loc(target_idx)
    target_vector = scaled_features[target_pos].reshape(1, -1)

    sim_scores = cosine_similarity(target_vector, scaled_features)[0]
    df['similarity'] = sim_scores * 100
    return df


# Endpoint: POST /recommend 
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json

        target_player = data.get('name')
        selected_metrics = data.get('metrics')
        selected_positions = data.get('positions', [])

        # 1. Φόρτωση & καθαρισμός
        df = load_data()

        if target_player not in df['Player_Name'].values:
            return jsonify({"error": "Player not found"}), 404

        df = clean_metrics(df, selected_metrics)

        # 2. Φίλτρο θέσεων
        df_filtered = filter_positions(df, selected_positions, target_player)

        # 3. Similarity
        df_scored = compute_similarity(df_filtered, selected_metrics, target_player)

        # 4. Top 5 αποτελέσματα (χωρίς τον ίδιο τον παίκτη)
        top5 = (
            df_scored[df_scored['Player_Name'] != target_player]
            .sort_values(by='similarity', ascending=False)
            .head(5)
        )

        results = [
            {
                "name":row['Player_Name'],
                "team":row['Club'],
                "position":row['Position'],
                "similarity":round(float(row['similarity']), 2),
            }
            for _, row in top5.iterrows()
        ]

        return jsonify(results)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# Entry point 
if __name__ == '__main__':
    app.run(port=5001, debug=True)