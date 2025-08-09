import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ------------------------- Functions -------------------------
def get_features_for_players(positions):
    features = set()
    for pos in positions:
        if pos == 'Forward':
            features.update([
                'Goals', 'Efficiency', '% Take-Ons', 'Actions created',
                'Expected Assists (xA)', "Actions in the Penalty Area", 'Key Passes',
                '% Aerial Duels', 'Progressive Actions (Total)', 'Successful Take-Ons'
            ])
        elif pos == 'Midfielder':
            features.update([
                'Progressive Actions (Total)', 'Interceptions', 'Tackles Won',
                'Blocks', 'Ball Recoveries', 'Key Passes',
                'Fouls Committed', '% Tackles/Duels', 'Touches Middle Third', '% Aerial Duels'
            ])
        elif pos == 'Defender':
            features.update([
                'Clearances', 'Blocks', 'Interceptions', '% Aerial Duels',
                'Touches', 'Fouls Committed', 'Aerial Duels Won',
                'Progressive Passes', 'Ball Recoveries', '% Tackles/Duels'
            ])
    return list(features)

def get_features_for_goalkeepers():
    return [
        'Clean Sheets', 'Crosses Stopped', 'Sweeper Actions', 'Saves',
        'Goals Against', 'Efficiency', '% Saves', '% Long Passes', 
        '% Crosses Stopped'
    ]

def get_features(positions):
    if 'Goalkeeper' in positions:
        return get_features_for_goalkeepers()
    else:
        return get_features_for_players(positions)

def get_df(path_folder, positions):
    try:
        file_name = "_gk" if 'Goalkeeper' in positions else ""
        df_path = os.path.join(path_folder, f"centiles/Scouting_centiles{file_name}.csv")
        df_radar = pd.read_csv(df_path)
        df_radar.rename(columns={df_radar.columns[0]: "Player"}, inplace=True)
        return df_radar
    except FileNotFoundError:
        st.error(f"Data file not found in folder '{df_path}'. Please check your selections and data.")
        return pd.DataFrame()

def plot_radar(players_data, features, players):
    if len(features) < 3:
        st.warning("Please select at least 3 features for a proper radar chart display.")
        return

    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    for player in players:
        values = players_data.loc[players_data["Player"] == player, features].values.flatten().tolist()
        if len(values) != len(features):
            st.warning(f"Not enough data for player {player} to plot radar.")
            continue
        values += values[:1]
        ax.plot(angles, values, label=player, linewidth=2)
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, fontsize=10)
    ax.set_yticklabels([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)

# ------------------------- Streamlit App -------------------------
st.set_page_config(page_title="Scouting")
st.sidebar.title("Select Parameters")
st.title("Scouting")
st.write(
    "- Access detailed scouting metrics and radar charts for players outside the Big Leagues. \n"
    "- Filter by position, season, and players to compare stats, percentiles, and adjusted metrics."
)

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=1)

season = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

if season_code:
    path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))
    
    positions = st.sidebar.multiselect("Position", ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'])

    if positions:
        df_radar = get_df(path_folder, positions)
        if df_radar.empty:
            st.stop()
        else:
            selected_features = get_features(positions)

            file_name = f"Scouting_aggregated_gk.csv" if 'Goalkeeper' in positions else f"Scouting_aggregated.csv"
            df_global_path = os.path.join(path_folder, f"centiles/{file_name}")
            df_global = pd.read_csv(df_global_path)
            df_global = df_global[df_global['Matches Played'] > 0]
            df_global = df_global[df_global['General Position'].isin(positions)]
                
            filtered_players = df_radar[df_radar['General Position'].isin(positions)]
            df_radar = df_radar[df_radar['General Position'].isin(positions)]
            players_all = filtered_players['Player'].tolist()

            selected_players = st.sidebar.multiselect("Players", players_all)

            if selected_players:
                df_global = df_global[df_global['Player'].isin(selected_players)]
                df_global = df_global[df_global['General Position'].isin(positions)]
                df_global = df_global.drop(columns=[col for col in df_global.columns if col.endswith("_x")])
                df_global.columns = [col[:-2] if col.endswith('_y') else col for col in df_global.columns]

                df_global["Matches Played"] = df_global["Matches Played"].astype("Int64")
                
                if 'Goalkeeper' in positions:
                    columns = ['Player', 'General Position', 'Age', 'Nation', 'Matches Played', 'Minutes Played', 'Goals Against', 'Clean Sheets', 'Team']
                else:
                    columns = ['Player', 'General Position', 'Age', 'Nation', 'Matches Played', 'Minutes Played', 'Goals', 'Assists', 'Yellow Cards', 'Red Cards', 'Team']

                st.subheader("📋 Global Player Statistics")
                df_display = df_global[columns].set_index('Player').round(2)
                df_display = df_display.rename(columns={
                    "Team": "Team(s)"
                })
                st.dataframe(df_display, use_container_width=True)

                st.subheader("📌 Player Radar Statistics")
                if selected_players and selected_features:
                    plot_radar(df_radar, selected_features, selected_players)
                    df_selected = df_radar[df_radar["Player"].isin(selected_players)][["Player"] + selected_features].set_index("Player")
                    st.subheader("📈 Player Percentiles")
                    st.dataframe(df_selected.T)
                    
                st.subheader("📈 Perfomance Metrics")
                if 'Goalkeeper' in positions: 
                    df_metrics = pd.read_csv(os.path.join(path_folder, "metrics", f"Scouting_metrics_gk.csv"))
                else:
                    df_metrics = pd.read_csv(os.path.join(path_folder, "metrics", f"Scouting_metrics.csv"))
                if not df_metrics.empty:
                    df_metrics = df_metrics[df_metrics['General Position'].isin(positions)]
                    df_metrics = df_metrics[df_metrics['Player'].isin(selected_players)]
                    df_metrics = df_metrics.set_index("Player")
                    df_metrics = df_metrics[[col for col in df_metrics.columns if col.endswith("Index")]]
                    st.dataframe(df_metrics.T)
                    
                st.subheader("🧮 Adjusted Stats + Percentiles (All Features)")
                for player in selected_players:
                    file_name = "Scouting_adjusted_gk.csv" if 'Goalkeeper' in positions else "Scouting_adjusted.csv"
                    df_adj_path = os.path.join(path_folder, f"centiles/{file_name}")
                    df_adj = pd.read_csv(df_adj_path)

                    stats_absolute = df_adj[
                        (df_adj["Player"] == player) & 
                        (df_adj['General Position'].isin(positions))
                    ]

                    stats_percentiles = df_radar[
                        (df_radar["Player"] == player)
                    ]

                    df_merged = pd.merge(
                        stats_absolute,
                        stats_percentiles,
                        on=["Player", "Age", "Nation"],
                        suffixes=("_abs", "_pct")
                    )

                    deleted_stats = ['Matches Played', 'Minutes Played', 'Age', 'Nation', 'Born', 'Squad', 'Team', 'Starts', 'Team(s)', 'League(s)', 'League', 'General Position']
                    common_stats = [col.replace("_abs", "") for col in df_merged.columns if col.endswith("_abs") and col.replace("_abs", "") not in deleted_stats]

                    valid_stats = []
                    for stat in common_stats:
                        abs_val = df_merged[f"{stat}_abs"]
                        if not (abs_val.isnull().all() or abs_val.sum() == 0):
                            valid_stats.append(stat)

                    df_combined = pd.DataFrame({
                        "Stat": valid_stats,
                        "Per 90 min or Percentage": [df_merged[f"{stat}_abs"].values[0] for stat in valid_stats],
                        "Percentile": [df_merged[f"{stat}_pct"].values[0] for stat in valid_stats]
                    }).set_index("Stat")

                    st.markdown(f"### 🔎 {player}")
                    st.dataframe(df_combined.sort_index(), use_container_width=True)