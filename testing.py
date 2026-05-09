import pymysql
import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
import tkinter as tk
from tkinter import ttk
from sklearn.metrics.pairwise import cosine_similarity

# SQL Connection
user = 'root'
password = ''
host = 'localhost'
port = '3306'
database = 'FootballDatabase'

engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")

#Φόρτωση per90 table
df = pd.read_sql("SELECT * FROM epl_player_stats_24_25_per90", engine)

#MinMax PER POSITION
metrics = [col for col in df.columns if '_per90' in col]
df_norm = df.copy()
for pos in df['Position'].unique():
    mask = df['Position'] == pos
    scaler = MinMaxScaler()
    df_norm.loc[mask, metrics] = scaler.fit_transform(df[mask][metrics])

df_norm.to_sql('epl_normalized_per90', engine, if_exists='replace', index=False)
print("Saved to SQL: epl_normalized_per90")











#παραθυρο προβολης πινακα
root = tk.Tk()
root.title("epl_player_stats_24_25")

frame = ttk.Frame(root)
frame.pack(fill="both", expand=True)

tree = ttk.Treeview(frame, columns=list(df.columns), show="headings")

# headers
for col in df.columns:
    tree.heading(col, text=col)
    tree.column(col, width=100, anchor="w")

# rows
for _, row in df.iterrows():
    tree.insert("", "end", values=list(row))

# scrollbars
vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")

frame.rowconfigure(0, weight=1)
frame.columnconfigure(0, weight=1)

root.mainloop()

#κανονικοποιηση δεδομενων

# Μετά το df_norm.to_sql() - επιλογή μετρήσεων & θέσης
POSITION = 'ST'  # Αλλάζεις ανά θέση
metrics = ['xG_per90', 'xAG_per90', 'Shots_per90', 'Progressive_Carries_per90']  # Αλλάζεις ανάλογα με τη θέση

# Φιλτράρισμα θέσης & handling NaN
player_df = df_norm[df_norm['Position'] == POSITION][['Player_Name', 'Club'] + metrics].copy()
player_df = player_df.dropna()  # Αφαίρεση παίκτες με κενά

# Features matrix (μόνο metrics)
X = player_df[metrics].values

# Cosine similarity matrix (όλοι με όλους)
similarity_matrix = cosine_similarity(X)

# DataFrame με scores & indices
sim_df = pd.DataFrame(
    similarity_matrix,
    index=player_df['Player_Name'],
    columns=player_df['Player_Name']
)

print("Top 5 similar ST:")
for i, player in enumerate(player_df['Player_Name'].head(10)):  # Πρώτοι 10
    top_sim = sim_df[player].sort_values(ascending=False).head(6)  # Εαυτός + top5
    print(f"\n{player} ({player_df[player_df['Player_Name']==player]['Club'].iloc[0]}):")
    print(top_sim)

# GUI: Εισαγωγή player -> top5
def find_similar(target_player):
    if target_player in sim_df.index:
        top5 = sim_df[target_player].sort_values(ascending=False).head(6)[1:]  # Χωρίς εαυτό
        return pd.DataFrame({
            'Player': top5.index,
            'Similarity': top5.values,
            'Team': [player_df[player_df['Player_Name']==p]['Club'].iloc[0] for p in top5.index]
        })
    return None



