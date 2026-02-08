import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Pinnacola LIVE", layout="wide")

# --- AUTO-REFRESH (TEMPO REALE) ---
# Ogni 5 secondi l'app si aggiorna da sola per vedere se l'altro ha inserito punti
st_autorefresh(interval=5000, key="datarefresh")

# --- DATABASE ---
url = "https://docs.google.com/spreadsheets/d/11J-xlOau6L9_6qz_1pQt4QZGX5uIFVjU-n94fiXuOtk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)


def get_data():
    # ttl=0 per non usare la cache e avere dati freschi
    return conn.read(spreadsheet=url, ttl="0s").dropna(how='all')


def save_data(df):
    conn.update(spreadsheet=url, data=df)


df = get_data()

# --- INTERFACCIA ---
st.title("🃏 Pinnacola Real-Time Score")

# Barra laterale solo per impostazioni e reset
with st.sidebar:
    soglia = st.number_input("Soglia Vittoria", value=1500, step=500)
    if st.button("⚠️ Reset Totale Torneo"):
        reset_df = pd.DataFrame(columns=["Partita", "Mano", "Punti_Bababui", "Punti_Io", "Chi_Ha_Chiuso"])
        save_data(reset_df)
        st.rerun()

# Calcolo punteggi
if not df.empty:
    n_partita = int(df['Partita'].max())
    attuale = df[df['Partita'] == n_partita]
    tot1 = attuale['Punti_Bababui'].sum()
    tot2 = attuale['Punti_Io'].sum()
else:
    n_partita, tot1, tot2 = 1, 0, 0

# DASHBOARD PUNTEGGI
c1, c2 = st.columns(2)
c1.metric("BABABUI", int(tot1))
c2.metric("IO", int(tot2))

st.divider()

# --- INSERIMENTO (Sincronizzato) ---
vinto = tot1 >= soglia or tot2 >= soglia

if not vinto:
    st.subheader("📝 Inserisci Punti Mano")
    # Nota: Streamlit non permette di "svuotare al click" nativamente,
    # ma usando value=None lo zero non c'è e appare il cursore vuoto.
    with st.form("form_mano", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)
        p1 = col_a.number_input("Punti Bababui", value=None, placeholder="Scrivi punti...")
        p2 = col_b.number_input("Punti Io", value=None, placeholder="Scrivi punti...")
        chi = col_c.selectbox("Chi ha chiuso?", ["Nessuno", "Bababui", "Io"])

        if st.form_submit_button("REGISTRA"):
            # Se p1 o p2 sono None, li trasformiamo in 0
            val1 = p1 if p1 is not None else 0
            val2 = p2 if p2 is not None else 0

            mano_n = len(df[df['Partita'] == n_partita]) + 1
            nuova = pd.DataFrame(
                [{"Partita": n_partita, "Mano": mano_n, "Punti_Bababui": val1, "Punti_Io": val2, "Chi_Ha_Chiuso": chi}])
            updated = pd.concat([df, nuova], ignore_index=True)
            save_data(updated)
            st.rerun()
else:
    st.balloons()
    vincitore = "Bababui" if tot1 >= soglia else "Io"
    st.success(f"🏆 {vincitore.upper()} HA VINTO!")
    if st.button("Inizia Nuova Partita"):
        nuova_p = pd.DataFrame(
            [{"Partita": n_partita + 1, "Mano": 0, "Punti_Bababui": 0, "Punti_Io": 0, "Chi_Ha_Chiuso": "START"}])
        updated = pd.concat([df, nuova_p], ignore_index=True)
        save_data(updated)
        st.rerun()

st.divider()

# --- STORICO IN TEMPO REALE (Sempre visibile a entrambi) ---
st.subheader("📜 Storico della Partita Corrente")
if not df.empty:
    # Mostriamo solo la partita in corso, ordinata per l'ultima mano inserita
    st.dataframe(df[df['Partita'] == n_partita].sort_values(by="Mano", ascending=False), use_container_width=True)

    st.divider()
    st.subheader("📈 Riepilogo Chiusure Totali")
    chiusure = df[df['Chi_Ha_Chiuso'].isin(['Bababui', 'Io'])]['Chi_Ha_Chiuso'].value_counts()
    st.write(chiusure)
