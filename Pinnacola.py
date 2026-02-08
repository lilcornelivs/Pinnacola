import streamlit as st
import pandas as pd

# --- INIZIALIZZAZIONE DATI ---
if 'partite' not in st.session_state:
    st.session_state.partite = []
if 'vinte_g1' not in st.session_state:
    st.session_state.vinte_g1 = 0
if 'vinte_g2' not in st.session_state:
    st.session_state.vinte_g2 = 0
if 'n_partita' not in st.session_state:
    st.session_state.n_partita = 1

st.set_page_config(page_title="Pinnacola Scoreboard", page_icon="🃏")

# --- SIDEBAR (Impostazioni) ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    soglia = st.number_input("Soglia Vittoria", value=1500, step=500)

    st.divider()
    st.subheader("🏆 Medagliere Totale")
    st.write(f"**Bababui:** {st.session_state.vinte_g1} vittorie")
    st.write(f"**Io:** {st.session_state.vinte_g2} vittorie")

    if st.button("Reset Totale Torneo"):
        st.session_state.partite = []
        st.session_state.vinte_g1 = 0
        st.session_state.vinte_g2 = 0
        st.session_state.n_partita = 1
        st.rerun()

# --- CALCOLO PUNTEGGI ---
df = pd.DataFrame(st.session_state.partite)
if not df.empty:
    dati_attuale = df[df['Partita'] == st.session_state.n_partita]
    tot_g1 = dati_attuale['Punti Bababui'].sum()
    tot_g2 = dati_attuale['Punti Io'].sum()
else:
    tot_g1, tot_g2 = 0, 0

# --- INTERFACCIA PRINCIPALE ---
st.title(f"🃏 Partita Corrente: #{st.session_state.n_partita}")

col1, col2 = st.columns(2)
col1.metric("Punti Bababui", f"{tot_g1}")
col2.metric("Punti Io", f"{tot_g2}")

st.divider()

# --- LOGICA VITTORIA ---
vinto = False
if tot_g1 >= soglia or tot_g2 >= soglia:
    vincitore = "Bababui" if tot_g1 >= soglia else "Io"
    st.balloons()
    st.success(f"🎉 {vincitore.upper()} HA VINTO LA PARTITA!")
    vinto = True

    if st.button("🏁 SALVA E INIZIA NUOVA PARTITA"):
        if vincitore == "Bababui":
            st.session_state.vinte_g1 += 1
        else:
            st.session_state.vinte_g2 += 1
        st.session_state.n_partita += 1
        st.rerun()

# --- INSERIMENTO PUNTI ---
if not vinto:
    st.subheader("📝 Registra Nuova Mano")
    with st.form("form_mano", clear_on_submit=True):
        c1, c2 = st.columns(2)
        p1 = c1.number_input("Punti Bababui", value=0, step=1)
        p2 = c2.number_input("Punti Io", value=0, step=1)
        if st.form_submit_button("Aggiungi Mano"):
            nuova_mano = {
                "Partita": st.session_state.n_partita,
                "Mano": len(df[df['Partita'] == st.session_state.n_partita]) + 1 if not df.empty else 1,
                "Punti Bababui": p1,
                "Punti Io": p2
            }
            st.session_state.partite.append(nuova_mano)
            st.rerun()

# --- STORICO ---
if not df.empty:
    st.subheader("📜 Storico della partita")
    st.dataframe(df[df['Partita'] == st.session_state.n_partita], use_container_width=True)