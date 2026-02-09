import streamlit as st
import pandas as pd
import requests
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr", layout="wide")

# --- SCUDO TOTALE ANTI-APPANNAMENTO ---
st.markdown("""
    <style>
    [data-stale="true"], div[data-fragment-id], [data-testid="stAppViewBlockContainer"] > div {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    [data-testid="stStatusWidget"] { display: none !important; }
    * { transition: none !important; animation: none !important; }
    </style>
    """, unsafe_allow_html=True)

# !!! IL TUO URL DI GOOGLE APPS SCRIPT !!!
API_URL = "https://script.google.com/macros/s/AKfycbw3YLweEqP1AxW912TUcMbBDRKv655VEAdWwG3Etxwrw-L2TG110kPFVaupyXy0j10VRA/exec"

# --- FUNZIONE GET_DATA ---
def get_data():
    cols = ["partita", "mano", "p1", "p2", "chi"]
    try:
        r = requests.get(API_URL)
        data = r.json()
        if not data: return pd.DataFrame(columns=cols)
        df_raw = pd.DataFrame(data)
        if "partita" not in df_raw.columns: return pd.DataFrame(columns=cols)
        # Conversione numerica
        for col in ['partita', 'mano', 'p1', 'p2']:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0).astype(int)
        return df_raw
    except:
        return pd.DataFrame(columns=cols)

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
    if st.button("🗑️ Reset Totale Torneo"):
        requests.post(API_URL, json={"action": "reset"})
        st.rerun()

st.title("🃏 Pppprrrrrrrrrrrrrrrrrrrrrrrrr")

# --- DASHBOARD TEMPO REALE ---
@st.fragment(run_every="2s") 
def live_dashboard(s_val):
    data = get_data()
    # Escludiamo righe speciali dai calcoli
    df_p = data[~data['chi'].isin(['CONFIG', 'WIN_MAKKA', 'WIN_OMO'])] if not data.empty else data
    
    v_makka, v_omo, n_p, t1, t2 = 0, 0, 1, 0, 0
    
    if not data.empty:
        # Conta le vittorie TIMBRATE nel database
        v_makka = len(data[data['chi'] == 'WIN_MAKKA'])
        v_omo = len(data[data['chi'] == 'WIN_OMO'])
        
        # Calcolo partita corrente
        if not df_p.empty:
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
    
    if not df_p.empty:
        # Filtriamo solo la partita attuale e togliamo lo START
        disp = df_p[(df_p['partita'] == n_p) & (~df_p['chi'].isin(['START']))] 
        
        if not disp.empty:
            # Ordiniamo PRIMA di rinominare
            disp = disp.sort_values(by="mano", ascending=False)
            
            # RINOMINIAMO LE COLONNE COME HAI CHIESTO
            disp = disp.rename(columns={
                'partita': 'Partita N.',
                'mano': 'Mano N.',
                'p1': 'Punti Makka Pakka',
                'p2': 'Punti Omo Cratolo',
                'chi': 'Chi ha chiuso'
            })
            
            # Mostriamo la tabella pulita senza l'indice numerico a sinistra (hide_index=True è supportato da st.dataframe, per st.table è automatico o si usa un trick, qui st.table va bene)
            st.table(disp)
    
    return n_p, t1, t2

# Esecuzione Dashboard
n_partita, tot1, tot2 = live_dashboard(soglia_scelta)

# --- LOGICA DI GIOCO ---
game_over = False

if tot1 >= soglia_scelta or tot2 >= soglia_scelta:
    if tot1 != tot2:
        game_over = True
    else:
        st.warning(f"⚠️ PAREGGIO OLTRE SOGLIA ({tot1} pari)! Si continua.")

if not game_over:
    st.write("---")
    st.subheader("📝 Registra Mano")
    with st.form("form_mano", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        v1 = col1.number_input("Punti Makka Pakka", value=None, placeholder="-30, 50...", step=5, min_value=-5000)
        v2 = col2.number_input("Punti Omo Cratolo", value=None, placeholder="-30, 50...", step=5, min_value=-5000)
        chi_chiude = col3.selectbox("Chi ha chiuso?", ["Nessuno", "Makka Pakka", "Omo Cratolo"])
        
        if st.form_submit_button("REGISTRA"):
            temp_df = get_data()
            if 'partita' in temp_df.columns:
                # Contiamo le mani reali per avere il numero progressivo 1, 2, 3...
                mani_partita = temp_df[(temp_df['partita'] == n_partita) & (~temp_df['chi'].isin(['START', 'WIN_MAKKA', 'WIN_OMO', 'CONFIG']))]
                numero_mano_reale = len(mani_partita) + 1
            else:
                numero_mano_reale = 1

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
    # PARTITA FINITA
    st.balloons()
    vincitore_nome = "Makka Pakka" if tot1 > tot2 else "Omo Cratolo"
    win_code = "WIN_MAKKA" if tot1 > tot2 else "WIN_OMO"
    
    st.success(f"🏆 {vincitore_nome.upper()} HA VINTO!")
    st.metric("Punteggio Finale", f"{tot1} - {tot2}")
    
    if st.button("🏁 SALVA VITTORIA E INIZIA NUOVA PARTITA"):
        # 1. Salva vittoria
        requests.post(API_URL, json={"action": "add", "partita": n_partita, "mano": 999, "p1": 0, "p2": 0, "chi": win_code})
        # 2. Nuova partita
        requests.post(API_URL, json={"action": "add", "partita": n_partita + 1, "mano": 0, "p1": 0, "p2": 0, "chi": "START"})
        st.rerun()
