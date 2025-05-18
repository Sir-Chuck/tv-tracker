import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- Password Gate ---
st.set_page_config(page_title="TV Tracker", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("🔒 Enter password to access app", type="password")
    if pw == st.secrets["APP_PASSWORD"]:
        st.session_state.authenticated = True
        st.experimental_rerun()
    else:
        st.stop()

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
CSV_FILE = "tv_data.csv"

# --- Load Data ---
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

# --- IMDb API via RapidAPI ---
def fetch_imdb_data(title):
    headers = {
        "X-RapidAPI-Key": st.secrets["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com"
    }

    # Step 1: Search
    search_url = "https://imdb8.p.rapidapi.com/title/find"
    search_params = {"q": title}
    search_res = requests.get(search_url, headers=headers, params=search_params).json()

    results = search_res.get("results", [])
    if not results:
        st.error("❌ No results found.")
        return {}

    options = [f"{r.get('title', '')} ({r.get('year', 'N/A')})" for r in results if r.get("id", "").startswith("/title/")]
    selection = st.selectbox("🎯 Select the correct show", options)
    selected_id = results[options.index(selection)]["id"].split("/")[-2]

    # Step 2: Details + Ratings
    detail_url = "https://imdb8.p.rapidapi.com/title/get-details"
    rating_url = "https://imdb8.p.rapidapi.com/title/get-ratings"

    details = requests.get(detail_url, headers=headers, params={"tconst": selected_id}).json()
    ratings = requests.get(rating_url, headers=headers, params={"tconst": selected_id}).json()

    # Genre
    genres = ", ".join(details.get("genres", [])) if details.get("genres") else ""

    # Production
    prod = details.get("production", {}).get("company", {}).get("name") or \
           details.get("productionStatus", {}).get("status") or ""

    # Streaming platform guess
    network_guess = details.get("production", {}).get("distributor", {}).get("name", "")
    streaming = network_guess or "N/A"

    return {
        "Title": details.get("title", ""),
        "Genre": genres,
        "Rating": ratings.get("rating", ""),
        "Years": str(details.get("year", "")),
        "Production": prod,
        "Streaming": streaming
    }

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
autofill = fetch_imdb_data(title_input) if title_input else {}

with st.form("add_form"):
    title = st.text_input("Title", value=autofill.get("Title", ""))
    genre = st.text_input("Genre", value=autofill.get("Genre", ""))
    watched = st.selectbox("Watched Status", ["Completed", "In Progress", "Ongoing", "Not Started"])
    rating = st.text_input("IMDb Rating", value=autofill.get("Rating", ""))
    years = st.text_input("Years it Ran", value=autofill.get("Years", ""))
    streaming = st.text_input("Streaming Platform", value=autofill.get("Streaming", ""))
    production = st.text_input("Production", value=autofill.get("Production", ""))

    st.markdown("### 🎯 Your Personal Scores (0–10)")
    fw = st.slider("First Watch", 0.0, 10.0, 5.0, step=0.1)
    rw = st.slider("Rewatchability", 0.0, 10.0, 5.0, step=0.1)
    orig = st.slider("Originality", 0.0, 10.0, 5.0, step=0.1)
    chars = st.slider("Characters", 0.0, 10.0, 5.0, step=0.1)
    prod_score = st.slider("Production Quality", 0.0, 10.0, 5.0, step=0.1)
    concl = st.slider("Conclusiveness", 0.0, 10.0, 5.0, step=0.1)
    writing = st.slider("Writing", 0.0, 10.0, 5.0, step=0.1)

    if st.form_submit_button("Add Show"):
        # Autofill missing fields just in case
        if not genre or not rating or not years or not production:
            fallback = fetch_imdb_data(title)
            genre = genre or fallback.get("Genre", "")
            rating = rating or fallback.get("Rating", "")
            years = years or fallback.get("Years", "")
            production = production or fallback.get("Production", "")
            streaming = streaming or fallback.get("Streaming", "")

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
        st.success(f"✅ '{title}' added to your tracker!")

# --- Export CSV ---
if not data.empty:
    csv = data.to_csv(index=False)
    st.download_button("📥 Download Tracked Shows (CSV)", csv, "tv_data.csv", "text/csv")
