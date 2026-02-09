import streamlit as st
import pandas as pd
import requests
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr", layout="wide")

# --- SCUDO TOTALE ANTI-APPANNAMENTO ---
st.markdown("""
    <style>
    /* Rende tutto opaco e stabile */
    [data-stale="true"], div[data-fragment-id], [data-testid="stAppViewBlockContainer"] > div {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    /* Nasconde caricamento */
    [data-testid="stStatusWidget"] { display: none !important; }
    * { transition: none !important; animation: none !important; }
    </style>
    """, unsafe_allow_html=True)

# !!! IL TUO URL DI GOOGLE APPS SCRIPT !!!
API_URL = "https://script.google.com/macros/s/AKfycbw3YLweEqP1AxW912TUcMbBDRKv655VEAdWwG3Etxwrw-L2TG110kPFVaupyXy0j10VRA/exec"

def get_data():
    try:
        r = requests.get(API_URL)
        df_raw = pd.DataFrame(r.json())
        if not df_raw.empty:
            for col in ['partita', 'mano', 'p1', 'p2']:
                if col in df_raw.columns:
                    df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0).astype(int)
        return df_raw
    except:
        return pd.DataFrame(columns=["partita", "mano", "p1", "p2", "chi"])

# --- CARICAMENTO INIZIALE ---
df_init = get_data()
soglia_default = 1500
if not df_init.empty and 'chi' in df_init.columns:
    c_rows = df_init[df_init['chi'] == 'CONFIG']
    if not c_rows.empty:
        soglia_default = int(c_rows.iloc[-1]['partita'])

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    soglia_scelta = st.number_input("Soglia Vittoria", value=soglia_default, step=100)
    if st.button("💾 Salva Soglia"):
        requests.post(API_URL, json={"action": "set_soglia", "valore": int(soglia_scelta)})
        st.success("Soglia Salvata!")
        time.sleep(1)
        st.rerun()
    st.divider()
    if st.button("🗑️ Reset Partite"):
        requests.post(API_URL, json={"action": "reset"})
        st.rerun()

st.title("🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr")

# --- DASHBOARD TEMPO REALE ---
@st.fragment(run_every="2s") 
def live_dashboard(s_val):
    data = get_data()
    df_p = data[data['chi'] != 'CONFIG'] if not data.empty else data
    
    v_makka, v_omo, n_p, t1, t2 = 0, 0, 1, 0, 0
    
    if not df_p.empty:
        # Calcolo Medagliere (aggiornato con la nuova logica di vittoria è complesso, 
        # qui manteniamo il conteggio semplice basato su chi supera la soglia per lo storico,
        # ma per la partita corrente usiamo la logica avanzata sotto)
        partite = df_p.groupby('partita').agg({'p1':'sum', 'p2':'sum'})
        
        # Logica medagliere approssimata (conta vittoria se uno supera soglia e l'altro no, o se supera ed è maggiore)
        v_makka = ((partite['p1'] >= s_val) & (partite['p1'] > partite['p2'])).sum()
        v_omo = ((partite['p2'] >= s_val) & (partite['p2'] > partite['p1'])).sum()
        
        n_p = int(df_p['partita'].max())
        curr = df_p[df_p['partita'] == n_p]
        t1, t2 = curr['p1'].sum(), curr['p2'].sum()

    m1, m2 = st.columns(2)
    m1.subheader(f"🏆 Makka Pakka: {v_makka}")
    m2.subheader(f"🏆 Omo Cratolo: {v_omo}")
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("PUNTI MAKKA PAKKA", int(t1))
    c2.metric("PUNTI OMO CRATOLO", int(t2))
    
    st.divider()
    st.subheader("📜 Storico Partita Corrente")
    disp = df_p[(df_p['partita'] == n_p) & (df_p['chi'] != 'START')] if not df_p.empty else pd.DataFrame()
    if not disp.empty:
        st.table(disp.rename(columns={'p1':'Punti M.P.', 'p2':'Punti O.C.', 'chi':'Chi'}).sort_values(by="mano", ascending=False))
    
    return n_p, t1, t2

# Esecuzione Dashboard
n_partita, tot1, tot2 = live_dashboard(soglia_scelta)

# --- LOGICA VITTORIA AVANZATA ---
# La partita continua se:
# 1. Nessuno ha raggiunto la soglia.
# 2. OPPURE i punteggi sono PARI (anche se sopra la soglia).
partita_in_corso = (tot1 < soglia_scelta and tot2 < soglia_scelta) or (tot1 == tot2)

if partita_in_corso:
    st.write("---")
    
    # Avviso speciale se siamo in pareggio oltre la soglia
    if tot1 >= soglia_scelta and tot2 >= soglia_scelta and tot1 == tot2:
        st.warning(f"⚠️ PAREGGIO OLTRE LA SOGLIA ({tot1} a {tot2})! Si continua finché uno non supera l'altro!")

    st.subheader("📝 Registra Mano")
    with st.form("form_mano", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        v1 = col1.number_input("Punti Makka Pakka", value=None, placeholder="-30, 50...", step=5, min_value=-5000)
        v2 = col2.number_input("Punti Omo Cratolo", value=None, placeholder="-30, 50...", step=5, min_value=-5000)
        chi_chiude = col3.selectbox("Chi ha chiuso?", ["Nessuno", "Makka Pakka", "Omo Cratolo"])
        
        if st.form_submit_button("REGISTRA"):
            temp_df = get_data()
            mani_partita = temp_df[(temp_df['partita'] == n_partita) & (temp_df['chi'] != 'START')]
            numero_mano_reale = len(mani_partita) + 1

            requests.post(API_URL, json={
                "action": "add", 
                "partita": n_partita, 
                "mano": numero_mano_reale, 
                "p1": v1 if v1 is not None else 0, 
                "p2": v2 if v2 is not None else 0, 
                "chi": chi_chiude
            })
            st.rerun()
else:
    # SE SIAMO QUI, QUALCUNO HA VINTO (Soglia superata E punteggi diversi)
    st.balloons()
    
    # Calcolo vincitore basato sul punteggio più alto
    vincitore = "Makka Pakka" if tot1 > tot2 else "Omo Cratolo"
    differenza = abs(tot1 - tot2)
    
    st.success(f"🏆 {vincitore.upper()} HA VINTO LA PARTITA DI {differenza} PUNTI!")
    st.write(f"Punteggio finale: {tot1} vs {tot2}")
    
    if st.button("🏁 Inizia Nuova Partita"):
        requests.post(API_URL, json={"action": "add", "partita": n_partita + 1, "mano": 0, "p1": 0, "p2": 0, "chi": "START"})
        st.rerun()
