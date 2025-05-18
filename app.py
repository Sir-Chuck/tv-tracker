import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- App Config ---
st.set_page_config(page_title="TV Show Tracker", layout="centered")

st.title("📺 My TV Show Tracker")

# --- Load or Create Tracker ---
@st.cache_data
def load_data():
    try:
        return pd.read_csv("tv_tracker.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Title", "Year", "Genre", "IMDb Rating", 
            "Network", "Production", "My Rating", 
            "Date Watched", "Favorite Character", 
            "Notes", "Status"
        ])

data = load_data()

# --- OMDb API Call ---
OMDB_API_KEY = "ead2f7a6"

def fetch_show_data(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}&type=series"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return None

# --- Search Field ---
title_input = st.text_input("Search for a TV Show")

if title_input:
    show = fetch_show_data(title_input)

    if show and show.get("Response") == "True":
        # Display IMDb Info
        st.image(show.get("Poster"), width=200)
        st.markdown(f"## {show['Title']}")
        st.write(f"**Years Aired**: {show.get('Year', 'N/A')}")
        st.write(f"**Genre**: {show.get('Genre', 'N/A')}")
        st.write(f"**IMDb Rating**: ⭐ {show.get('imdbRating', 'N/A')}")
        st.write(f"**Production**: {show.get('Production', 'N/A')}")
        st.write(f"**Released**: {show.get('Released', 'N/A')}")

        # --- Custom Rating Form ---
        with st.form("rating_form"):
            st.subheader("📓 Your Rating")
            my_rating = st.slider("My Rating (1-10)", 1, 10, 5)
            date_watched = st.date_input("Date Watched", value=date.today())
            fav_char = st.text_input("Favorite Character")
            notes = st.text_area("Notes / Review")
            status = st.selectbox("Status", ["Watching", "Completed"])
            submitted = st.form_submit_button("Save Entry")

            if submitted:
                new_entry = {
                    "Title": show["Title"],
                    "Year": show["Year"],
                    "Genre": show["Genre"],
                    "IMDb Rating": show["imdbRating"],
                    "Network": show["Released"],  # Approximation
                    "Production": show.get("Production", "N/A"),
                    "My Rating": my_rating,
                    "Date Watched": date_watched,
                    "Favorite Character": fav_char,
                    "Notes": notes,
                    "Status": status
                }
                data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
                data.to_csv("tv_tracker.csv", index=False)
                st.success("✅ Saved to Watchlist!")

    else:
        st.error("❌ Show not found. Try refining your title.")

# --- Show Tracker Table ---
if not data.empty:
    st.subheader("📘 Your Watchlist")
    st.dataframe(data)

    if st.checkbox("🔽 Show raw data"):
        st.write(data)

    if st.checkbox("📤 Export to CSV"):
        csv = data.to_csv(index=False)
        st.download_button("Download CSV", csv, "tv_tracker.csv", "text/csv")

