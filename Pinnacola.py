import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Pinnacola LIVE", layout="wide")

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


# --- LOGICA ---
st.title("🃏 Pinnacola Live Sync")
df = get_data()

# Converti i dati in numeri
if not df.empty:
    df[['partita', 'mano', 'p1', 'p2']] = df[['partita', 'mano', 'p1', 'p2']].apply(pd.to_numeric)

# Impostazioni Sidebar
with st.sidebar:
    soglia = st.number_input("Soglia Vittoria", value=1500, step=500)
    if st.button("🗑️ Reset Totale"):
        requests.delete(f"{API_URL}/all")
        st.rerun()

# Calcolo Punteggi
if not df.empty:
    n_p = df['partita'].max()
    curr = df[df['partita'] == n_p]
    tot1, tot2 = curr['p1'].sum(), curr['p2'].sum()
else:
    n_p, tot1, tot2 = 1, 0, 0

# Dashboard
c1, c2 = st.columns(2)
c1.metric("BABABUI", int(tot1))
c2.metric("IO", int(tot2))

st.divider()

# --- INSERIMENTO (Senza lo 0 iniziale) ---
if tot1 < soglia and tot2 < soglia:
    st.subheader("📝 Registra Mano")
    with st.form("form_mano", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        # value=None toglie lo 0 automatico
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
    st.success(f"🏆 {vincitore.upper()} HA VINTO!")
    if st.button("🏁 Nuova Partita"):
        nuova_p = {"partita": int(n_p + 1), "mano": 0, "p1": 0, "p2": 0, "chi": "START"}
        requests.post(API_URL, json={"data": [nuova_p]})
        st.rerun()

# --- STORICO IN TEMPO REALE ---
st.divider()
st.subheader("📜 Storico della Partita")
if not df.empty:
    # Mostra la tabella con le ultime mani in alto
    st.table(df[df['partita'] == n_p].sort_values(by="mano", ascending=False))
