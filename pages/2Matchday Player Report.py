import streamlit as st
import pandas as pd
import os

# ------------------------- Functions -------------------------
def add_average(df):
    avg = round(df["Rating"].mean(), 2)
    df_result = df[["Player", "Rating"]].copy()
    df_result = df_result.set_index("Player")
    df_result.loc["Average"] = avg
    return df_result

def get_match_info(df, home, away):
    match = df[(df["Home Team"] == home) & (df["Away Team"] == away)]
    return match.iloc[0] if not match.empty else {}

def get_stats_infos(position):
    if "GK" in position:
        list = ['Player', 'Game Week', 'Team', 'League', 'Position', 'Age', 'Minutes', 'Shots on Target Against', 'Goals Against', 'Saves', 'Post-Shot Expected Goals (PSxG)', 'Save Efficiency', 
                'Completed Long Passes', 'Attempted Long Passes', 'Crosses Faced',	'Crosses Stopped', 'Defensive Actions Outside Penalty Area']
    else:
        list =['Player', 'Game Week', 'Team', 'League', 'Position', 'Age', 'Minutes', 'Goals', 'Assists', 'Shots Total', 'Shots on Target', 'Expected Goals (xG)', 'Shot-Creating Actions (SCA)', 
               'Goal-Creating Actions (GCA)', 'Key Passes', 'Passes into Final Third', 'Passes into Penalty Area', 'Crosses into Penalty Area', 'Crosses', 
                'Expected Assists (xA)', 'Passes Completed', 'Passes Attempted', 'Progressive Passes', 'Progressive Carries', 'Take-Ons Attempted', 
                'Successful Take-Ons', 'Tackles Won', 'Dribblers Tackled', 'Interceptions', 'Errors Leading to Shot', 'Ball Recoveries', 'Ball Losses', 'Touches', 
                'Yellow Cards', 'Red Cards', 'Second Yellow Card',	'Offsides', 'Aerials Won', 'Total Aerials']
    return list

def prepare_player_stats(stats_df, ratings_df, exclude_cols=None):
    if exclude_cols is None:
        exclude_cols = []
    df = stats_df.merge(
        ratings_df[["Player", "Rating"]],
        on="Player",
        how="left"
    )
    df = df.drop(columns=[col for col in exclude_cols if col in df.columns], errors='ignore')
    if "Player" in df.columns and "Rating" in df.columns:
        cols = df.columns.tolist()
        cols.remove("Player")
        cols.remove("Rating")
        df = df[["Player", "Rating"] + cols]
    df = df.set_index("Player")
    return df

def team_stats(df_stats, team_name):
    important_stats = [
        'Expected Goals (xG)', 'Progressive Passes', 'Progressive Carries', 
        'Key Passes', 'Passes into Final Third', 'Tackles Won', 'Interceptions', 'Aerials Won', 'Offsides',
    ]
    cols = [col for col in important_stats if col in df_stats.columns]
    if not cols:
        return pd.DataFrame()
    df_team = df_stats[cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    df_summary = df_team.sum().to_frame(name=team_name).round(2)
    return df_summary


# ------------------------- Streamlit App -------------------------
st.set_page_config(page_title="Matchday Player Report")
st.title("Matchday Player Report")
#st.write(
#    "- View detailed matchday reports by league, week, and match. \n"
#    "- See player ratings, in-depth stats, and compare performances for both teams."
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
    
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))
path_players = os.path.join(base_path, "ratings", "data_players.csv")
path_goalkeepers = os.path.join(base_path, "ratings", "data_goals.csv")
path_players_stats = os.path.join(base_path, "clean", "data_players.csv")
path_goalkeepers_stats = os.path.join(base_path, "clean", "data_goals.csv")
path_teams_stats = os.path.join(base_path, "clean", "data_teams.csv")
path_leagues = os.path.join(base_path, "leagues_games")

df_players = pd.read_csv(path_players)
df_gk = pd.read_csv(path_goalkeepers)
df_all = pd.concat([df_players, df_gk], ignore_index=True)

df_players_stats = pd.read_csv(path_players_stats)
df_gk_stats = pd.read_csv(path_goalkeepers_stats)
df_players_stats = df_players_stats[get_stats_infos("")]
df_gk_stats = df_gk_stats[get_stats_infos("GK")]

available_leagues = df_players["League"].dropna().unique().tolist()
selected_leagues = st.sidebar.multiselect("League", available_leagues)

if os.path.exists(path_teams_stats):
    df_teams_stat = pd.read_csv(path_teams_stats)
else:
    df_teams_stat = pd.DataFrame()

if selected_leagues:
    df_games = pd.read_csv(f"{path_leagues}/{selected_leagues[0]}_games.csv")

    available_weeks = sorted(df_games["Game Week"].dropna().unique(), key=lambda x: int(str(x).strip("J").strip()))
    selected_weeks = st.sidebar.multiselect("Game Week", available_weeks)

    if selected_weeks:
        df_week = df_games[df_games["Game Week"].isin(selected_weeks)]

        df_week["Match Label"] = df_week["Home Team"] + " vs " + df_week["Away Team"]
        match_labels = df_week["Match Label"].tolist()
        selected_matches = st.sidebar.multiselect("Match", match_labels)

        for match_label in selected_matches:
            try:
                home_team, away_team = match_label.split(" vs ")
            except ValueError:
                st.warning(f"Invalid match format: {match_label}")
                continue

            match_info = get_match_info(df_week, home_team, away_team)
            game_week = match_info.get("Game Week", "N/A")

            st.write(f"## {home_team} vs {away_team}")
            st.write(f"**Score:** {match_info.get('Score', 'N/A')} | "
                     f"**Referee:** {match_info.get('Referee', 'N/A')} | **Attendance:** {match_info.get('Attendance', 'N/A')} | "
                     f"**Venue:** {match_info.get('Venue', 'N/A')}")
            
            df_home_ratings = df_all[
                (df_all["Team"] == home_team) &
                (df_all["Game Week"] == game_week) &
                (df_all["League"] == selected_leagues[0])
            ].drop(columns=["ID"], errors="ignore")

            df_away_ratings = df_all[
                (df_all["Team"] == away_team) &
                (df_all["Game Week"] == game_week) &
                (df_all["League"] == selected_leagues[0])
            ].drop(columns=["ID"], errors="ignore")

            df_home_stats = df_players_stats[
                (df_players_stats["Team"] == home_team) &
                (df_players_stats["Game Week"] == game_week) &
                (df_players_stats["League"] == selected_leagues[0])
            ].drop(columns=["ID"], errors="ignore")

            df_away_stats = df_players_stats[
                (df_players_stats["Team"] == away_team) &
                (df_players_stats["Game Week"] == game_week) &
                (df_players_stats["League"] == selected_leagues[0])
            ].drop(columns=["ID"], errors="ignore")
            
            df_home_stats_gk = df_gk_stats[
                (df_gk_stats["Team"] == home_team) &
                (df_gk_stats["Game Week"] == game_week) &
                (df_gk_stats["League"] == selected_leagues[0])
            ].drop(columns=["ID"], errors="ignore")

            df_away_stats_gk = df_gk_stats[
                (df_gk_stats["Team"] == away_team) &
                (df_gk_stats["Game Week"] == game_week) &
                (df_gk_stats["League"] == selected_leagues[0])
            ].drop(columns=["ID"], errors="ignore")
            
            if not df_teams_stat.empty:
                df_teams_stat = df_teams_stat[
                    ((df_teams_stat["Team"] == home_team) | (df_teams_stat["Team"] == away_team)) &
                    (df_teams_stat["Game Week"] == game_week) &
                    (df_teams_stat["League"] == selected_leagues[0])
                ].drop(columns=["ID"], errors="ignore")
            
            columns_excl = ['Game Week', 'Team', 'League']

            df_home_players = prepare_player_stats(df_home_stats, df_home_ratings, exclude_cols=columns_excl)
            df_away_players = prepare_player_stats(df_away_stats, df_away_ratings, exclude_cols=columns_excl)
            df_home_gk = prepare_player_stats(df_home_stats_gk, df_home_ratings, exclude_cols=columns_excl)
            df_away_gk = prepare_player_stats(df_away_stats_gk, df_away_ratings, exclude_cols=columns_excl)

            df_home_summary = team_stats(df_home_stats, home_team)
            df_away_summary = team_stats(df_away_stats, away_team)
            df_team_stats_bis = pd.concat([df_home_summary, df_away_summary], axis=1)
            if not df_teams_stat.empty:
                columns_excl = ['Game Week', 'League']
                df_teams_stat = df_teams_stat.drop(columns=[col for col in columns_excl if col in df_teams_stat.columns], errors='ignore')

                st.markdown("## Team Stats Overview")
                df_team_stats = pd.concat([df_teams_stat.set_index("Team").T, df_team_stats_bis], axis=0)
                st.dataframe(df_team_stats)
            
            else:
                st.markdown("## Team Stats Overview")
                st.dataframe(df_team_stats_bis)
            
            st.markdown(f"### {home_team}")
            st.dataframe(df_home_players.sort_values(by="Rating", ascending=False), use_container_width=True)
            st.dataframe(df_home_gk.sort_values(by="Rating", ascending=False), use_container_width=True)

            st.markdown(f"### {away_team}")
            st.dataframe(df_away_players.sort_values(by="Rating", ascending=False), use_container_width=True)
            st.dataframe(df_away_gk.sort_values(by="Rating", ascending=False), use_container_width=True)