# streamlit run "/Users/matteolemesre/Desktop/Data Project/Data LOSC/Github/Introduction.py"
import streamlit as st

st.set_page_config(page_title="Data LOSC")

st.title("Data LOSC")

st.markdown(""" 
I'm passionate about data analysis, data science, and football — especially as a dedicated Lille OSC supporter.
This dashboard is a personal end-to-end project designed to analyze, compare, and visualize football player and team performances, using data scraped from [FBref.com](https://fbref.com).

Pages overview:
- **Player Performance Overview:** Compare individual performances in attack, passing, defense, and possession, with radar charts and average ratings.
- **Matchday Player Report:** Dive into match-specific ratings and stats by league, week, and team.
- **Top Player Rankings:** Rank top players by average rating, filtered by league, position, age, and matches played.
- **Player Performance Indices:** Explore custom indices by role and minutes played, displayed on a percentile scale for advanced comparisons.
- **Top Match Performances:** Highlight the best single-match outputs by stat (e.g., assists, interceptions, saves).
- **Top Season Performances:** Rank seasonal outputs by stat, with totals or per-90 metrics.
- **Team Performances:** Compare team performances across leagues using percentile charts and key performance indicators.

Note: 
- **Big Leagues:** Top 5 European leagues, UCL, UEL and UECL — over 2,100 matches per season
- **Minor Leagues:** Argentine Primera, Brazilian Série A, Dutch Eredivisie, MLS, Portuguese Primeira Liga, Copa Libertadores, English Championship, Italian Serie B, Liga MX, and Belgian Pro League

---

> Use the **sidebar on the left** to start exploring the data!
""")
#- **Scouting:** Access detailed metrics and radar charts for players from outside the Big Leagues.
