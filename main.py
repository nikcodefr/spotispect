import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px

# Load environment variables
load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:5000'

# Streamlit app configuration
st.set_page_config(page_title="Spotify Song Analysis", page_icon=":musical_note:", layout="wide")

# Initialize Spotify API with show_dialog=True
auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-read-recently-played user-top-read user-read-private user-library-read',
    show_dialog=True
)

# Simulate routing with session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'spotify_token' not in st.session_state:
    st.session_state.spotify_token = None

def navigate_to(page_name):
    st.session_state.current_page = page_name

# Home Page
def home_page():
    st.title('Spotify Song Analysis')
    st.write("Analyze your favorite songs and artists, and explore global trends!")
    if st.button('Login with Spotify'):
        navigate_to('login')

# Login Page
def login_page():
    st.title('Authenticating...')
    try:
        # Get Spotify token
        if st.session_state.spotify_token is None:
            token = auth_manager.get_access_token(as_dict=False)
            st.session_state.spotify_token = token
        sp = spotipy.Spotify(auth=st.session_state.spotify_token)
        
        # Fetch user information
        user = sp.current_user()
        st.success(f"Logged in as {user['display_name']}")
        
        if st.button('Go to Dashboard'):
            navigate_to('dashboard')
    except Exception as e:
        st.error("Login failed. Please try again.")
        st.write(e)

# Dashboard Page
def dashboard_page():
    st.title('Dashboard')

    # Initialize Spotify API using stored token
    sp = spotipy.Spotify(auth=st.session_state.spotify_token)

    # Single search bar for both User and Global metrics
    artist_search = st.text_input("Search for an artist:")

    if artist_search:
        results = sp.search(q=artist_search, type='artist', limit=1)
        if results['artists']['items']:
            artist = results['artists']['items'][0]
            st.subheader(f"Artist: {artist['name']}")
            
            # Display artist's profile picture
            if artist['images']:
                st.image(artist['images'][0]['url'], width=200, caption=artist['name'])

            # Simulate tabbed navigation for user and global metrics
            option = st.radio("Choose Dashboard:", ['User Metrics', 'Global Metrics'])

            if option == 'User Metrics':
                user_dashboard(sp, artist)
            else:
                global_dashboard(sp, artist)
        else:
            st.error("Artist not found. Please try again.")

# User Dashboard
def user_dashboard(sp, artist):
    st.header("User Metrics")

    artist_name = artist['name']
    user_tracks = sp.current_user_recently_played(limit=50)
    artist_tracks = []

    # Extract streams and track names for the inputted artist
    for item in user_tracks['items']:
        track = item['track']
        if artist_name.lower() in [artist.lower() for artist in [a['name'] for a in track['artists']]]:
            artist_tracks.append({
                'Track Name': track['name'],
                'Streams': track['popularity']  # Popularity as a proxy for streams
            })

    if artist_tracks:
        df = pd.DataFrame(artist_tracks)
        st.subheader(f"Number of Streams for Tracks by {artist_name}")
        fig = px.bar(df, x='Track Name', y='Streams', title=f"Streams for {artist_name}", labels={'Streams': 'Stream Count', 'Track Name': 'Tracks'})
        st.plotly_chart(fig)
    else:
        st.write("No tracks by this artist found in your listening history.")

    # Listening History Metrics
    recent_tracks = sp.current_user_recently_played(limit=50)
    artist_plays = [item['track']['artists'][0]['name'] for item in recent_tracks['items']]
    artist_count = artist_plays.count(artist['name'])
    st.metric("Total Plays for Artist", artist_count)

    # Time of Day Preferences (Example Heatmap)
    timestamps = [pd.Timestamp(item['played_at']).hour for item in recent_tracks['items']]
    time_df = pd.DataFrame({'Hour': timestamps}).value_counts().reset_index(name='Count')
    fig = px.density_heatmap(time_df, x='Hour', y='Count', title="Time of Day Preferences")
    st.plotly_chart(fig)

# Global Dashboard
def global_dashboard(sp, artist):
    st.header("Global Metrics")

    # Artist Popularity
    popularity = artist['popularity']
    followers = artist['followers']['total']
    st.metric("Popularity Score", popularity)
    st.metric("Follower Count", followers)

    # Top Tracks Globally
    top_tracks = sp.artist_top_tracks(artist['id'])['tracks']
    track_names = [track['name'] for track in top_tracks]
    track_popularity = [track['popularity'] for track in top_tracks]

    df_global_tracks = pd.DataFrame({
        'Track Name': track_names,
        'Popularity': track_popularity
    })

    st.subheader("Top Tracks by Popularity")
    st.bar_chart(df_global_tracks.set_index('Track Name'))

    # Genre Analysis
    genres = artist['genres']
    genre_df = pd.DataFrame({'Genre': genres, 'Count': [1] * len(genres)})
    fig = px.pie(genre_df, names='Genre', values='Count', title="Genre Distribution")
    st.plotly_chart(fig)

# Main App Logic
if st.session_state.current_page == 'home':
    home_page()
elif st.session_state.current_page == 'login':
    login_page()
elif st.session_state.current_page == 'dashboard':
    dashboard_page()






