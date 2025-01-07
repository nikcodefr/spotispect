# SpotiSpect
Analyze how you and the world listen to your favorite artists on Spotify.
- Explore personalized metrics for your favorite artists.
- View global popularity and trends of top artists.
- Visualize listening habits with charts and graphs.
  
https://github.com/user-attachments/assets/39764bb3-4ad7-4af7-8ba5-d410b9f393ec

# Prerequisites:
Ensure that `pip@24.3.1` and `python@3.12` are installed.

# Installation:
Clone this repository and move into the project directory.
```
git clone https://github.com/nikcodefr/spotispect.git
cd spotispect
```
Install the dependencies in `requirements.txt`.
```
pip install -r requirements.txt
```

# Set up Spotify application:
- Create a new application on [Spotify's Developer Dashboard](https://developer.spotify.com/dashboard).
- Add ```http://localhost:5000``` under the `Redirect URIs` section. Ensure this matches the value of the `REDIRECT_URI` variable written in `main.py`.
- Select the `Web API` checkbox and complete app creation.

# Set up Environment Variables:
- Go to your app's settings on Spotify's Developer Dashboard and find the values of your `CLIENT_ID` and `CLIENT_SECRET`.
- Add the variables in a `.env` file. Refer `example.env` in the repository structure.

# Usage:
Run the application file.
```
streamlit run main.py
```
The application should be up and running on the `Local URL` visible in the terminal. Use `Ctrl + Click` to open the link on your browser.
  




