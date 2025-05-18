import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- Config ---
st.set_page_config(page_title="TV Tracker", layout="wide")

# --- Styles ---
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: Verdana !important;
            color: #2a2a2a;
        }
        .title {
            font-family: 'Courier New', monospace;
            font-size: 38px;
            font-weight: 400;
            margin-bottom: 0;
        }
        .chuck {
            font-size: 20px;
            font-weight: 600;
            margin-top: -10px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">TV Tracker</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="chuck">
        <span style="color:#f27802">C</span>
        <span style="color:#2e0854">H</span>
        <span style="color:#7786c8">U</span>
        <span style="color:#708090">C</span>
        <span style="color:#b02711">K</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Constants ---
OMDB_API_KEY = "ead2f7a6"
CSV_FILE = "tv_data.csv"

# --- Load CSV ---
@st.cache_data
def load_data():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        columns = [
            "Title", "Genre", "Watched", "Rating", "Years", "Streaming", "Production",
            "First Watch", "Rewatchability", "Originality", "Characters",
            "Production Score", "Conclusiveness", "Writing", "Avg Score"
        ]
        return pd.DataFrame(columns=columns)

data = load_data()

# --- OMDb Search ---
def fetch_omdb_data(title):
    # Fallback using known IMDb IDs
    imdb_id = MANUAL_IMDB_IDS.get(title.strip())
    if imdb_id:
        url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
        res = requests.get(url).json()
        if res.get("Response") == "True":
            return {
                "Title": res.get("Title", ""),
                "Genre": res.get("Genre", ""),
                "Rating": res.get("imdbRating", ""),
                "Years": res.get("Year", ""),
                "Production": res.get("Production", "")
            }

    # Fuzzy search fallback
    search_url = f"http://www.omdbapi.com/?s={title}&apikey={OMDB_API_KEY}&type=series"
    search_res = requests.get(search_url).json()
    search_results = search_res.get("Search", [])

    if search_results:
        options = [f"{item['Title']} ({item.get('Year', 'N/A')})" for item in search_results]
        selection = st.selectbox("🎯 Select the correct show", options)
        selected_title = selection.split(" (")[0]

        selected_url = f"http://www.omdbapi.com/?t={selected_title}&apikey={OMDB_API_KEY}&type=series"
        selected_res = requests.get(selected_url).json()

        if selected_res.get("Response") == "True":
            return {
                "Title": selected_res.get("Title", ""),
                "Genre": selected_res.get("Genre", ""),
                "Rating": selected_res.get("imdbRating", ""),
                "Years": selected_res.get("Year", ""),
                "Production": selected_res.get("Production", "")
            }

    st.error("❌ No show found. Try refining your search.")
    return {}


# --- Upload CSV ---
st.markdown("📂 **Upload a CSV to start or use the form below to add new shows.**")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    data = pd.read_csv(uploaded_file)
    data.to_csv(CSV_FILE, index=False)
    st.success("✅ CSV uploaded successfully!")

# --- Display Table ---
st.subheader("📊 My Tracked Shows")
if "Avg Score" in data.columns:
    st.dataframe(data.sort_values("Avg Score", ascending=False), use_container_width=True)
else:
    st.dataframe(data, use_container_width=True)

st.markdown("---")

# --- Add New Show ---
st.header("➕ Add a New Show")

title_input = st.text_input("TV Show Title")
autofill = fetch_omdb_data(title_input) if title_input else {}

with st.form("add_form"):
    title = st.text_input("Title", value=autofill.get("Title", ""))
    genre = st.text_input("Genre", value=autofill.get("Genre", ""))
    watched = st.selectbox("Watched Status", ["Completed", "In Progress", "Ongoing", "Not Started"])
    rating = st.text_input("IMDb Rating", value=autofill.get("Rating", ""))
    years = st.text_input("Years it Ran", value=autofill.get("Years", ""))
    streaming = st.text_input("Streaming Platform")
    production = st.text_input("Production", value=autofill.get("Production", ""))

    st.markdown("### 🎯 Your Personal Scores (0–10)")
    fw = st.slider("First Watch", 0, 10, 5)
    rw = st.slider("Rewatchability", 0, 10, 5)
    orig = st.slider("Originality", 0, 10, 5)
    chars = st.slider("Characters", 0, 10, 5)
    prod_score = st.slider("Production Quality", 0, 10, 5)
    concl = st.slider("Conclusiveness", 0, 10, 5)
    writing = st.slider("Writing", 0, 10, 5)

    if st.form_submit_button("Add Show"):
        # Fill missing fields
        if not genre or not rating or not years or not production:
            omdb_fallback = fetch_omdb_data(title)
            genre = genre or omdb_fallback.get("Genre", "")
            rating = rating or omdb_fallback.get("Rating", "")
            years = years or omdb_fallback.get("Years", "")
            production = production or omdb_fallback.get("Production", "")

        avg = round((fw + rw + orig + chars + prod_score + concl + writing) / 7, 2)
        new_row = {
            "Title": title,
            "Genre": genre,
            "Watched": watched,
            "Rating": rating,
            "Years": years,
            "Streaming": streaming,
            "Production": production,
            "First Watch": fw,
            "Rewatchability": rw,
            "Originality": orig,
            "Characters": chars,
            "Production Score": prod_score,
            "Conclusiveness": concl,
            "Writing": writing,
            "Avg Score": avg
        }
        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
        data.to_csv(CSV_FILE, index=False)
        st.success(f"✅ '{title}' added to tracker!")

# --- Download Button ---
if not data.empty:
    csv = data.to_csv(index=False)
    st.download_button("📥 Download Tracked Shows (CSV)", csv, "tv_data.csv", "text/csv")
