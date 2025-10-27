import streamlit as st
import pandas as pd
import os

# ------------------------- Functions -------------------------
def get_player_stats():
    return [
        "Goals", "Shots on Target", 
        "Key Passes", 
        "Expected Assists (xA)", 
        "Passes Completed (Total)", 
        "Passes Completed (Short)",  
        "Passes Completed (Medium)", 
        "Passes Completed (Long)",
        "Passes into Final Third", "Passes into Penalty Area", 
        "Crosses into Penalty Area", "Progressive Passes", 
        "Progressive Passes Received",
        "Progressive Carries", "Progressive Runs",
        "Carries into Final Third", "Carries into Penalty Area",
        "Successful Take-Ons", "Tackles Won", "Tackles Defensive Third", 
        "Challenges Tackled", 
        "Interceptions", "Clearances", "Blocks", 
        "Errors", "Touches", "Touches Attacking Third", 
        "Touches Attacking Penalty Area",
        "Fouls Committed", "Fouls Drawn", "Penalties Won", 
        "Penalties Conceded", "Own Goals", 
        "Aerials Won"
    ]

def get_goalkeeper_stats():
    return [
        "Goals Against", "Saves", 
        "Launched Passes Completed", "Completed Long Passes", 
        "Through Balls", "Crosses Stopped", 
        "Sweeper Actions", "Defensive Actions Outside Penalty Area",
    ]

def get_opponent_score(row):
    league = row["League"]
    gameweek = row["Game Week"]
    team = row["Team"]
    match_df = games.get(league)
    
    if match_df is None:
        return pd.Series(["Unknown", "N/A"])

    match = match_df[match_df["Game Week"] == gameweek]
    for _, m in match.iterrows():
        if m["Home Team"] == team:
            return pd.Series([m["Away Team"], m["Score"]])
        elif m["Away Team"] == team:
            return pd.Series([m["Home Team"], m["Score"]])
    
    return pd.Series(["Unknown", "N/A"])

# ------------------------- Streamlit App -------------------------
st.set_page_config(page_title="Top Match Performances")
st.title("Top Match Performances")
#st.write(
#    "- Highlight the best single-match performances for any stat by players or goalkeepers. \n"
#    "- Filter by season, league, position, and age to showcase standout games."
#)

st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=0)

season = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))

paths = {
    "games": os.path.join(path_folder, "leagues_games", "{}_games.csv"),
    "clean_players": os.path.join(path_folder, "players", "clean", "data_players.csv"),
    "clean_goals": os.path.join(path_folder, "players", "clean", "data_goals.csv"),
    "ratings_players": os.path.join(path_folder, "players", "ratings", "data_players.csv"),
    "ratings_goals": os.path.join(path_folder, "players", "ratings", "data_goals.csv"),
}

df_players = pd.read_csv(paths["clean_players"])
df_goalkeepers = pd.read_csv(paths["clean_goals"])
df_ratings_players = pd.read_csv(paths["ratings_players"])
df_ratings_goalkeepers = pd.read_csv(paths["ratings_goals"])
df_all = pd.concat([df_players, df_goalkeepers], ignore_index=True)
df_ratings = pd.concat([df_ratings_players, df_ratings_goalkeepers], ignore_index=True)

for col in ["Player", "Game Week", "Team", "League"]:
    df_all[col] = df_all[col].astype(str)
    df_ratings[col] = df_ratings[col].astype(str)

df_ratings = df_ratings.drop_duplicates(subset=["Player", "Game Week", "Team", "League"])
df_ratings_filtered = df_ratings[["Player", "Game Week", "Team", "League", "Rating"]]

df = pd.merge(
    df_all,                      
    df_ratings_filtered,        
    on=["Player", "Game Week", "Team", "League"],
    how="left"
)

positions = st.sidebar.multiselect("Position", df["General Position"].unique())
if not positions:
    st.stop()

if set(positions) == {"Goalkeeper"}:
    stats_list = get_goalkeeper_stats()
    df = df[df["General Position"] == "Goalkeeper"]
else:
    stats_list = get_player_stats()
    df = df[df["General Position"].isin(positions)]
    
leagues = sorted(df["League"].dropna().unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
top_n = st.sidebar.slider("Number of top performances to display", 5, 100, 30)
age_max = st.sidebar.slider("Maximum age", 15, 50, 50)

df = df[df["League"].isin(selected_leagues)]
if stat and stat in df.columns:
    df = df[df[stat].notna()]

games = {}
for lg in df["League"].unique():
    try:
        games[lg] = pd.read_csv(paths["games"].format(lg))
    except FileNotFoundError:
        continue

if positions and stat and selected_leagues:
    df[["Opponent", "Score"]] = df.apply(get_opponent_score, axis=1)

    df = df[df[stat].notna() & df["Score"].notna()]
    
    df_top = df.copy()
    
    df_top["Age"] = df_top["Age"].astype(str).str.split("-").str[0].astype(int)
    df_top = df_top[df_top["Age"] <= age_max]
    
    df_top = df_top.sort_values(by=stat, ascending=False).head(top_n)
    
    df_display = df_top[[
        "Player", stat, "Rating", "Position", "Age", "Nationality", "Minutes", "Score", "Team", "Opponent",
        "League", "Game Week"
    ]].rename(columns={
        stat: stat,
        "Team": "Team",
        "Game Week": "Game Week",
        "Minutes": "Minutes Played"
    })
    
    st.dataframe(df_display.set_index("Player"), use_container_width=True)