import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# --------- Fonctions utilitaires ---------
def extract_matchday_num(j):
    match = re.match(r"J(\d+)", str(j))
    return int(match.group(1)) if match else -1

# --------- Streamlit App ---------
st.set_page_config(page_title="Top Player Rankings")
st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=0)

season_code = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

if season_code:
    path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}", "players"))

    df_scores_players = pd.read_csv(os.path.join(path_folder, "ratings/data_players.csv"))
    df_scores_goalkeepers = pd.read_csv(os.path.join(path_folder, "ratings/data_goals.csv"))
    df_scores = pd.concat([df_scores_players, df_scores_goalkeepers], ignore_index=True)

positions = df_scores['General Position'].dropna().unique()
all_positions = st.sidebar.checkbox("All positions", value=True)
selected_positions = positions if all_positions else [st.sidebar.selectbox("Choose a position", positions)]

leagues = sorted(df_scores["League"].dropna().unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

matchdays = sorted(df_scores["Game Week"].dropna().unique(), key=extract_matchday_num)
all_matchdays = st.sidebar.checkbox("All matchdays", value=True)
selected_matchdays = matchdays if all_matchdays else [st.sidebar.selectbox("Choose a matchday", matchdays)]

top_n = st.sidebar.slider("Number of players to display", 5, 100, 30)
min_matches = st.sidebar.slider("Minimum matches played", 1, 50, 25)
age_max = st.sidebar.slider("Maximum age", 15, 50, 50)

df_scores_filtered = df_scores[
    (df_scores["League"].isin(selected_leagues)) &
    (df_scores["Game Week"].isin(selected_matchdays))
]

df_scores_filtered["Matches"] = 1
df_agg = df_scores_filtered.groupby("Player", as_index=False).agg({
    "Team": lambda x: sorted(list(set(x.dropna()))),
    "League": lambda x: sorted(list(set(x.dropna()))),
    "Position": lambda x: x.mode().iloc[0] if not x.mode().empty else None,
    "General Position": lambda x: x.mode().iloc[0] if not x.mode().empty else None,
    "Age": "max",
    "Rating": "mean",
    "Matches" : "count",
    "Minutes": "sum",
    "Nationality": "first"
})

df_agg = df_agg[df_agg["General Position"].isin(selected_positions)]
df_agg["Average Rating"] = df_agg["Rating"].round(2)
df_agg.drop(columns=["Rating"], inplace=True)
df_avg = df_agg[(df_agg["Matches"] >= min_matches) & (df_agg["Age"] <= age_max)]
df_avg["Average Rating"] = df_avg["Average Rating"].round(2)
df_top = df_avg.sort_values(by="Average Rating", ascending=False).head(top_n)
df_top.set_index("Player", inplace=True)

# --------- Display ---------
st.title("Top Player Rankings")
#st.write(
#    "- Rank the top players by average rating with customizable filters. \n"
#    "- Filter by league, position, age, and number of matches played."
#)

if all_leagues or len(selected_leagues) > 1:
    cols_to_display = ["Average Rating", "Position", "Age", "Nationality", "Matches", "Minutes", "Team", "League"]
    rename_cols = {"Team": "Team(s)", "League": "League(s)"}
else:
    cols_to_display = ["Average Rating", "Position", "Age", "Nationality", "Matches", "Minutes", "Team"]
    rename_cols = {"Team": "Team(s)"}

st.dataframe(
    df_top[cols_to_display].rename(columns=rename_cols),
    use_container_width=True
)
