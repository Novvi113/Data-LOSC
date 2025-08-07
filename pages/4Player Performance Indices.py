import streamlit as st
import pandas as pd
import os

# ---------------- Stats ----------------
def get_player_stats():
    return ["Offensive Index", "Passing Index", "Possession Index", "Defensive Index"]

def get_goalkeeper_stats():
    return ["Line Index", "Passes Index"]

st.set_page_config(page_title="Player Performance Indices")
st.title("Player Performance Indices")

st.markdown("""
This page lets you explore and compare players through a set of **custom performance indices**, built for advanced analysis across leagues, positions, and roles.

- Filter by **league category**, **player position**, **age**, and **specific metric** to highlight the player profiles you're interested in.
- Each index is displayed on a **percentile scale**, allowing fair and contextualized comparisons between players.
- The **indices are calculated using a custom algorithm** tailored to player roles and minutes played, and continuously refined based on new data.
- These metrics aim to provide a consistent and objective framework for **ranking** and **profiling** players across competitions.
""")

# ---------------- Sidebar progressive filters ----------------
st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=1)

season = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))
paths = {
    "metrics_players": os.path.join(base_path, "metrics", f"data_players_metrics.csv"),
    "metrics_gk": os.path.join(base_path, "metrics", f"data_goals_metrics.csv"),
    "aggregated_players": os.path.join(base_path, "centiles", f"data_players_aggregated.csv"),
    "aggregated_gk": os.path.join(base_path, "centiles", f"data_goals_aggregated.csv"),
    "ratings_players": os.path.join(base_path, "ratings", "data_players.csv"),
    "ratings_gk": os.path.join(base_path, "ratings", "data_goals.csv")
}

df_players = pd.read_csv(paths["metrics_players"])
df_gk = pd.read_csv(paths["metrics_gk"])

df_notes = pd.concat([
    pd.read_csv(paths["ratings_players"]),
    pd.read_csv(paths["ratings_gk"])
], ignore_index=True)


positions = st.sidebar.multiselect("Position", sorted(set(list(df_gk['General Position'].unique()) + list(df_players['General Position'].unique()))))
if not positions:
    st.stop()

is_only_gk = set(positions) == {"Goalkeeper"}
stats_list = get_goalkeeper_stats() if is_only_gk else get_player_stats()
stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
if not stat:
    st.stop()

n = st.sidebar.slider("Number of top players to display", 5, 100, 30)
min_minutes = st.sidebar.slider("Minimum minutes played", 0, 4000, 2000)
age_max = st.sidebar.slider("Maximum age", 15, 50, 50)

if "Goalkeeper" in positions:
    df_all = df_gk
else: 
    df_all = df_players

df_filtered = df_all[(df_all["General Position"].isin(positions)) & (df_all[stat].notna())].copy()
df_filtered = df_filtered[df_filtered["Minutes"] >= min_minutes]
df_filtered["Age"] = df_filtered["Age"].astype(str).str.split("-").str[0].astype(int)
df_filtered = df_filtered[df_filtered["Age"] <= age_max]

df_grouped = df_filtered[["Player", stat, "Minutes", "Age", "Nationality"]].copy()

if not df_notes.empty:
    df_rating = df_notes.groupby("Player", as_index=False)["Rating"].mean().rename(columns={"Rating": "Average Rating"})
    df_rating["Average Rating"] = df_rating["Average Rating"].round(2)
    most_common_pos = df_notes.groupby('Player')['Position'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
    df_rating = df_rating.merge(most_common_pos, on='Player', how='left')

    df_club = df_notes.groupby("Player")["Team"].agg(lambda x: ", ".join(sorted(set(x)))).reset_index()
    df_league = df_notes.groupby("Player")["League"].agg(lambda x: ", ".join(sorted(set(x)))).reset_index()

    df_final = df_grouped.merge(df_rating, on="Player", how="left") \
                         .merge(df_club, on="Player", how="left") \
                         .merge(df_league, on="Player", how="left")
else:
    df_rating = pd.DataFrame(columns=["Player"])
    df_aggregated_players = pd.read_csv(paths["aggregated_players"])
    df_aggregated_gk = pd.read_csv(paths["aggregated_gk"])
    df_aggregated_gk["General Position"] = "Goalkeeper"
    df_aggregated_all = pd.concat([df_aggregated_players, df_aggregated_gk], ignore_index=True)
    df_club = df_aggregated_all[["Player", "Team"]].drop_duplicates()

    df_final = df_grouped.merge(df_rating, on="Player", how="left") \
                         .merge(df_club, on="Player", how="left")

df_final = df_final.sort_values(by=stat, ascending=False).head(n)

columns_to_display = ["Player", stat, "Age", "Nationality", "Minutes"]
if "Average Rating" in df_final.columns:
    columns_to_display = ["Player", stat, "Average Rating", "Age", "Nationality", "Minutes"]
if "Position" in df_final.columns:
    columns_to_display = ["Player", stat, "Average Rating", "Position", "Age", "Nationality", "Minutes"]
if "Team" in df_final.columns:
    df_final.rename(columns={"Team": "Team(s)"}, inplace=True)
    columns_to_display.append("Team(s)")
if "League" in df_final.columns:
    df_final.rename(columns={"League": "League(s)"}, inplace=True)
    columns_to_display.append("League(s)")

df_display = df_final[columns_to_display]
st.dataframe(df_display.set_index("Player"), use_container_width=True)