import io
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

#Functions

def calc_points (df_input):
    result = [df_input['Result'] == "W", df_input['Result'] == "D", df_input['Result'] == "L",]
    points = [3,1,0]
    df_input['Points'] = np.select(result, points, default=0)
    return df_input

@st.cache_data(ttl=600)
def load_private_csv(file):
    # Construct the GitHub API URL for raw content
    # (Using the Accept header below allows fetching the actual file content)
    FILE_PATH = file
    BRANCH = "main"
    url = f"https://api.github.com/somewun/Data/contents/{FILE_PATH}?ref={BRANCH}"
    
    # Retrieve the token securely from Streamlit Secrets
    headers = {
        "Authorization": f"token {st.secrets['GITHUB_PAT']}",
        "Accept": "application/vnd.github.v3.raw"  # Crucial to get raw text instead of JSON metadata
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Convert the raw text stream into a Pandas DataFrame
        df = pd.read_csv(io.StringIO(response.text))
        return df
    else:
        st.error(f"Failed to fetch data from GitHub. Status Code: {response.status_code}")
        return None

RED = (255,0,0)
BLUE = (0, 108, 149)
GREEN = (51, 180, 29)

st.set_page_config(page_title = 'Marple Athletic Girls Stats (2026/27)', page_icon = ':soccer:', layout = 'wide')

# 1. Initialize the access state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 2. Define the modal dialog
@st.dialog("🔒 Enter Access Code")
def login_dialog():
    st.write("This dashboard is locked. Please enter your authorization code to proceed.")
    
    # Text input for the secret code
    user_code = st.text_input("Access Code", type="password")
    
    if st.button("Unlock Dashboard"):
        # Replace 'secret123' with your actual required code
        if user_code == st.secrets["pwd"]:
            st.session_state.authenticated = True
            st.success("Access granted!")
            st.rerun()  # Instantly refreshes the app to show the dashboard
        else:
            st.error("Incorrect code. Please try again.")

# 3. Control app layout based on authentication status
if not st.session_state.authenticated:
    # Trigger the dialog modal to pop up automatically
    login_dialog()
    st.warning("Please enter the correct code in the popup window to view the dashboard data.")
    
else:
    # 4. Your actual dashboard content goes here
    #with open("stats_dashboard_2627.py") as file:
        #exec(file.read())

    #Load data sets
    df_fixtures_table = load_private_csv("fixtures_table_2627.csv")
    df_opposition_table = load_private_csv("opposition_table.csv")
    df_player_table = load_private_csv("player_table_2627.csv")
    df_season_table = load_private_csv("season_table.csv")
    df_match_data = load_private_csv("match_data_2627.csv")
    df_training_data = load_private_csv("training_data_2627.csv")

    # Convert Date column to datetime data type
    #df_fixtures_table['Date'] = pd.to_datetime(df_fixtures_table['Date'], dayfirst=True)

    #Add points to the fixtures table
    df_fixtures_table["Wins"] = np.where(df_fixtures_table["Result"] == "W", 1, 0)
    df_fixtures_table["Draws"] = np.where(df_fixtures_table["Result"] == "D", 1, 0)
    df_fixtures_table["Losses"] = np.where(df_fixtures_table["Result"] == "L", 1, 0)

    #Titles and other
    st.header("Marple Athletic U13 Girls Stats 2026/27")
    st.logo(image = "logo_cropped.png", size = "Large")

    #Tabs
    tab1, tab2, tab3 = st.tabs(["Team Stats", "Player Stats", "Season Summary"])

    #Tab for the Team Stats
    with tab1:
        # Upper Section: Main Container holding Columns
        with st.container(border=True):
    
            # Create columns inside the container
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
            #create metrics within the columns
            with col1:
                st.metric("Matches", value = int(df_match_data["Match ID"].nunique()))
            with col2:
                st.metric("Goals", value = int(df_match_data["Goals"].sum()))
            with col3:
                st.metric("Shots", value = int(df_match_data["Shots"].sum()))
            with col4:
                st.metric("Assists", value = int(df_match_data["Assist"].sum()))
            with col5:
                st.metric("Pass", value = int(df_match_data["Key Pass"].sum()))
            with col6:
                st.metric("Saves", value = int(df_match_data["Saves"].sum()))
            with col7:
                st.metric("Tackles", value = int(df_match_data["Tcks made"].sum()))
            with col8:
                st.metric("Missed Tackles", value = int(df_match_data["Tcks miss"].sum()))

        #secondary container below
        with st.container(border=True):

            # Create columns inside the lower container
            cola, colb = st.columns([2,3])
    
            #column for goals for and against and fixtures dataframe
            with cola:
                # Create columns inside the container
                col1, col2, col3 = st.columns(3)
    
                #create metrics within the columns
                with col1:
                    st.metric("Goals per game", value = df_fixtures_table["Goals For"].mean(), format="%.2f")
                with col2:
                    st.metric("Opp Goals per game", value = df_fixtures_table["Goals Against"].mean(), format="%.2f")
                with col3:
                    st.metric("Win %", value = int((df_fixtures_table["Result"] == "W").sum() / df_fixtures_table["Result"].count() * 100))
            
                #Creating the fixtures dataframe
                df_results = pd.merge(df_fixtures_table, df_opposition_table, on='Opposition ID', how='left')
                df_results_table = df_results[['Date', 'Name', 'Result', 'Goals For', 'Goals Against', 'League/Cup']].rename(columns={'Name': 'Opposition Name'})
                st.dataframe(df_results_table, column_config={"Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY")},hide_index=True,height=1000)
        
            #column for line graph of match stats
            with colb:
                #Linegraaph of match stats
                df_matches = pd.merge(df_match_data, df_fixtures_table, on='Match ID', how='left')
                df_match_stats = df_matches.groupby('Date')["Date","Goals", "Shots", "Assist", "Key Pass", "Saves", "Tcks made", "Tcks miss"].sum().reset_index()
                fig_stats = px.line(df_match_stats, x="Date", y=df_match_stats.columns, hover_data={"Date": "|%B %d, %Y"})
                fig_stats.update_xaxes(dtick="M1",tickformat="%b\n%Y")
                st.plotly_chart(fig_stats)

                #Bar charts showing goals for and conceeded vs teams
                df_goals = df_results_table.groupby('Opposition Name')['Opposition Name', 'Goals For', 'Goals Against'].sum().reset_index()
                fig_goals = go.Figure(data=[go.Bar(name='Goals Scored', x=df_goals['Opposition Name'], y=df_goals['Goals For']),go.Bar(name='Goals Conceeded', x=df_goals['Opposition Name'], y=df_goals['Goals Against'])])
                # Change the bar mode
                fig_goals.update_layout(barmode='group')
                st.plotly_chart(fig_goals)

    #Tab for the individual player stats
    with tab2:

        df_player_matches = pd.merge(df_match_data, df_player_table, on='Player ID', how='left')

        cola, colb = st.columns([2,6])

        with cola:
            st.write("### Select Player")
            # 2. Add player dropdown filter
            player_list = df_player_table['Name'].unique()
            selected_player_name = st.selectbox("Choose a Player", player_list)

            # 3. Get Selected Player ID and filter match data
            selected_player_id = df_player_table[df_player_table['Name'] == selected_player_name]['Player ID'].values[0]
            df_selected_player = df_match_data[df_match_data['Player ID'] == selected_player_id]

            df_player_training = df_training_data[df_training_data["Player ID"] == selected_player_id]
            #work out player attendances
            player_attendance = pd.DataFrame({"Status": ["Attended", "Missed"], "Count": [df_player_training["Attended"].sum(), df_player_training["Missed"].sum(),],})
            #setup doughnut chart
            fig_player_att = px.pie(player_attendance, names="Status", values="Count", hole=0.4, color="Status", color_discrete_map={"Attended": "#2ecc71", "Missed": "#e74c3c"},)
            #Plot doughnut chart
            st.plotly_chart(fig_player_att)

        with colb:
            with st.container(border=True):
    
                st.write(f"Season stats - **{selected_player_name}**")
                # Create columns inside the container
                col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)

                # Calculate total matches for the selected player to prevent ZeroDivisionError
                total_player_matches = df_selected_player["Match ID"].nunique()

                #create metrics within the columns
                with col1:
                    st.metric("Matches", value=int(total_player_matches))
                with col2:
                    st.metric("Goals", value=int(df_selected_player["Goals"].sum()))
                with col3:
                    st.metric("Shots", value=int(df_selected_player["Shots"].sum()))
                with col4:
                    st.metric("Assists", value=int(df_selected_player["Assist"].sum()))
                with col5:
                    st.metric("Pass", value=int(df_selected_player["Key Pass"].sum()))
                with col6:
                    st.metric("Saves", value=int(df_selected_player["Saves"].sum()))
                with col7:
                    st.metric("Tackles", value=int(df_selected_player["Tcks made"].sum()))
                with col8:
                    st.metric("Missed Tackles", value=int(df_selected_player["Tcks miss"].sum()))
                with col9:
                    st.metric("MVP", value=int(df_selected_player["MVP"].sum()))

            with st.container(border=True):
                st.write("Stats per match")
                col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
            
                # Prevent division by zero if a player has no matches logged
                match_denom = total_player_matches if total_player_matches > 0 else 1

                with col1:
                    st.metric("Matches", value=1 if total_player_matches > 0 else 0)
                with col2:
                    st.metric("Goals", value=round(df_selected_player["Goals"].sum() / match_denom, 2))
                with col3:
                    st.metric("Shots", value=round(df_selected_player["Shots"].sum() / match_denom, 2))
                with col4:
                    st.metric("Assists", value=round(df_selected_player["Assist"].sum() / match_denom, 2))
                with col5:
                    st.metric("Pass", value=round(df_selected_player["Key Pass"].sum() / match_denom, 2))
                with col6:
                    st.metric("Saves", value=round(df_selected_player["Saves"].sum() / match_denom, 2))
                with col7:
                    st.metric("Tackles", value=round(df_selected_player["Tcks作 made" if "Tcks作 made" in df_selected_player else "Tcks made"].sum() / match_denom, 2))
                with col8:
                    st.metric("Missed Tackles", value=round(df_selected_player["Tcks miss"].sum() / match_denom, 2))
                with col9:
                    st.metric("MVP", value=round(df_selected_player["MVP"].sum() / match_denom, 2))
        
            #Linegraaph of individual player match stats
            df_matches = pd.merge(df_selected_player, df_fixtures_table, on='Match ID', how='left')
            df_match_stats = df_matches.groupby('Date')["Date","Goals", "Shots", "Assist", "Key Pass", "Saves", "Tcks made", "Tcks miss", "MVP"].sum().reset_index()
            fig_stats = px.line(df_match_stats, x="Date", y=df_match_stats.columns, hover_data={"Date": "|%B %d, %Y"})
            fig_stats.update_xaxes(dtick="M1",tickformat="%b\n%Y")
            st.plotly_chart(fig_stats)

    #Tab for the Season Summary
    with tab3:
        cola, colb = st.columns(2)

        with cola:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric("Wins", value = int((df_fixtures_table["Result"] == "W").sum()))
                with col2:
                    st.metric("Draws", value = int((df_fixtures_table["Result"] == "D").sum()))
                with col3:
                    st.metric("Losses", value = int((df_fixtures_table["Result"] == "L").sum()))
                with col4:
                    st.metric("Goal Diff", value = (int(df_fixtures_table["Goals For"].sum()) - int(df_fixtures_table["Goals Against"].sum())))
                with col5:
                    st.metric("Points", value = ((int((df_fixtures_table["Result"] == "W").sum()) * 3) + int((df_fixtures_table["Result"] == "D").sum())))
        
            #Cumulative points linechart
            df_fixtures_table = calc_points(df_fixtures_table)#['Points'] = np.select(result, points, default=0)
            fig_points = px.ecdf(df_fixtures_table, x="Date", y="Points")
            st.plotly_chart(fig_points)

            #Cup Results Dataframe
            df_results = pd.merge(df_fixtures_table, df_opposition_table, on='Opposition ID', how='left')
            df_results_table = df_results[['Date', 'Name', 'Result', 'Goals For', 'Goals Against', 'League/Cup', 'Round']].rename(columns={'Name': 'Opposition Name'})
            df_cup_results = df_results_table[df_results_table['League/Cup'] == "Cup"]
            st.dataframe(df_cup_results, column_config={"Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY")},hide_index=True)    



        with colb:
            #results by opposition
            df_results = pd.merge(df_fixtures_table, df_opposition_table, on='Opposition ID', how='left')
            df_results_table = df_results[['Name', 'Result', 'Goals For', 'Goals Against']].rename(columns={'Name': 'Opposition Name'})
            #add calculated columns
            df_results_table["Wins"] = np.where(df_results_table["Result"] == "W", 1, 0)
            df_results_table["Draws"] = np.where(df_results_table["Result"] == "D", 1, 0)
            df_results_table["Losses"] = np.where(df_results_table["Result"] == "L", 1, 0)
            df_results_table = calc_points(df_results_table)#['Points'] = np.select(result, points, default=0)
            #Display final Dataframe
            st.dataframe(df_results_table.groupby('Opposition Name')['Opposition Name', 'Wins', 'Draws', 'Losses', 'Goals For', 'Goals Against', 'Points'].sum())

            #Player stats for the season
            df_players = pd.merge(df_match_data, df_player_table, on='Player ID', how='left')
            df_players_stats = df_players[["Name","Pld", "Goals", "Shots", "Assist", "Key Pass", "Saves", "Tcks made", "Tcks miss"]]
            st.dataframe(df_players_stats.groupby("Name")["Pld", "Goals", "Shots", "Assist", "Key Pass", "Saves", "Tcks made", "Tcks miss"].sum())
    

    
    # Optional logout option
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.rerun()

