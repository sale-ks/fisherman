import streamlit as st
import google.generativeai as genai

# 1. Podešavanje API-ja
# OBAVEZNO: Koristi svoj novi API ključ
API_KEY = "AIzaSyDiktOM2X-FVEJZu_A4pIex_m8KTDWQ8K8" 
genai.configure(api_key=API_KEY)

# --- KLJUČNA IZMENA: KORISTIMO MODEL IZ 2026. GODINE ---
# Umesto gemini-1.5-flash (koji je ugašen), koristimo 2.5 ili 3.0
MODEL_NAME = 'gemini-2.5-flash' 

try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"Model {MODEL_NAME} nije dostupan. Pokušavam sa novijom verzijom...")
    model = genai.GenerativeModel('gemini-3-flash') # Rezervna opcija

# --- UI DEO (Standardno) ---
st.title("🎣 Feeder Majstor v3.0 (2026 Edition)")

voda = st.selectbox("Tip vode:", ["Stajaća voda", "Spori tok", "Brza reka", "Komercijala"])
riba = st.selectbox("Ciljana riba:", ["Deverika", "Šaran", "Babuška", "Mrena", "Skobalj"])
sezona = st.selectbox("Sezona:", ["Proleće", "Leto", "Jesen", "Zima"])
iskustvo = st.select_slider("Iskustvo:", ["Početnik", "Srednje", "Iskusan"])
vreme = st.radio("Vremenske prilike:", ["Sunčano", "Oblačno", "Kiša", "Vetrovito"], horizontal=True)

if st.button("SASTAVI MI TAKTIKU 🚀", use_container_width=True):
    try:
        prompt = f"""
        Ti si ekspert za feeder ribolov. Korisnik peca na {voda}, cilj je {riba}. 
        Vreme je {vreme}, sezona {sezona}. Iskustvo ribolovca: {iskustvo}.
        Sastavi profesionalan plan na srpskom jeziku:
        1. Mix hrane i aditivi.
        2. Montaža, udica i predvez.
        3. Glavni mamci.
        4. Taktika hranjenja.
        """

        with st.spinner(f'Molimo vas sacekajte'):
            response = model.generate_content(prompt)
            st.success("Taktika generisana!")
            st.markdown(response.text)
            st.balloons()

    except Exception as e:
        if "404" in str(e):
            st.error("Greška 404: Google je ugasio ovaj model. Promeni MODEL_NAME u 'gemini-3-flash'.")
        elif "429" in str(e):
            st.error("Ispucana kvota! Sačekaj 60 sekundi.")
        else:
            st.error(f"Greška: {e}")