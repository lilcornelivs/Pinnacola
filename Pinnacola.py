import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr", layout="wide")

# !!! INCOLLA QUI SOTTO IL TUO LINK CHE FINISCE CON /exec !!!
API_URL = "https://script.google.com/macros/s/AKfycbx9EZz8y8V19YkL0NMo8ic1oV5J411Mb71kx7mpLX0rofl2yAOOLcya_ozxoEWD8vIB9w/exec"

# Aggiornamento automatico ogni 5 secondi per il tempo reale
st_autorefresh(interval=5000, key="datarefresh")

def get_data():
    try:
        r = requests.get(API_URL)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame(columns=["partita", "mano", "p1", "p2", "chi"])

# --- CARICAMENTO DATI ---
df = get_data()

# Conversione dati in numeri
if not df.empty:
    for col in ['partita', 'mano', 'p1', 'p2']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# Sidebar (Impostazioni e Reset)
with st.sidebar:
    st.header("⚙️ Impostazioni")
    soglia = st.number_input("Soglia Vittoria", value=1500, step=500)
    st.divider()
    if st.button("🗑️ Reset Totale Torneo"):
        requests.post(API_URL, json={"action": "reset"})
        st.rerun()

# --- LOGICA CALCOLO VITTORIE (IL MEDAGLIERE) ---
vinte_makka, vinte_omo = 0, 0
if not df.empty and df['partita'].max() > 0:
    partite_tot = df.groupby('partita').agg({'p1': 'sum', 'p2': 'sum'})
    vinte_makka = (partite_tot['p1'] >= soglia).sum()
    vinte_omo = (partite_tot['p2'] >= soglia).sum()
    n_p = df['partita'].max()
    curr = df[df['partita'] == n_p]
    tot1, tot2 = curr['p1'].sum(), curr['p2'].sum()
else:
    n_p, tot1, tot2 = 1, 0, 0

# --- DASHBOARD PRINCIPALE ---
st.title("🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr") 

# Medagliere
m1, m2 = st.columns(2)
m1.subheader(f"🏆 Makka Pakka: {vinte_makka}")
m2.subheader(f"🏆 Omo Cratolo: {vinte_omo}")

st.divider()

# Punteggio Partita Corrente
c1, c2 = st.columns(2)
c1.metric("MAKKA PAKKA (Punti)", int(tot1))
c2.metric("OMO CRATOLO (Punti)", int(tot2))

st.divider()

# --- INSERIMENTO PUNTI (Supporta NEGATIVI e casella vuota) ---
if tot1 < soglia and tot2 < soglia:
    st.subheader("📝 Registra Mano")
    with st.form("form_mano", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        # value=None toglie lo 0 automatico. min_value=-2000 permette i negativi.
        val1 = col1.number_input("Punti Makka Pakka", value=None, placeholder="Inserisci...", min_value=-2000, max_value=2000)
        val2 = col2.number_input("Punti Omo Cratolo", value=None, placeholder="Inserisci...", min_value=-2000, max_value=2000)
        chi_chiude = col3.selectbox("Chi ha chiuso?", ["Nessuno", "Makka Pakka", "Omo Cratolo"])
        
        if st.form_submit_button("REGISTRA"):
            nuova_mano = {
                "action": "add",
                "partita": int(n_p),
                "mano": len(curr[curr['chi'] != 'START']) + 1 if not df.empty else 1,
                "p1": val1 if val1 is not None else 0,
                "p2": val2 if val2 is not None else 0,
                "chi": chi_chiude
            }
            requests.post(API_URL, json=nuova_mano)
            st.rerun()
else:
    st.balloons()
    vincitore = "Makka Pakka" if tot1 >= soglia else "Omo Cratolo"
    st.success(f"🏆 {vincitore.upper()} HA VINTO LA PARTITA!")
    if st.button("🏁 Inizia Nuova Partita"):
        nuova_p = {"action": "add", "partita": int(n_p + 1), "mano": 0, "p1": 0, "p2": 0, "chi": "START"}
        requests.post(API_URL, json=nuova_p)
        st.rerun()

# --- STORICO IN TEMPO REALE ---
st.divider()
st.subheader("📜 Storico della Partita")
if not df.empty:
    display_df = df[(df['partita'] == n_p) & (df['chi'] != 'START')]
    if not display_df.empty:
        # Rinominiamo le colonne per la visualizzazione
        display_df = display_df.rename(columns={
            'p1': 'Punti Makka Pakka', 
            'p2': 'Punti Omo Cratolo', 
            'chi': 'Chiusura'
        })
        st.table(display_df.sort_values(by="mano", ascending=False))
