import streamlit as st
import pandas as pd
import numpy as np
import random as rd
from collections import defaultdict
import os
import matplotlib.pyplot as plt

# ------------------------- Functions -------------------------
def load_matches_data(path_folder, selected_league):
    path = os.path.join(path_folder, f"leagues_games/{selected_league}_games.csv")
    return pd.read_csv(path)

def load_ranking_uefa_data(path_folder, selected_league):
    path = os.path.join(path_folder, f"UEFA Leagues/Ranking {selected_league}.csv")
    return pd.read_csv(path)

def compute_points(Matches, matches_played):
    df = Matches[:matches_played * 18].dropna(subset=["Score"])
    teams = sorted(set(Matches["Home Team"]).union(set(Matches["Away Team"])))
    points = {team: 0 for team in teams}
    
    if not df.empty:
        for _, row in df.iterrows():
            home = row["Home Team"]
            away = row["Away Team"]
            score = row["Score"]
            try:
                home_goals, away_goals = [int(x.strip()) for x in score.replace('–', '-').split('-')]
            except:
                continue
            if home_goals > away_goals:
                points[home] += 3
            elif home_goals < away_goals:
                points[away] += 3
            else:
                points[home] += 1
                points[away] += 1
                
    df_points = pd.DataFrame(list(points.items()), columns=["Team", "Pts"])
    return df_points

def simulate_match(team1, team2, points_teams, UEFAcoeff, proba_draw):
    coeff_team1 = UEFAcoeff[team1]
    coeff_team2 = UEFAcoeff[team2]
    proba_team1 = coeff_team1*(1 - proba_draw) / (coeff_team1 + coeff_team2)
    proba_team2 = coeff_team2*(1 - proba_draw) / (coeff_team1 + coeff_team2)
    proba = [proba_team1, proba_draw, proba_team2]
    
    resultat = rd.choices(['team1', 'draw', 'team2'], proba)[0]
    
    if resultat == 'team1':
        points_teams[team1] += 3
    elif resultat == 'team2':
        points_teams[team2] += 3
    else:
        points_teams[team1] += 1
        points_teams[team2] += 1

def qualification(points_attempted, qualification_points, playoff_points, elimination_points):
    for i in range(len(points_attempted)):
        if i <= 8:
            qualification_points[points_attempted[i]] += 1
        elif i <= 24:  
            playoff_points[points_attempted[i]] += 1
        else:  
            elimination_points[points_attempted[i]] += 1
    return qualification_points, playoff_points, elimination_points

def frequency(points):
    min_point = min(points)
    max_point = max(points)
    counts = [0] * (max_point - min_point + 1)
    values = list(range(min_point, max_point + 1))
    for p in points:
        counts[p - min_point] += 1
    return counts, values

def qualification_percentage(team_rankings, total_qualifications):
    for team in team_rankings.keys():
        if isinstance(team_rankings[team], list):
            for i in range(len(team_rankings[team])):
                if team_rankings[team][i] <= 8:
                    total_qualifications[team]['Qualifications'] += 1
                elif team_rankings[team][i] <= 24:
                    total_qualifications[team]['Playoffs'] += 1
                else:
                    total_qualifications[team]['Eliminations'] += 1  
    return total_qualifications

# ------------------------- Streamlit Layout -------------------------
st.set_page_config(page_title="UEFA Leagues Simulation", layout="wide")
st.title("UEFA Leagues Simulation")

st.sidebar.title("Parameters")
selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=0)
selected_league = st.sidebar.selectbox("League", ["UEFA Champions League", "UEFA Europa League", "UEFA Europa Conference League"], index=None)

season_code = {"2023-2024":"23_24","2024-2025":"24_25","2025-2026":"25_26"}[selected_season]
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))

if not selected_league:
    st.stop()
    
Matches = load_matches_data(path_folder, selected_league)
Ranking = load_ranking_uefa_data(path_folder, selected_league)

league_matches_dict = {
    "UEFA Champions League": 8,
    "UEFA Europa League": 8,
    "UEFA Europa Conference League": 6
}
no_matches = league_matches_dict[selected_league]
Matches = Matches[:no_matches * 18]
selected_matches_played = st.sidebar.selectbox("Matches Played", range(no_matches + 1), index=None)
if selected_matches_played is None:
    st.stop()
    
#proba_draw = st.sidebar.slider("Probability of draw", 0.0, 1.0, 0.2, 0.01)
proba_draw = 0.2
Standing = compute_points(Matches, selected_matches_played)

Confrontations = {}
for index, row in Matches.iterrows():
    home = row['Home Team']
    away = row['Away Team']
    Confrontations.setdefault(home, []).append(away)
    Confrontations.setdefault(away, []).append(home)

Real_points = {team: points for team, points in zip(Standing['Team'], Standing['Pts'])}
UEFAcoeff = {team: coeff for team, coeff in zip(Ranking['Team'], Ranking['Pts'])}

# ------------------------- Simulation -------------------------
N = 10**5
total_team_points = defaultdict(list)
total_qualifications = {team: {'Qualifications': 0, 'Playoffs': 0, 'Eliminations': 0} for team in Ranking['Team']}

qualification_points = {i: 0 for i in range(0, 3*no_matches + 1)}
playoff_points = {i: 0 for i in range(0, 3*no_matches + 1)}
elimination_points = {i: 0 for i in range(0, 3*no_matches + 1)}

with st.spinner("Simulating matches... This may take a few minutes."):
    for i in range(N):
        team_rankings = defaultdict(list)
        confrontations_copy = {team: opponents[:] for team, opponents in Confrontations.items()}
        team_points = {team: points for team, points in Real_points.items()}
        
        for team in Ranking['Team']:
            opponents = confrontations_copy[team][selected_matches_played:]
            for opponent in opponents:
                simulate_match(team, opponent, team_points, UEFAcoeff, proba_draw)
                confrontations_copy[team].remove(opponent)
                confrontations_copy[opponent].remove(team)
        
        ranking = sorted(team_points.items(), key=lambda x: x[1], reverse=True)
        for position, (team, points) in enumerate(ranking):
            team_rankings[team].append(position + 1)
            total_team_points[team].append(points)
        
        points_list = [points for _, points in ranking]
        qualification_points, playoff_points, elimination_points = qualification(points_list, qualification_points, playoff_points, elimination_points)
        total_qualifications = qualification_percentage(team_rankings, total_qualifications)

# ------------------------- Visualization -------------------------
st.subheader("Standing")
df_standing = Standing.copy()
df_standing = df_standing.sort_values(by="Pts", ascending=False).reset_index(drop=True)
df_standing["Pts"] = df_standing["Pts"].astype(int)
df_standing.index = df_standing.index + 1
df_standing.index.name = "Rank"
st.table(df_standing)

st.subheader("Probability by Points")
points  = []
qualif  = []
playoff = []
elim    = []

for point in sorted(qualification_points.keys()):
    total_cases = qualification_points[point] + playoff_points[point] + elimination_points[point]
    if total_cases == 0:
        continue
    points.append(point)
    qualif.append(100 * qualification_points[point] / total_cases)
    playoff.append(100 * playoff_points[point] / total_cases)
    elim.append(100 * elimination_points[point] / total_cases)

fig, ax = plt.subplots(figsize=(12,6))
ax.plot(points, qualif, label="Qualification %", marker='o')
ax.plot(points, playoff, label="Play-off %", marker='o')
ax.plot(points, elim, label="Elimination %", marker='o')
ax.set_xlabel("Points")
ax.set_ylabel("Percentage (%)")
ax.set_title("Qualification / Play-off / Elimination Probability by Points")
ax.set_xticks(points)
ax.set_ylim(0, 105)
ax.grid(True, linestyle="--", alpha=0.5)
ax.legend()
st.pyplot(fig)

st.subheader("Average Points Ranking")
expected_points = {team: sum(points) / len(points) for team, points in total_team_points.items()}
df_expected = pd.DataFrame(sorted(expected_points.items(), key=lambda x: x[1], reverse=True), columns=["Team", "Expected Points"])
df_expected["Expected Points"] = df_expected["Expected Points"].map("{:.2f}".format)
st.table(df_expected)

st.subheader("Qualification Probabilities per Team")
results = []
for team in Ranking['Team']:
    pct_qual    = 100 * total_qualifications[team]['Qualifications'] / N
    pct_playoff = 100 * total_qualifications[team]['Playoffs'] / N
    pct_elim    = 100 * total_qualifications[team]['Eliminations'] / N
    results.append((team, pct_qual, pct_playoff, pct_elim))

results.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
df_results = pd.DataFrame(results, columns=["Team","Qualification %","Play-off %","Elimination %"])
df_results["Qualification %"] = df_results["Qualification %"].map("{:.2f}".format)
df_results["Play-off %"] = df_results["Play-off %"].map("{:.2f}".format)
df_results["Elimination %"] = df_results["Elimination %"].map("{:.2f}".format)
st.table(df_results)