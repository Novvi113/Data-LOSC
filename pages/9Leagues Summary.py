import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict
import os

# ------------------------- Functions -------------------------
def load_matches_data(path_folder, selected_league):
    path = os.path.join(path_folder, f"leagues_games/{selected_league}_games.csv")
    return pd.read_csv(path)

def compute_points(Matches, matches_played, no_others_matchs):
    df = Matches[:matches_played * no_others_matchs].dropna(subset=["Score"])
    teams = sorted(set(Matches["Home Team"]).union(set(Matches["Away Team"])))
    points = {team: 0 for team in teams}
    goals_for = {team: 0 for team in teams}
    goals_against = {team: 0 for team in teams}
    
    if not df.empty:
        for _, row in df.iterrows():
            home = row["Home Team"]
            away = row["Away Team"]
            score = row["Score"]
            try:
                home_goals, away_goals = [int(x.strip()) for x in score.replace('–', '-').split('-')]
            except:
                continue

            goals_for[home] += home_goals
            goals_against[home] += away_goals
            goals_for[away] += away_goals
            goals_against[away] += home_goals

            if home_goals > away_goals:
                points[home] += 3
            elif home_goals < away_goals:
                points[away] += 3
            else:
                points[home] += 1
                points[away] += 1

    df_points = pd.DataFrame({
        "Team": list(points.keys()),
        "Pts": list(points.values()),
        "Goals": [goals_for[t] for t in points.keys()],
        "Goals Against": [goals_against[t] for t in points.keys()],
    })
    
    df_points["Goal Diff"] = df_points["Goals"] - df_points["Goals Against"]
    return df_points

def compute_average_opponent_rank(Matches, Standing, matches_played, no_others_matchs):
    df_matches_played = Matches[:matches_played * no_others_matchs].dropna(subset=["Score"])
    if df_matches_played.empty or Standing.empty:
        return pd.DataFrame()

    opponents = defaultdict(list)
    for _, row in df_matches_played.iterrows():
        home, away = row["Home Team"], row["Away Team"]
        opponents[home].append(away)
        opponents[away].append(home)

    current_ranks = {
        team: rank for rank, team in enumerate(
            Standing.sort_values(
                by=["Pts", "Goal Diff", "Goals"],
                ascending=[False, False, False]
            )["Team"],
            start=1
        )
    }

    avg_opponents = {}
    median_opponents = {}
    for team, opp_list in opponents.items():
        ranks = [current_ranks[opp] for opp in opp_list if opp in current_ranks]
        avg_opponents[team] = round(np.mean(ranks), 2) if ranks else np.nan
        median_opponents[team] = int(round(np.median(ranks))) if ranks else np.nan

    df_opp = pd.DataFrame({
        "Team": list(avg_opponents.keys()),
        "Average Opponent Rank": [v for v in avg_opponents.values()], 
        "Median Opponent Rank":[v for v in median_opponents.values()]
    })

    df_opp = df_opp.sort_values(by="Average Opponent Rank", ascending=True).reset_index(drop=True)
    df_opp.index = df_opp.index + 1
    df_opp.index.name = "Rank"
    df_opp["Average Opponent Rank"] = df_opp["Average Opponent Rank"].map(lambda x: f"{x:.2f}")

    return df_opp

# ------------------------- Streamlit Layout -------------------------
st.set_page_config(page_title="Leagues Summary", layout="wide")
st.title("Leagues Summary")

st.sidebar.title("Parameters")
selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=0)
selected_league = st.sidebar.selectbox("League", ["UEFA Champions League", "UEFA Europa League", "UEFA Europa Conference League", "Italian Serie A", "French Ligue 1", "German Bundesliga", "English Premier League", "Spanish La Liga"], index=None)

season_code = {"2023-2024":"23_24","2024-2025":"24_25","2025-2026":"25_26"}[selected_season]
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))

if not selected_league:
    st.stop()
    
Matches = load_matches_data(path_folder, selected_league)

league_info = {
    "UEFA Champions League": {"matches": 8, "opponents": 36},
    "UEFA Europa League": {"matches": 8, "opponents": 36},
    "UEFA Europa Conference League": {"matches": 6, "opponents": 36},
    "Italian Serie A": {"matches": 38, "opponents": 20},
    "French Ligue 1": {"matches": 34, "opponents": 18},
    "German Bundesliga": {"matches": 34, "opponents": 18},
    "English Premier League": {"matches": 38, "opponents": 20},
    "Spanish La Liga": {"matches": 38, "opponents": 20}
}

no_matches = league_info[selected_league]["matches"]
no_opponents = league_info[selected_league]["opponents"]
no_others_matchs = no_opponents // 2
Matches = Matches[:no_matches * no_others_matchs]
selected_matches_played = st.sidebar.selectbox("Matches Played", range(no_matches + 1), index=None)
if selected_matches_played is None:
    st.stop()
    
Standing = compute_points(Matches, selected_matches_played, no_others_matchs)

# ------------------------- Visualization -------------------------
st.subheader("Standing")
Standing = Standing.sort_values(
        by=["Pts", "Goal Diff", "Goals"],
        ascending=[False, False, False]
    ).reset_index(drop=True)
Standing["Pts"] = Standing["Pts"].astype(int)
Standing.index = Standing.index + 1
Standing.index.name = "Rank"
st.table(Standing)

# ------------------------- Average Opponent Rank -------------------------
st.subheader("Average Opponent Rank")

df_opp = compute_average_opponent_rank(Matches, Standing, selected_matches_played, no_others_matchs)

if not df_opp.empty:
    st.table(df_opp)
else:
    st.stop()