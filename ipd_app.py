import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
from fpdf import FPDF
import os

# --- STYLE NAVY & LIGHT BLUE ---
st.set_page_config(page_title="IPD PHOENIX MASTER", layout="wide", page_icon="🦅")

st.markdown(f"""
    <style>
    .main {{ background-color: #050a14; color: white; }}
    [data-testid="stMetricValue"] {{ color: #1565C0; font-family: 'Helvetica', sans-serif; font-weight: bold; }}
    .stButton>button {{ border: 1px solid #1565C0; background-color: #0B3D91; color: white; border-radius: 4px; font-weight: bold; width: 100%; height: 3em; }}
    .stButton>button:hover {{ background-color: #1565C0; box-shadow: 0 0 10px #1565C0; color: white; }}
    .trello-card {{ background: white; color: #1a1c24; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 8px solid #1565C0; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); }}
    .trello-header {{ color: #1565C0; font-weight: bold; border-bottom: 2px solid #1565C0; padding-bottom: 5px; text-transform: uppercase; margin-bottom: 15px; }}
    .cfo-panel {{ background: #0B3D91; padding: 20px; border-radius: 8px; border: 1px solid #1565C0; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('ipd_ultimate_v2.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS campaigns (id INTEGER PRIMARY KEY, name TEXT, target_margin REAL, goal INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, campaign TEXT, client TEXT, seller TEXT, margin REAL, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT, owner TEXT, deadline TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS meetings (id INTEGER PRIMARY KEY, title TEXT, date TEXT, participants TEXT, decisions TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, timestamp TEXT, action TEXT)')
    conn.commit()
    conn.close()

def add_log(action):
    conn = sqlite3.connect('ipd_ultimate_v2.db')
    conn.execute("INSERT INTO logs (timestamp, action) VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action))
    conn.commit()
    conn.close()

init_db()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("roa_logo.jpg"):
        st.image("roa_logo.jpg", use_container_width=True)
    st.markdown("<h2 style='text-align:center; color:#1565C0;'>IPD PHOENIX</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:0.8rem;'>RISE OF AFRICA</p>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("PILOTAGE", ["DASHBOARD", "CAMPAGNES", "VENTES & BONUS", "KANBAN MISSIONS", "GOUVERNANCE", "AUDIT"])

# --- 1. DASHBOARD ---
if menu == "DASHBOARD":
    st.title("📊 Dashboard Stratégique")
    conn = sqlite3.connect('ipd_ultimate_v2.db')
    df_s = pd.read_sql_query("SELECT * FROM sales WHERE status='Payé'", conn)
    conn.close()

    if not df_s.empty:
        total = df_s['margin'].sum()
        st.markdown('<div class="cfo-panel">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CASH ENCAISSÉ", f"{total:,.0f} $")
        c2.metric("RENAISSANCE (40%)", f"{total*0.4:,.0f} $")
        c3.metric("POOL ÉQUIPE (40%)", f"{total*0.4:,.0f} $")
        c4.metric("MARKETING (20%)", f"{total*0.2:,.0f} $")
        st.markdown('</div>', unsafe_allow_html=True)
        
        fig = px.area(df_s, x='date', y='margin', title="Courbe de la Remontada", color_discrete_sequence=['#1565C0'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée encaissée. Configurez une campagne et enregistrez des ventes payées.")

# --- 2. CAMPAGNES ---
elif menu == "CAMPAGNES":
    st.title("🎯 Objectifs & Suivi Campagnes")
    with st.form("c_form"):
        name = st.text_input("Nom de la campagne (ex: Solaire pour tous)")
        t_marg = st.number_input("Marge cible par kit ($)", min_value=0, value=1400)
        goal = st.number_input("Objectif Total (ex: 300)", min_value=1)
        if st.form_submit_button("LANCER LA CAMPAGNE"):
            conn = sqlite3.connect('ipd_ultimate_v2.db')
            conn.execute("INSERT INTO campaigns (name, target_margin, goal) VALUES (?,?,?)", (name, t_marg, goal))
            conn.commit()
            conn.close()
            add_log(f"Campagne créée : {name}")
            st.success(f"Campagne {name} enregistrée avec succès.")

# --- 3. VENTES & RÈGLE CLOVIS ---
elif menu == "VENTES & BONUS":
    st.title("💰 Ventes & Commissions (Règle 50/30/20)")
    conn = sqlite3.connect('ipd_ultimate_v2.db')
    camps = [r[0] for r in conn.execute("SELECT name FROM campaigns").fetchall()]
    conn.close()

    with st.expander("Saisir une transaction"):
        if not camps:
            st.warning("Veuillez d'abord créer une campagne.")
        else:
            with st.form("s_form"):
                cp = st.selectbox("Campagne", camps)
                cl = st.text_input("Client")
                sl = st.text_input("Vendeur Chasseur (ex: Clovis)")
                ma = st.number_input("Marge réelle conclue ($)", min_value=0, value=1400)
                stt = st.selectbox("Statut", ["Payé", "En attente"])
                if st.form_submit_button("VALIDER TRANSACTION"):
                    conn = sqlite3.connect('ipd_ultimate_v2.db')
                    conn.execute("INSERT INTO sales (campaign, client, seller, margin, status, date) VALUES (?,?,?,?,?,?)",
                                 (cp, cl, sl, ma, stt, date.today().isoformat()))
                    conn.commit()
                    conn.close()
                    add_log(f"Vente : {cl} par {sl}")
                    st.balloons()

    conn = sqlite3.connect('ipd_ultimate_v2.db')
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()
    if not df.empty:
        # Calculs selon ta règle 40% (Pool) -> 50/30/20
        df['Pool_Total_40%'] = df['margin'] * 0.40
        df['Clovis_Chasseur_(50%)'] = df['Pool_Total_40%'] * 0.50
        df['Pool_Equipe_(30%)'] = df['Pool_Total_40%'] * 0.30
        df['Structure_(20%)'] = df['Pool_Total_40%'] * 0.20
        st.write("### Suivi des Commissions")
        st.dataframe(df, use_container_width=True)

# --- 4. KANBAN ---
elif menu == "KANBAN MISSIONS":
    st.title("📋 Kanban des Opérations")
    with st.sidebar:
        st.markdown("### Nouvelle Mission")
        tn = st.text_input("Tâche")
        to = st.selectbox("Responsable", ["Clovis", "Moriah", "Pôle Énergie", "Construction"])
        ts = st.selectbox("Statut", ["À FAIRE", "EN COURS", "TERMINÉ"])
        if st.button("AJOUTER AU KANBAN"):
            conn = sqlite3.connect('ipd_ultimate_v2.db')
            conn.execute("INSERT INTO tasks (task, owner, deadline, status) VALUES (?,?,?,?)", (tn, to, str(date.today()), ts))
            conn.commit()
            conn.close()

    conn = sqlite3.connect('ipd_ultimate_v2.db')
    tk = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    
    c1, c2, c3 = st.columns(3)
    status_list = [("À FAIRE", "#1565C0", c1), ("EN COURS", "#FF8C00", c2), ("TERMINÉ", "#228B22", c3)]
    
    for status, color, column in status_list:
        with column:
            st.markdown(f'<div class="trello-header">{status}</div>', unsafe_allow_html=True)
            for _, r in tk[tk['status'] == status].iterrows():
                st.markdown(f'<div class="trello-card" style="border-left-color:{color}"><b>{r["task"]}</b><br><small>Responsable : {r["owner"]}</small></div>', unsafe_allow_html=True)

# --- 5. GOUVERNANCE ---
elif menu == "GOUVERNANCE":
    st.title("🤝 Gouvernance & CR PDF")
    with st.form("m_f"):
        subj = st.text_input("Sujet de la Réunion")
        decs = st.text_area("Décisions & Actions à mener")
        if st.form_submit_button("GÉNÉRER LE CR PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="I&P DEVELOPMENT - COMPTE-RENDU", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.multi_cell(0, 10, txt=f"Date: {date.today()}\nSujet: {subj}\n\nDécisions et Actions :\n{decs}")
            st.download_button("📥 Télécharger le CR", data=pdf.output(dest='S').encode('latin-1'), file_name=f"CR_IPD_{date.today()}.pdf")

# --- 6. AUDIT ---
elif menu == "AUDIT":
    st.title("🛡️ Audit Log (Traçabilité)")
    conn = sqlite3.connect('ipd_ultimate_v2.db')
    st.table(pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn))
    conn.close()