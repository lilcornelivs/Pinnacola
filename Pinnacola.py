import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr", layout="wide")

# !!! USA IL TUO URL DI GOOGLE APPS SCRIPT (quello che finisce con /exec) !!!
API_URL = "https://script.google.com/macros/s/AKfycbyittMfGZOp6v58WiGI0hQT1G2_Va2Yr0qaZRSppG3GKOkN8t5WB7zy364pPabaKevubA/exec"

# Aggiornamento automatico ogni 5 secondi
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

# --- GESTIONE SOGLIA PERSISTENTE ---
soglia_salvata = 1500 # Default
if not df.empty:
    config_row = df[df['chi'] == 'CONFIG']
    if not config_row.empty:
        soglia_salvata = int(config_row.iloc[-1]['partita'])

# Sidebar
with st.sidebar:
    st.header("⚙️ Impostazioni")
    nuova_soglia = st.number_input("Soglia Vittoria", value=soglia_salvata, step=100)
    
    if st.button("💾 Salva Soglia per sempre"):
        requests.post(API_URL, json={"action": "set_soglia", "valore": int(nuova_soglia)})
        st.success(f"Soglia impostata a {nuova_soglia}!")
        st.rerun()
        
    st.divider()
    if st.button("🗑️ Reset Totale Torneo"):
        requests.post(API_URL, json={"action": "reset"})
        st.rerun()

# --- LOGICA CALCOLO VITTORIE ---
soglia = nuova_soglia
vinte_makka, vinte_omo = 0, 0
df_partite = df[df['chi'] != 'CONFIG']

if not df_partite.empty and df_partite['partita'].max() > 0:
    partite_tot = df_partite.groupby('partita').agg({'p1': 'sum', 'p2': 'sum'})
    vinte_makka = (partite_tot['p1'] >= soglia).sum()
    vinte_omo = (partite_tot['p2'] >= soglia).sum()
    n_p = df_partite['partita'].max()
    curr = df_partite[df_partite['partita'] == n_p]
    tot1, tot2 = curr['p1'].sum(), curr['p2'].sum()
else:
    n_p, tot1, tot2 = 1, 0, 0

# --- DASHBOARD PRINCIPALE ---
st.title("🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr") 

m1, m2 = st.columns(2)
m1.subheader(f"🏆 Makka Pakka: {vinte_makka}")
m2.subheader(f"🏆 Omo Cratolo: {vinte_omo}")

st.divider()

c1, c2 = st.columns(2)
c1.metric("MAKKA PAKKA (Punti)", int(tot1))
c2.metric("OMO CRATOLO (Punti)", int(tot2))

st.divider()

# --- INSERIMENTO PUNTI ---
if tot1 < soglia and tot2 < soglia:
    st.subheader("📝 Registra Mano")
    st.info("💡 Puoi scrivere il segno meno (es: -30) per i punti negativi.")
    with st.form("form_mano", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        # value=None permette di avere la casella vuota all'inizio
        # min_value=-5000 permette di digitare il simbolo "-"
        # step=5 imposta il salto dei pulsanti + e -
        val1 = col1.number_input("Punti Makka Pakka", value=None, placeholder="-30, 50, ecc...", min_value=-5000, max_value=5000, step=5)
        val2 = col2.number_input("Punti Omo Cratolo", value=None, placeholder="-30, 50, ecc...", min_value=-5000, max_value=5000, step=5)
        
        chi_chiude = col3.selectbox("Chi ha chiuso?", ["Nessuno", "Makka Pakka", "Omo Cratolo"])
        
        if st.form_submit_button("REGISTRA"):
            nuova_mano = {
                "action": "add",
                "partita": int(n_p),
                "mano": len(curr[curr['chi'] != 'START']) + 1 if not df_partite.empty else 1,
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

st.divider()
st.subheader("📜 Storico della Partita")
if not df_partite.empty:
    display_df = df_partite[(df_partite['partita'] == n_p) & (~df_partite['chi'].isin(['START', 'CONFIG']))]
    if not display_df.empty:
        display_df = display_df.rename(columns={'p1': 'Punti Makka Pakka', 'p2': 'Punti Omo Cratolo', 'chi': 'Chiusura'})
        st.table(display_df.sort_values(by="mano", ascending=False))
