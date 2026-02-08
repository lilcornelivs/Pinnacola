import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Pinaculo d l cratoli", layout="wide")

# Link magico di SheetDB (Metti il tuo qui)
API_URL = "https://sheetdb.io/api/v1/za39slqkwuwfj"

# Aggiornamento automatico ogni 5 secondi per il tempo reale
st_autorefresh(interval=5000, key="datarefresh")

def get_data():
    try:
        response = requests.get(API_URL)
        return pd.DataFrame(response.json())
    except:
        return pd.DataFrame(columns=["partita", "mano", "p1", "p2", "chi"])

# --- CARICAMENTO DATI ---
df = get_data()

# Converti i dati in numeri (se presenti)
if not df.empty:
    df[['partita', 'mano', 'p1', 'p2']] = df[['partita', 'mano', 'p1', 'p2']].apply(pd.to_numeric)

# Impostazioni Sidebar
with st.sidebar:
    st.header("⚙️ Impostazioni")
    soglia = st.number_input("Soglia Vittoria", value=1500, step=500)
    st.divider()
    if st.button("🗑️ Reset Totale Torneo"):
        requests.delete(f"{API_URL}/all")
        st.rerun()

# --- LOGICA CALCOLO VITTORIE (IL MEDAGLIERE) ---
vinte_baba = 0
vinte_io = 0

if not df.empty:
    # Raggruppiamo i punti per ogni partita giocata
    partite_totali = df.groupby('partita').agg({'p1': 'sum', 'p2': 'sum'})
    # Contiamo quante volte Bababui o Io abbiamo superato la soglia
    vinte_baba = (partite_totali['p1'] >= soglia).sum()
    vinte_io = (partite_totali['p2'] >= soglia).sum()
    
    # Partita attuale
    n_p = df['partita'].max()
    curr = df[df['partita'] == n_p]
    tot1, tot2 = curr['p1'].sum(), curr['p2'].sum()
else:
    n_p, tot1, tot2 = 1, 0, 0

# --- DASHBOARD PRINCIPALE ---
st.title("🃏 Pinnacola Live Sync")

# Riga superiore con Vittorie Totali (Medagliere) e Punti Correnti
m1, m2 = st.columns(2)
m1.subheader(f"🏆 Partite Vinte Bababui: {vinte_baba}")
m2.subheader(f"🏆 Partite Vinte Io: {vinte_io}")

st.divider()

c1, c2 = st.columns(2)
c1.metric("PUNTI BABABUI (Partita attuale)", int(tot1))
c2.metric("PUNTI IO (Partita attuale)", int(tot2))

st.divider()

# --- INSERIMENTO (Senza lo 0 iniziale) ---
if tot1 < soglia and tot2 < soglia:
    st.subheader("📝 Registra Mano")
    with st.form("form_mano", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        val1 = col1.number_input("Punti Bababui", value=None, placeholder="Scrivi...")
        val2 = col2.number_input("Punti Io", value=None, placeholder="Scrivi...")
        chi_chiude = col3.selectbox("Chi ha chiuso?", ["Nessuno", "Bababui", "Io"])
        
        if st.form_submit_button("REGISTRA"):
            nuova_mano = {
                "partita": int(n_p),
                "mano": len(curr) + 1 if not df.empty else 1,
                "p1": val1 if val1 is not None else 0,
                "p2": val2 if val2 is not None else 0,
                "chi": chi_chiude
            }
            requests.post(API_URL, json={"data": [nuova_mano]})
            st.rerun()
else:
    st.balloons()
    vincitore = "Bababui" if tot1 >= soglia else "Io"
    st.success(f"🏆 {vincitore.upper()} HA VINTO LA PARTITA!")
    if st.button("🏁 Inizia Nuova Partita"):
        nuova_p = {"partita": int(n_p + 1), "mano": 0, "p1": 0, "p2": 0, "chi": "START"}
        requests.post(API_URL, json={"data": [nuova_p]})
        st.rerun()

# --- STORICO IN TEMPO REALE ---
st.divider()
st.subheader("📜 Storico della Partita Corrente")
if not df.empty:
    st.table(df[df['partita'] == n_p].sort_values(by="mano", ascending=False))
