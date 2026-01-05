import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime

# --- 1. KONFIGURACIJA I PODACI ---
API_KEY = "AIzaSyDiktOM2X-FVEJZu_A4pIex_m8KTDWQ8K8" # Zameni svojim ključem
genai.configure(api_key=API_KEY)

# Podaci o zabranama (Lovostaj u Srbiji/Regionu)
# Formati: (mesec_pocetka, dan_pocetka, mesec_kraja, dan_kraja)
ZABRANE = {
    "Šaran": {"period": (4, 1, 5, 31), "info": "01. april - 31. maj"},
    "Deverika": {"period": (4, 15, 5, 31), "info": "15. april - 31. maj"}, # ISPRAVLJENO: 5. mesec, 31. dan
    "Mrena": {"period": (4, 15, 5, 31), "info": "15. april - 31. maj"},
    "Skobalj": {"period": (4, 15, 5, 31), "info": "15. april - 31. maj"},
    "Babuška": {"period": None, "info": "Nema zabrane (invazivna vrsta)"},
    "Amur": {"period": None, "info": "Nema zabrane"}
}

# Funkcija za automatsko određivanje godišnjeg doba
def get_current_season():
    month = datetime.now().month
    if 3 <= month <= 5: return "Proleće"
    elif 6 <= month <= 8: return "Leto"
    elif 9 <= month <= 11: return "Jesen"
    else: return "Zima"

# Funkcija za provere zabrane
def proveri_zabranu(riba):
    today = datetime.now()
    podaci = ZABRANE.get(riba)
    
    if not podaci or not podaci["period"]:
        return False, podaci["info"] if podaci else "Nema podataka"
    
    try:
        m_start, d_start, m_end, d_end = podaci["period"]
        start_date = datetime(today.year, m_start, d_start)
        end_date = datetime(today.year, m_end, d_end)
        
        u_zabrani = start_date <= today <= end_date
        return u_zabrani, podaci["info"]
    except ValueError:
        return False, "Greška u kalendaru zabrana"

# Funkcija za vreme (Open-Meteo)
def get_weather(grad):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={grad}&count=1&format=json"
        geo_res = requests.get(geo_url).json()
        if "results" in geo_res:
            lat, lon = geo_res["results"][0]["latitude"], geo_res["results"][0]["longitude"]
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=surface_pressure"
            w_res = requests.get(w_url).json()
            temp = w_res["current_weather"]["temperature"]
            press = w_res["hourly"]["surface_pressure"][0]
            return f"Temp: {temp}°C, Pritisak: {press}hPa"
        return "Vreme: nedostupno"
    except: return "Vreme: greška"

# --- 2. INTERFEJS ---
st.set_page_config(page_title="Feeder Majstor Smart", page_icon="🎣")

# Automatski podaci
danasnji_datum = datetime.now().strftime("%d. %m. %Y.")
sezona = get_current_season()

st.title("🎣 Feeder Majstor PRO")
st.subheader(f"📅 Danas je: {danasnji_datum} | Sezona: {sezona}")

grad = st.text_input("📍 Unesi grad u kom pecaš:", "Beograd")

col1, col2 = st.columns(2)
with col1:
    voda = st.selectbox("Tip vode:", ["Stajaća voda", "Spori tok", "Brza reka", "Komercijala"])
    riba = st.selectbox("Ciljana riba:", list(ZABRANE.keys()))
with col2:
    iskustvo = st.select_slider("Tvoje iskustvo:", ["Početnik", "Srednje", "Iskusan"])

# Provera zabrane i ispis
u_zabrani, info_period = proveri_zabranu(riba)
if u_zabrani:
    st.error(f"⚠️ PAŽNJA: **{riba}** je trenutno u ZABRANI (Lovostaj)! Period: {info_period}. Molimo te da ribu odmah vratiš u vodu.")
else:
    st.success(f"✅ {riba} nije u zabrani. Lovostaj je: {info_period}.")

# --- 3. GENERISANJE TAKTIKE ---
if st.button("SASTAVI MOJU TAKTIKU 🚀"):
    info_vreme = get_weather(grad)
    
    # Model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Ti si profesionalni ribolovac. Danas je {danasnji_datum}, sezona je {sezona}.
    Vreme na lokaciji {grad} je {info_vreme}.
    Korisnik peca ribu: {riba} na vodi: {voda}.
    Njegovo iskustvo je {iskustvo}.

    Sastavi preciznu taktiku na srpskom jeziku:
    1. Recept za hranu prilagođen temperaturi od {info_vreme}.
    2. Najbolji sistem i mamac.
    3. Kratak savet za ovu sezonu ({sezona}).
    """

    with st.spinner('Analiziram uslove...'):
        try:
            response = model.generate_content(prompt)
            st.markdown("---")
            st.markdown(response.text)
            if u_zabrani:
                st.warning("Napomena: Taktika je generisana u edukativne svrhe, poštuj pravila lovostaja!")
        except Exception as e:
            st.error(f"Greška: {e}")