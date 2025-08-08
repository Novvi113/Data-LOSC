import streamlit as st
import pandas as pd
import os

# ----------------------- Stats ------------------------
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
# ----------------------- Streamlit UI ------------------------
st.set_page_config(page_title="Top Season Performances")
st.title("Top Season Performances")
st.write("Rank seasonal outputs by stat, with totals or per-90 metrics.")
# ----------------------- Sidebar ------------------------
st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=1)

if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"
else:
    season_code = None
    st.error("Invalid season selected.")
    st.stop()

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))
paths = {
    "adjusted_players": os.path.join(base_path, "centiles", f"data_players_adjusted.csv"),
    "adjusted_gk": os.path.join(base_path, "centiles", f"data_goals_adjusted.csv"),
    "aggregated_players": os.path.join(base_path, "centiles", f"data_players_aggregated.csv"),
    "aggregated_gk": os.path.join(base_path, "centiles", f"data_goals_aggregated.csv"),
    "data_players_average": os.path.join(base_path, "ratings", "data_players_average.csv"),
    "data_goals_average": os.path.join(base_path, "ratings", "data_goals_average.csv")
}

per_90 = st.sidebar.checkbox("Per 90 min?", value=True)

# ----------------------- Load Data ------------------------
try:
    if per_90:
        df_players = pd.read_csv(paths["adjusted_players"])
        df_gk = pd.read_csv(paths["adjusted_gk"])
    else:
        df_players = pd.read_csv(paths["aggregated_players"])
        df_gk = pd.read_csv(paths["aggregated_gk"])
except Exception as e:
    st.error(f"Error loading data files: {e}")
    st.stop()

df_gk["General Position"] = "Goalkeeper"
df_all = pd.concat([df_players, df_gk], ignore_index=True)

df_rating = pd.concat([
        pd.read_csv(paths["data_players_average"]),
        pd.read_csv(paths["data_goals_average"])
    ], ignore_index=True)
    
positions = st.sidebar.multiselect("Position", df_rating['General Position'].unique())
if not positions:
    st.stop()

is_only_gk = set(positions) == {"Goalkeeper"}
stats_list = get_goalkeeper_stats() if is_only_gk else get_player_stats()
stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
n = st.sidebar.slider("Number of top players to display", 5, 100, 30)
min_minutes = st.sidebar.slider("Minimum minutes played", 0, 4000, 2000)
age_max = st.sidebar.slider("Maximum age", 15, 50, 50)

df_filtered = df_all[(df_all["General Position"].isin(positions)) & (df_all[stat].notna())].copy()

df_filtered["Age"] = df_filtered["Age"].astype(str).str.split("-").str[0].astype(int)
df_filtered = df_filtered[df_filtered["Age"] <= age_max]
df_filtered = df_filtered[df_filtered["Minutes"] >= min_minutes]

df_grouped = df_filtered.groupby("Player", as_index=False).agg({
    stat: "sum",
    "Minutes": "sum",
    "Age": "first", 
    "Nationality": "first"
})

df_grouped[stat] = df_grouped[stat].round(2)
df_grouped = df_grouped[df_grouped["Minutes"] >= min_minutes]

# ----------------------- Join Data ------------------------
if not df_rating.empty:
    df_total = df_grouped.merge(df_rating, on=["Player", "Nationality", "Age"], how="left") \
                     .merge(df_all, on=["Player", "Nationality", "Age"], how="left") 
    
    df_total = df_total.rename(columns={
        "Most Common Position": "Position",
        "Team": "Team(s)",
        "Minutes": "Minutes Played",
        "League": "League(s)"
    })

else:
    df_rating = pd.DataFrame(columns=["Player", "Average Rating"])
    try:
        df_aggregated_players = pd.read_csv(paths["aggregated_players"])
        df_aggregated_gk = pd.read_csv(paths["aggregated_gk"])
    except Exception as e:
        st.error(f"Error loading aggregated data: {e}")
        st.stop()

    df_aggregated_gk["General Position"] = "Goalkeeper"
    df_aggregated_all = pd.concat([df_aggregated_players, df_aggregated_gk], ignore_index=True)
    df_club = df_aggregated_all[["Player", "Team"]].drop_duplicates()
    
    df_total = df_grouped.merge(df_rating, on="Player", how="left") \
                        .merge(df_club, on="Player", how="left") \
                        .merge(df_all, on="Player", how="left")

cols_x = [col for col in df_total.columns if col.endswith('_x')]
rename_dict = {col: col.replace('_x', '') for col in cols_x}
df_total = df_total.rename(columns=rename_dict)
df_total = df_total.loc[:, ~df_total.columns.duplicated()]
df_total = df_total.drop(columns=[col for col in df_total.columns if '_y' in col or '_x' in col], errors='ignore')

df_total = df_total.sort_values(by=stat, ascending=False).head(n)

# ----------------------- Display ------------------------
df_total = df_total.rename(columns={
    "Team": "Team(s)",
    "Minutes": "Minutes Played",
    "League": "League(s)"
})

selected_columns = ["Player", stat, "Average Rating", "Position", "Age", "Nationality", "Minutes Played", "Team(s)", "League(s)"]

df_display = df_total[selected_columns].drop_duplicates()

df_display["League(s)"] = df_display["League(s)"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

if "Goalkeeper" in positions:
    df_display["Minutes Played"] = df_display["Minutes Played"].astype(int)
    
df_display = df_display.loc[:, ~df_display.columns.duplicated()]
st.dataframe(df_display.set_index("Player"), use_container_width=True)


