import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:5000'

st.set_page_config(page_title="SpotiSpect", page_icon=":musical_note:", layout="wide")

auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-read-recently-played user-top-read user-read-private user-library-read',
    show_dialog=True
)

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'spotify_token' not in st.session_state:
    st.session_state.spotify_token = None

def navigate_to(page_name):
    st.session_state.current_page = page_name

def home_page():
    st.header("Spotify Artist Insights", divider="green")
    st.write("Analyze how you and the world listen to your favourite artists on Spotify.")
    st.markdown("""
        - Explore personalized metrics for your favorite artists.
        - View global popularity and trends of top artists.
        - Visualize listening habits with charts and graphs.
    """)
    st.markdown("Connect your Spotify account to proceed.", help="By connecting your Spotify account, you are granting permission to SpotiSpect to access your [Spotify data](https://i.imgur.com/fhbO43z.png). You can remove this access at any time in your account settings. For more information about how SpotiSpect can use your personal data, please see SpotiSpect's privacy policy.")
    if st.button('Login with Spotify', help="Click twice to proceed. [Know Why](https://docs.streamlit.io/develop/concepts/design/buttons#:~:text=Buttons%20created%20with,becomes%20False.)."):
        navigate_to('login')

def login_page():
    st.header('Authorization Status', divider="green")
    try:
        if st.session_state.spotify_token is None:
            token = auth_manager.get_access_token(as_dict=False)
            st.session_state.spotify_token = token
        sp = spotipy.Spotify(auth=st.session_state.spotify_token)
        
        user = sp.current_user()
        st.success(f"Logged in as {user['display_name']}")
        
        if st.button('Go to Dashboard', help="Click twice to proceed. [Know Why](https://docs.streamlit.io/develop/concepts/design/buttons#:~:text=Buttons%20created%20with,becomes%20False.)."):
            navigate_to('dashboard')
    except Exception as e:
        st.error("Login failed. Please try again.")
        st.write(e)

def dashboard_page():
    st.header('Dashboard', divider="green")

    sp = spotipy.Spotify(auth=st.session_state.spotify_token)

    artist_search = st.text_input("Search for an artist:")

    if artist_search:
        results = sp.search(q=artist_search, type='artist', limit=50)  
        exact_match_artist = None

        for artist in results['artists']['items']:
            if artist['name'].lower() == artist_search.lower():
                exact_match_artist = artist
                break

        if exact_match_artist:
            artist = exact_match_artist
            st.subheader(f"Artist: {artist['name']}")
            
            if artist['images']:
                st.image(artist['images'][0]['url'], width=200, caption=artist['name'])

            option = st.radio("Choose Dashboard:", ['User Metrics', 'Global Metrics'])

            if option == 'User Metrics':
                user_dashboard(sp, artist)
            else:
                global_dashboard(sp, artist)
        else:
            st.error("Artist not found. Please enter the correct name and try again.")

def user_dashboard(sp, artist):
    st.header("User Metrics")

    artist_name = artist['name']
    user_tracks = sp.current_user_recently_played(limit=50)
    artist_tracks = []

    for item in user_tracks['items']:
        track = item['track']
        if artist_name.lower() in [artist.lower() for artist in [a['name'] for a in track['artists']]]:
            artist_tracks.append({
                'Track Name': track['name'],
                'Streams': track['popularity'] 
            })

    recent_tracks = sp.current_user_recently_played(limit=50)
    artist_plays = [item['track']['artists'][0]['name'] for item in recent_tracks['items']]
    artist_count = artist_plays.count(artist['name'])
    st.metric(f"Recent Plays for {artist_name}", artist_count, help="Based on the last 50 tracks you played on Spotify.")

    if artist_tracks:
        df = pd.DataFrame(artist_tracks)
        fig = px.bar(df, x='Track Name', y='Streams', title=f"Streams for {artist_name}", labels={'Streams': 'Stream Count', 'Track Name': 'Tracks'})
        fig.update_traces(marker_color = "#1cc658")
        st.plotly_chart(fig)
    else:
        st.write("You have not listened to this artist recently.")

    timestamps_with_day = [
    {
        'Hour': pd.Timestamp(item['played_at']).hour,
        'Day': pd.Timestamp(item['played_at']).day_name()
    }
    for item in recent_tracks['items']
    ]
    time_df_with_day = pd.DataFrame(timestamps_with_day).value_counts().reset_index(name='Count')
    fig3 = px.density_heatmap(
    time_df_with_day,
    x='Hour',
    y='Day',
    z='Count',
    color_continuous_scale=px.colors.sequential.Plasma,
    title="Time and Day Listening Preferences",
    labels={'Hour': 'Hour of the Day', 'Day': 'Day of the Week'}
    )
    st.plotly_chart(fig3)

def global_dashboard(sp, artist):
    st.header("Global Metrics")

    popularity = artist['popularity']
    followers = artist['followers']['total']
    st.metric("Popularity Score", popularity)
    st.metric("Follower Count", followers)

    top_tracks = sp.artist_top_tracks(artist['id'])['tracks']
    track_names = [track['name'] for track in top_tracks]
    track_popularity = [track['popularity'] for track in top_tracks]

    df_global_tracks = pd.DataFrame({
        'Track Name': track_names,
        'Popularity': track_popularity
    })

    st.subheader("Top Tracks by Popularity")
    st.bar_chart(df_global_tracks.set_index('Track Name'))

    genres = artist['genres']
    genre_df = pd.DataFrame({'Genre': genres, 'Count': [1] * len(genres)})

    fig = px.pie(genre_df, names='Genre', values='Count', title="Genre Distribution")
    st.plotly_chart(fig)

page = st.session_state.get('current_page', 'home')

if page == 'home':
    home_page()
elif page == 'login':
    login_page()
elif page == 'dashboard':
    dashboard_page()







