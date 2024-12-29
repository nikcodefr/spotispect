import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:5000'

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope='user-read-recently-played user-top-read user-read-private user-read-email user-follow-read playlist-read-private user-library-read'
    )
)

st.set_page_config(page_title='Spotify Song Analysis', page_icon=':musical_note:')
st.title('Welcome')
st.write('Analyze songs from your favorite artists')

top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')

track_names = [track['name'] for track in top_tracks['items']]
track_durations = [track['duration_ms'] / 60000 for track in top_tracks['items']]  

df = pd.DataFrame({
    'Track Name': track_names,
    'Duration (Minutes)': track_durations
})
df.set_index('Track Name', inplace=True)

st.subheader('Track Durations for Your Top Tracks')
st.bar_chart(df, height=500)


