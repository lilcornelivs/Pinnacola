import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Pinnacola Live Sync", page_icon="🃏")

# --- CONNESSIONE AL DATABASE (Google Sheets) ---
# Sostituisci l'URL sotto con quello del TUO foglio Google
url = "https://docs.google.com/spreadsheets/d/11J-xlOau6L9_6qz_1pQt4QZGX5uIFVjU-n94fiXuOtk/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)


def get_data():
    return conn.read(spreadsheet=url, ttl="0s")  # ttl=0 forza l'aggiornamento immediato


def save_data(df):
    conn.update(spreadsheet=url, data=df)


# --- CARICAMENTO DATI ---
df = get_data()

# --- SIDEBAR: ARCHIVIO E STATISTICHE ---
with st.sidebar:
    st.header("📊 Archivio Storico")

    if not df.dropna().empty:
        # Calcolo chiusure totali
        chiusure = df['Chi_Ha_Chiuso'].value_counts()
        st.write("**Record Chiusure:**")
        st.write(chiusure)

        st.divider()
        st.write("**Tutte le mani giocate:**")
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Nessun dato nell'archivio.")

    if st.button("🗑️ Svuota Database (Reset Totale)"):
        reset_df = pd.DataFrame(columns=["Partita", "Mano", "Punti_Bababui", "Punti_Io", "Chi_Ha_Chiuso"])
        save_data(reset_df)
        st.rerun()

# --- LOGICA PUNTEGGI ATTUALI ---
st.title("🃏 Pinnacola Live Score")

soglia = st.number_input("Soglia Vittoria", value=1500, step=500)

if not df.dropna().empty:
    n_partita_attuale = df['Partita'].max()
    partita_attuale = df[df['Partita'] == n_partita_attuale]
    tot_g1 = partita_attuale['Punti_Bababui'].sum()
    tot_g2 = partita_attuale['Punti_Io'].sum()
else:
    n_partita_attuale = 1
    tot_g1, tot_g2 = 0, 0

# Dashboard
c1, c2 = st.columns(2)
c1.metric("Bababui", int(tot_g1))
c2.metric("Io", int(tot_g2))

st.divider()

# --- INSERIMENTO MANO ---
st.subheader(f"📝 Inserisci Mano (Partita {n_partita_attuale})")

with st.form("form_punti", clear_on_submit=True):
    col_p1, col_p2, col_chi = st.columns(3)
    p1 = col_p1.number_input("Punti Bababui", step=1, value=0)
    p2 = col_p2.number_input("Punti Io", step=1, value=0)
    chi_chiude = col_chi.selectbox("Chi ha chiuso?", ["Nessuno", "Bababui", "Io"])

    submit = st.form_submit_button("REGISTRA MANO")

if submit:
    # Calcolo nuova mano
    nuova_mano_n = len(df[df['Partita'] == n_partita_attuale]) + 1 if not df.dropna().empty else 1

    nuova_riga = pd.DataFrame([{
        "Partita": int(n_partita_attuale),
        "Mano": nuova_mano_n,
        "Punti_Bababui": p1,
        "Punti_Io": p2,
        "Chi_Ha_Chiuso": chi_chiude
    }])

    updated_df = pd.concat([df, nuova_riga], ignore_index=True)
    save_data(updated_df)
    st.rerun()

# --- LOGICA VITTORIA ---
if tot_g1 >= soglia or tot_g2 >= soglia:
    vincitore = "Bababui" if tot_g1 >= soglia else "Io"
    st.balloons()
    st.success(f"🏆 {vincitore.upper()} HA VINTO!")

    if st.button("🏁 Chiudi Partita e inizia la prossima"):
        nuova_partita_riga = pd.DataFrame([{
            "Partita": int(n_partita_attuale + 1),
            "Mano": 0,
            "Punti_Bababui": 0,
            "Punti_Io": 0,
            "Chi_Ha_Chiuso": "START"
        }])
        updated_df = pd.concat([df, nuova_partita_riga], ignore_index=True)
        save_data(updated_df)
        st.rerun()
