import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr", layout="wide")

# CSS ANTI-APPANNAMENTO
st.markdown("""
    <style>
    [data-stale="true"], div[data-fragment-id], [data-testid="stAppViewBlockContainer"] > div {
        opacity: 1 !important; filter: none !important; transition: none !important;
    }
    [data-testid="stStatusWidget"] { display: none !important; }
    * { transition: none !important; animation: none !important; }
    </style>
    """, unsafe_allow_html=True)

# !!! INCOLLA IL NUOVO LINK APPS SCRIPT !!!
API_URL = "https://script.google.com/macros/s/AKfycbw3YLweEqP1AxW912TUcMbBDRKv655VEAdWwG3Etxwrw-L2TG110kPFVaupyXy0j10VRA/exec"

def get_data():
    cols = ["partita", "mano", "p1", "p2", "p3", "chi"]
    try:
        r = requests.get(API_URL)
        data = r.json()
        if not data: return pd.DataFrame(columns=cols)
        df_raw = pd.DataFrame(data)
        for c in cols:
            if c not in df_raw.columns: df_raw[c] = 0 if c != 'chi' else ""
        for col in ['partita', 'mano', 'p1', 'p2', 'p3']:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0).astype(int)
        return df_raw
    except:
        return pd.DataFrame(columns=cols)

# --- CARICAMENTO INIZIALE ---
df_init = get_data()
soglia_default = 1500
if not df_init.empty:
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
    if st.button("🗑️ Reset Totale"):
        requests.post(API_URL, json={"action": "reset"})
        st.rerun()

st.title("🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr")

# --- DASHBOARD (2 GIOCATORI) ---
@st.fragment(run_every="2s") 
def live_dashboard(s_val):
    data = get_data()
    df_p = data[~data['chi'].isin(['CONFIG', 'WIN_MAKKA', 'WIN_OMO'])] if not data.empty else data
    
    v_makka = len(data[data['chi'] == 'WIN_MAKKA']) if not data.empty else 0
    v_omo = len(data[data['chi'] == 'WIN_OMO']) if not data.empty else 0
    
    n_p, t1, t2 = 1, 0, 0
    if not df_p.empty:
        n_p = int(df_p['partita'].max())
        curr = df_p[df_p['partita'] == n_p]
        t1, t2 = curr['p1'].sum(), curr['p2'].sum()

    m1, m2 = st.columns(2)
    m1.subheader(f"🏆 Makka Pakka: {v_makka}")
    m2.subheader(f"🏆 Omo Cratolo: {v_omo}")
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("MAKKA PAKKA", int(t1))
    c2.metric("OMO CRATOLO", int(t2))
    
    st.divider()
    st.subheader("📜 Storico Partita")
    if not df_p.empty:
        disp = df_p[(df_p['partita'] == n_p) & (~df_p['chi'].isin(['START']))].sort_values(by="mano", ascending=False)
        st.table(disp[['partita', 'mano', 'p1', 'p2', 'chi']].rename(columns={'partita':'Partita','mano':'Mano','p1':'Makka P.','p2':'Omo C.','chi':'Chi ha chiuso'}))
    return n_p, t1, t2

n_partita, tot1, tot2 = live_dashboard(soglia_scelta)

# --- INSERIMENTO (SENZA FORM PER FIX BUG) ---
game_over = False
if tot1 >= soglia_scelta or tot2 >= soglia_scelta:
    if tot1 != tot2: game_over = True
    else: st.warning(f"⚠️ PAREGGIO ({tot1})! Si continua.")

if not game_over:
    st.write("---")
    st.subheader("📝 Registra Mano")
    
    # Inizializza session state per i campi se non esistono
    if "val_p1" not in st.session_state: st.session_state.val_p1 = None
    if "val_p2" not in st.session_state: st.session_state.val_p2 = None
    if "val_chi" not in st.session_state: st.session_state.val_chi = "Nessuno"

    col1, col2, col3 = st.columns(3)
    # Usiamo key per legare il valore allo stato. Niente st.form.
    val1 = col1.number_input("Punti Makka Pakka", value=None, placeholder="-30, 50...", step=5, key="input_p1")
    val2 = col2.number_input("Punti Omo Cratolo", value=None, placeholder="-30, 50...", step=5, key="input_p2")
    chi_chiude = col3.selectbox("Chi ha chiuso?", ["Nessuno", "Makka Pakka", "Omo Cratolo"], key="input_chi")
    
    # Bottone diretto: quando clicchi, Streamlit forza la lettura dei valori
    if st.button("REGISTRA MANO", type="primary"):
        # Calcolo numero mano
        temp_df = get_data()
        mani_partita = temp_df[(temp_df['partita'] == n_partita) & (~temp_df['chi'].isin(['START', 'WIN_MAKKA', 'WIN_OMO', 'CONFIG']))]
        nuova_mano = len(mani_partita) + 1
        
        requests.post(API_URL, json={
            "action": "add", "partita": n_partita, "mano": nuova_mano,
            "p1": val1 if val1 else 0, "p2": val2 if val2 else 0, "p3": 0, "chi": chi_chiude
        })
        # Reset manuale dei campi non necessario col reload, ma st.rerun pulisce tutto
        st.rerun()

else:
    st.balloons()
    vincitore = "Makka Pakka" if tot1 > tot2 else "Omo Cratolo"
    win_code = "WIN_MAKKA" if tot1 > tot2 else "WIN_OMO"
    st.success(f"🏆 {vincitore.upper()} HA VINTO!")
    if st.button("🏁 SALVA E NUOVA PARTITA"):
        requests.post(API_URL, json={"action": "add", "partita": n_partita, "mano": 999, "p1":0,"p2":0,"p3":0, "chi": win_code})
        requests.post(API_URL, json={"action": "add", "partita": n_partita + 1, "mano": 0, "p1":0,"p2":0,"p3":0, "chi": "START"})
        st.rerun()
