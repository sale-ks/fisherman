import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime
import urllib.parse

# --- 1. KONFIGURACIJA ---
if "GEMINI_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_KEY"]
else:
    st.error("API ključ nedostaje u Secrets!")
    st.stop()

genai.configure(api_key=API_KEY)
MODEL_NAME = 'gemini-2.0-flash' 

LOKALNE_RADNJE = {
    "Beograd": ["Formax Store", "DTD Ribarstvo", "Carpologija", "Alas", "Ribolovac"],
    "Kruševac": ["Predator", "Ribolovačka radnja Profi", "Rasina", "Ribosport"],
    "Niš": ["Formax Store Niš", "Plovak-Mare", "Enter Fishing Shop", "Eagle Eye"],
    "Novi Sad": ["Formax Store", "Travar", "Riboshop", "Carpologija NS"],
    "Kragujevac": ["Ribosport", "Srebrna Udica", "Marlin", "Formax Store KG"],
    "Čačak": ["Barbus", "Ribolovac Čačak", "Udica"],
    "Kraljevo": ["Ribolovac KV", "Trofej", "Blinker"],
    "Subotica": ["Plovak SU", "Ribomarket", "Zlatna Udica"],
    "Šabac": ["Zlatna Ribica", "Delfin", "Šaran Šabac"],
    "Smederevo": ["Dunavski Vuk", "Ribolovac SD"],
    "Pančevo": ["Tamiški Ribolovac", "Plovak PA"],
    "Valjevo": ["Kolubara Ribolov", "Keder"]
}

ZABRANE = {
    "Šaran": {"info": "01. apr - 31. maj"},
    "Deverika": {"info": "15. apr - 31. maj"},
    "Mrena": {"info": "15. apr - 31. maj"},
    "Skobalj": {"info": "15. apr - 31. maj"},
    "Babuška": {"info": "Nema zabrane"},
    "Amur": {"info": "Nema zabrane"}
}

# Inicijalizacija Session State
for key in ['shopping_list', 'taktika_tekst', 'mesta_tekst', 'checked_items']:
    if key not in st.session_state: st.session_state[key] = [] if 'list' in key or 'tekst' in key else {}
if 'prikaz_moda' not in st.session_state: st.session_state.prikaz_moda = "📋 Taktika"

def get_weather(grad):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={grad}&count=1&format=json").json()
        if "results" in geo:
            res = geo["results"][0]
            w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={res['latitude']}&longitude={res['longitude']}&current_weather=true").json()
            return f"{w['current_weather']['temperature']}°C"
        return "N/A"
    except: return "Greška"

# --- 2. VIZUELNO PODEŠAVANJE (AGRESIVNI CSS) ---
st.set_page_config(page_title="Feeder Majstor PRO", page_icon="🎣", layout="centered")

st.markdown("""
    <style>
    /* Sakriva Toolbar (krunu, GitHub, profil) */
    .stAppToolbar { display: none !important; }
    /* Sakriva Footer */
    footer { visibility: hidden !important; height: 0px !important; }
    /* Sakriva statusne ikonice */
    [data-testid="stStatusWidget"] { display: none !important; }
    /* Sakriva Viewer Badge (donji desni ugao) */
    .stAppViewerBadge { display: none !important; }
    /* Smanjuje header prostor */
    header { visibility: hidden !important; height: 0px !important; }
    /* Pomeranje sadržaja na vrhu */
    .block-container { padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GLAVNI EKRAN ---
st.title("🎣 Feeder Majstor PRO")

with st.container(border=True):
    c1, c2 = st.columns([1, 2])
    with c1: grad = st.text_input("📍 Grad:", "Beograd", key="grad_widget")
    with c2: brendovi = st.multiselect("🥣 Brendovi:", [
        "Svi brendovi", "Gica Mix", "Maros Mix", "Sensas", "VDE", 
        "Haldorado", "Benzar Mix", "Feedermania", "Formax Elegance", "CPK"
    ], default=["Svi brendovi"])

    c3, c4 = st.columns(2)
    with c3: voda = st.selectbox("💧 Voda:", ["Stajaća voda", "Spori tok", "Brza reka", "Komercijala"])
    with c4: riba = st.selectbox("🐟 Riba:", list(ZABRANE.keys()))
    
    iskustvo = st.select_slider("🧠 Iskustvo:", ["Početnik", "Srednje", "Iskusan"])
    budzet = st.radio("💰 Budžet:", ["Ekonomičan", "Standard", "Premium"], horizontal=True)

if st.button("SASTAVI KOMPLETAN PLAN 🚀", use_container_width=True, type="primary"):
    vreme_info = get_weather(grad)
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"Ekspert si za feeder. Lokacija {grad}, Vreme {vreme_info}, Riba {riba}, Voda {voda}, Brendovi {brendovi}, Budžet {budzet}. Daj [TAKTIKA], [MESTA] i [LISTA] (razdvojeno zarezima)."
        with st.spinner('Sastavljam plan...'):
            res_text = model.generate_content(prompt).text
            if "[LISTA]" in res_text and "[MESTA]" in res_text:
                st.session_state.taktika_tekst = res_text.split("[TAKTIKA]")[1].split("[MESTA]")[0].strip()
                st.session_state.mesta_tekst = res_text.split("[MESTA]")[1].split("[LISTA]")[0].strip()
                lista_raw = res_text.split("[LISTA]")[1].strip()
                st.session_state.shopping_list = [i.strip() for i in lista_raw.split(",") if i.strip()]
                st.session_state.checked_items = {item: False for item in st.session_state.shopping_list}
                st.session_state.prikaz_moda = "📋 Taktika"
    except Exception as e:
        st.error(f"Greška: {e}")

# --- 4. PRIKAZ REZULTATA (SA TABOM ZA RADNJE) ---
if st.session_state.taktika_tekst:
    st.markdown("---")
    st.session_state.prikaz_moda = st.radio(
        "Izaberi prikaz:", 
        ["📋 Taktika", "📍 Gde pecati?", "🛒 Šoping Lista", "🛒 Prodavnice"], 
        horizontal=True, key="nav_radio"
    )

    if st.session_state.prikaz_moda == "📋 Taktika":
        st.markdown(st.session_state.taktika_tekst)
    elif st.session_state.prikaz_moda == "📍 Gde pecati?":
        st.markdown(st.session_state.mesta_tekst)
    elif st.session_state.prikaz_moda == "🛒 Šoping Lista":
        selektovano = []
        for i, item in enumerate(st.session_state.shopping_list):
            res = st.checkbox(item, key=f"cb_f_{i}", value=st.session_state.checked_items.get(item, False))
            st.session_state.checked_items[item] = res
            if res: selektovano.append(item)
        if selektovano:
            txt = f"SPISAK ZA PECANJE ({grad}):\n" + "\n".join([f"- {s}" for s in selektovano])
            encoded_txt = urllib.parse.quote(txt)
            c1, c2, c3 = st.columns(3)
            with c1: st.download_button("💾 TXT", txt, "spisak.txt", use_container_width=True)
            with c2: st.link_button("📲 WA", f"https://wa.me/?text={encoded_txt}", use_container_width=True)
            with c3: st.link_button("💜 Viber", f"viber://forward?text={encoded_txt}", use_container_width=True)
    
    # NOVI TAB: PRODAVNICE I MAPE (Umesto Sidebara)
    elif st.session_state.prikaz_moda == "🛒 Prodavnice":
        st.subheader(f"Prodavnice u gradu {grad}")
        map_url = f"https://www.google.com/maps/search/ribolovacka+oprema+{grad}"
        st.link_button(f"🔍 Otvori Google Mapu za: {grad}", map_url, use_container_width=True)
        
        nadjen_grad = next((g for g in LOKALNE_RADNJE if grad.lower() == g.lower()), None)
        if nadjen_grad:
            st.write(f"**Preporučene radnje u gradu {nadjen_grad}:**")
            for r in LOKALNE_RADNJE[nadjen_grad]:
                st.success(f"🏬 {r}")
        else:
            st.info("Koristi dugme iznad da vidiš sve radnje na mapi.")