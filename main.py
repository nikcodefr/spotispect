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

            option = st.radio("Choose Dashboard:", ['Personal Metrics', 'Global Metrics'])

            if option == 'Personal Metrics':
                user_dashboard(sp, artist)
            else:
                global_dashboard(sp, artist)
        else:
            st.error("Artist not found. Please enter the correct name and try again.")

def user_dashboard(sp, artist):
    st.header("Personal Metrics", divider="gray")

    artist_name = artist['name']
    user_tracks = sp.current_user_recently_played(limit=50)

    if not user_tracks or 'items' not in user_tracks or not user_tracks['items']:
        st.markdown(":red-background[No recent tracks found in your Spotify listening history.]")
        return

    artist_tracks = []

    for item in user_tracks['items']:
        track = item['track']
        if artist_name.lower() in [artist.lower() for artist in [a['name'] for a in track['artists']]]:
            artist_tracks.append({
                'Track Name': track['name'],
                'Streams': track['popularity'] 
            })

    recent_tracks = sp.current_user_recently_played(limit=50)
    artist_plays = [
        artist['name']
        for item in recent_tracks['items']
        for artist in item['track']['artists']
        if artist_name.lower() == artist['name'].lower()]
    artist_count = len(artist_plays)
    st.metric(f"Recent Plays for {artist_name}", artist_count, help="Based on the last 50 tracks you played on Spotify. Includes features.")

    cols_per_row = 6

    if artist_tracks:
        track_play_counts = pd.DataFrame([
            {'Track Name': item['track']['name'], 'Play Count': 1}
            for item in user_tracks['items']
            if artist_name.lower() in [artist.lower() for artist in [a['name'] for a in item['track']['artists']]]
        ]).groupby('Track Name').sum().reset_index()

        fig = px.bar(
            track_play_counts,
            x='Track Name',
            y='Play Count',
            title=f"Streams for {artist_name}",
            labels={'Play Count': 'Number of Plays', 'Track Name': 'Track'},
        )
        fig.update_traces(marker_color="#1cc658")
        st.plotly_chart(fig)

        #Code to print favourites by artist

        artist_albums = pd.DataFrame([
            {
            'Album Name': item['track']['album']['name'],
            'Artist': ", ".join(a['name'] for a in item['track']['album']['artists']),
            'Album Cover': item['track']['album']['images'][0]['url'],
            'Year': pd.Timestamp(item['track']['album']['release_date']).year
            }
            for item in user_tracks['items']
            if artist_name.lower() in [artist.lower() for artist in [a['name'] for a in item['track']['artists']]]
        ]).drop_duplicates(subset='Album Name').sort_values(by='Year', ascending=False)

        if not artist_albums.empty:
            st.markdown(f"**Top Albums with {artist_name}**")
            rows = [artist_albums.iloc[i:i + cols_per_row] for i in range(0, len(artist_albums), cols_per_row)]

            for row in rows:
                cols = st.columns(cols_per_row)
                for col, (_, album) in zip(cols, row.iterrows()):
                    with col:
                        st.image(album['Album Cover'], width=200, caption=f"{album['Album Name']} ({album['Year']}) • {album['Artist']}")
        else:
            st.markdown(":red-background[You have not listened to an album with this artist recently.]")

        #Code to print first track

        artist_albums = pd.DataFrame([
            {
            'Album Name': item['track']['album']['name'],
            'Artist': ", ".join(a['name'] for a in item['track']['album']['artists']),
            'Album Cover': item['track']['album']['images'][0]['url'],
            'Year': pd.Timestamp(item['track']['album']['release_date']).year
            }
            for item in user_tracks['items']
            if artist_name.lower() in [artist.lower() for artist in [a['name'] for a in item['track']['artists']]]
        ]).drop_duplicates(subset='Album Name').sort_values(by='Year', ascending=False)

        if not artist_albums.empty:
            album_distribution = artist_albums['Album Name'].value_counts(normalize=True) * 100
            fig2 = px.pie(
                names=album_distribution.index,
                values=album_distribution.values,
                title=f"Album Distribution for {artist_name}",
            )
            st.plotly_chart(fig2)
    else:
        st.markdown(":red-background[You have not listened to this artist recently.]")

    st.header("General Stats", divider="gray")

    st.markdown("**Top Streams**", help="Based on the last 50 tracks you played on Spotify.")

    if user_tracks['items']:
        track_play_counts = pd.DataFrame([
        {
            'Track Name': item['track']['name'],
            'Artist Name': ", ".join(artist['name'] for artist in item['track']['artists']),
            'Play Count': 1
        }
        for item in user_tracks['items']
    ]).groupby(['Track Name', 'Artist Name']).sum().reset_index()

    track_play_counts['Track Label'] = track_play_counts['Track Name'] + " by " + track_play_counts['Artist Name']

    fig = px.bar(
        track_play_counts,
        x='Track Label',
        y='Play Count',
        labels={'Play Count': 'Number of Plays'},
    )
    fig.update_traces(marker_color="#1cc658", hovertemplate='%{x}<br>Number of Plays=%{y}')

    fig.update_layout(
        xaxis=dict(
            showticklabels=False, 
            title="Track",
            title_font=dict(size=14)
        ),
        yaxis_title="Number of Plays",
        margin=dict(l=40, r=40, t=40, b=80)
    )

    fig.add_annotation(
        text="▲  Hover over bars for track details.",
        xref="paper", yref="paper",
        x=0.5, y=-0.2, 
        showarrow=False,
        font=dict(size=14, color="gray"),
        align="center"
    )

    st.plotly_chart(fig)

    st.markdown("**Top Albums**", help="Based on the last 50 tracks you played on Spotify.")
    general_albums = pd.DataFrame([
        {
        'Album Name': item['track']['album']['name'],
        'Artist': ", ".join(a['name'] for a in item['track']['album']['artists']),
        'Album Cover': item['track']['album']['images'][0]['url'],
        'Year': pd.Timestamp(item['track']['album']['release_date']).year
        }
        for item in user_tracks['items']
    ]).drop_duplicates(subset='Album Name').sort_values(by='Year', ascending=False)

    if not general_albums.empty:
        cols_per_row = 8
        rows = [general_albums.iloc[i:i + cols_per_row] for i in range(0, len(general_albums), cols_per_row)]

        for row in rows:
            cols = st.columns(cols_per_row)
            for col, (_, album) in zip(cols, row.iterrows()):
                with col:
                    st.image(album['Album Cover'], width=150, caption=f"{album['Album Name']} ({album['Year']}) • {album['Artist']}")
    else:
        st.markdown(":red-background[No albums found in your recent listening history.]")

    st.markdown("**Top Genres**", help="Based on the last 50 tracks you played on Spotify.")

    genres = [genre for item in user_tracks['items'] for genre in sp.artist(item['track']['artists'][0]['id'])['genres']]
    genre_counts = pd.DataFrame(genres, columns=['Genre']).value_counts(normalize=True).reset_index(name='Percentage')
    fig_genre = px.pie(
        genre_counts,
        names='Genre',
        values='Percentage',
    )
    st.plotly_chart(fig_genre)

    total_ms = sum(item['track']['duration_ms'] for item in user_tracks['items'])
    total_minutes = total_ms // 60000
    st.metric("Listening Duration", f"{total_minutes // 60} hrs {total_minutes % 60} mins", help="Based on the last 50 tracks you played on Spotify.")

    st.markdown("**Listening Hours**", help="Based on the last 50 tracks you played on Spotify.")

    timestamps = [
        pd.Timestamp(item['played_at']).hour
        for item in user_tracks['items']
    ]
    active_hours = pd.DataFrame(timestamps, columns=['Hour']).value_counts().reset_index(name='Count')
    fig_time = px.bar(
        active_hours,
        x='Hour',
        y='Count',
        labels={'Hour': 'Hour of the Day', 'Count': 'Number of Tracks Played'}
    )
    st.plotly_chart(fig_time)

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
    st.header("Global Metrics", divider="gray")

    popularity = artist['popularity']
    followers = artist['followers']['total']
    st.metric("Popularity Score", popularity, help="Out of 100.")
    st.metric("Follower Count", followers)

    top_tracks = sp.artist_top_tracks(artist['id'])['tracks']
    track_names = [track['name'] for track in top_tracks]
    track_popularity = [track['popularity'] for track in top_tracks]

    max_length = 20 
    short_track_names = [
    name if len(name) <= max_length else name[:max_length] + "..." 
    for name in track_names
    ]

    df_global_tracks = pd.DataFrame({
    'Short Track Name': short_track_names,
    'Full Track Name': track_names,         
    'Popularity': track_popularity
    })

    fig = px.bar(
        df_global_tracks,
        x='Short Track Name',
        y='Popularity',
        title="Top Tracks by Popularity",
        labels={'Short Track Name': 'Track', 'Popularity': 'Popularity Score'},
    )
    fig.update_traces(
    hovertemplate='<b>%{customdata}</b><br>Popularity: %{y}',
    customdata=df_global_tracks['Full Track Name'],            
    marker_color="#1cc658",                                    
    )
    st.plotly_chart(fig)

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







