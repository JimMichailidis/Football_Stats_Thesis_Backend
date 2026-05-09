from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

engine = create_engine("mysql+pymysql://root:@localhost/footballdatabase")

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        target_player = data.get('name')
        selected_metrics = data.get('metrics') 
        selected_positions = data.get('positions', [])

        df = pd.read_sql("SELECT * FROM epl_player_stats_24_25_per90", engine)
        
        if target_player not in df['Player_Name'].values:
            return jsonify({"error": "Player not found"}), 404

        # data cleaning: replace inf with NaN and fill with 0
        df[selected_metrics] = df[selected_metrics].replace([np.inf, -np.inf], np.nan).fillna(0)

        # position filtering
        if selected_positions:
            mask = df['Position'].isin(selected_positions) | (df['Player_Name'] == target_player)
            df_comp = df[mask].copy()
        else:
            df_comp = df.copy()

        # Scaling & Similarity
        features = df_comp[selected_metrics].values
        scaler = MinMaxScaler()
        scaled_features = scaler.fit_transform(features)
        scaled_features = np.nan_to_num(scaled_features)

        target_idx = df_comp[df_comp['Player_Name'] == target_player].index[0]
        pos_in_matrix = df_comp.index.get_loc(target_idx)
        
        target_vector = scaled_features[pos_in_matrix].reshape(1, -1)
        sim_scores = cosine_similarity(target_vector, scaled_features)[0]

        df_comp['similarity'] = sim_scores * 100

        recommendations = df_comp[df_comp['Player_Name'] != target_player] \
                            .sort_values(by='similarity', ascending=False) \
                            .head(5)

        results = []
        for _, row in recommendations.iterrows():
            results.append({
                "name": row['Player_Name'],
                "team": row['Club'],
                "position": row['Position'],
                "similarity": round(float(row['similarity']), 2)
            })
        return jsonify(results)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)