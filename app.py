import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
from streamlit_gsheets import GSheetsConnection

# 1. Page & Layout Config
st.set_page_config(page_title="Sanduuqa Wargale", page_icon="💰", layout="centered")

# --- LOGIN APP ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 Sanduuqa Wargale</h2>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Gal Nidaamka", use_container_width=True):
        if username == "admin" and password == "wargale2026":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Username ama Password waa khalad!")
    st.stop()

# --- INITIALIZE VARIABLES ---
connection_success = False

# --- NEW FRESH GSHEETS CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Soo akhrinta xaashiyaha cusub
    df_members = conn.read(worksheet="Members", ttl=0)
    df_tx = conn.read(worksheet="Transactions", ttl=0)
    
    # Sifaynta khadadka eberka ah
    df_members = df_members.dropna(how="all")
    df_tx = df_tx.dropna(how="all")
    
    # Hubinta tiirarka haddii uu sheet-ku cusub yahay oo madhan yahay
    if df_members.empty or 'ID' not in df_members.columns:
        df_members = pd.DataFrame(columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])
    if df_tx.empty or 'Amount' not in df_tx.columns:
        df_tx = pd.DataFrame(columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
        
    connection_success = True
except Exception as e:
    st.error("⚠️ Cilad dhanka isku xirka Google Sheets ah: Fadlan hubi Secrets-ka ama in Email-ka robot-ka uu Editor ka yahay Sheet-ka cusub.")
    df_members = pd.DataFrame(columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])
    df_tx = pd.DataFrame(columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
    connection_success = False

# --- NAVIGATION MENU ---
menu = st.radio("MENU:", ["📊 Dashboard", "📝 Add Member", "💵 Gali Lacag", "📋 Liiska & WhatsApp"], horizontal=True)

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>Sanduuqa Wargale</h3>", unsafe_allow_html=True)
    
    total_members = len(df_members)
    
    if not df_tx.empty and 'Amount' in df_tx.columns:
        df_tx['Amount'] = pd.to_numeric(df_tx['Amount'], errors='coerce').fillna(0)
        total_deposit = df_tx[df_tx['Type'] == 'Deposit']['Amount'].sum()
        total_expense = df_tx[df_tx['Type'] == 'Expense']['Amount'].sum()
    else:
        total_deposit = 0
        total_expense = 0
        
    current_balance = total_deposit - total_expense

    st.metric(label="👥 Wadarta Tolka Diiwāngashan", value=f"{total_members} Qof")
    st.metric(label="📥 Total Deposit (Lacagta Gashto)", value=f"${total_deposit:,.2f}", delta="Guud ahaan")
    st.metric(label="📤 Total Expense (Lacagta Baxday)", value=f"${total_expense:,.2f}", delta="- Kharash", delta_color="inverse")
    st.markdown("---")
    st.metric(label="💰 LACAGTA SANDUUQA KU JIRTA (HADA)", value=f"${current_balance:,.2f}")

# --- 2. ADD MEMBER ---
elif menu == "📝 Add Member":
    st.subheader("Diiwaangali Xubin Cusub")
    with st.form("add_form", clear_on_submit=True):
        m_1 = st.text_input("Magaca Koowaad")
        m_2 = st.text_input("Magaca Labaad")
        m_3 = st.text_input("Magaca Saddexaad")
        degmo = st.text_input("Dagmada")
        xaafad = st.text_input("Xaafada")
        tel = st.text_input("Telefonka (Ex: 25261xxxxxxx)")
        
        if st.form_submit_button("Badbaadi (Save to Drive)", use_container_width=True):
            if m_1 and tel:
                full_name = f"{m_1} {m_2} {m_3}".strip()
                
                if not df_members.empty and 'ID' in df_members.columns:
                    try:
                        new_id = int(pd.to_numeric(df_members['ID'], errors='coerce').max()) + 1
                    except:
                        new_id = len(df_members) + 1
                else:
                    new_id = 1
                
                if connection_success:
                    new_row = pd.DataFrame([[int(new_id), full_name, degmo, xaafad, str(tel)]], columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])
                    df_updated = pd.concat([df_members, new_row], ignore_index=True)
                    conn.update(worksheet="Members", data=df_updated)
                    st.success(f"Si guul leh ayaa loo kaydiyay: {full_name}")
                    st.rerun()
                else:
                    st.error("Xiriirka Google Sheet-ka ma jiro, dib u tijaabi.")
            else:
                st.error("Fadlan Magaca iyo Telefoonka waa muhiim!")

# --- 3. GALI LACAG ---
elif menu == "💵 Gali Lacag":
    st.subheader("Diiwaangali Lacag (Hore ama Hada)")
    if df_members.empty:
        st.warning("Fadlan marka hore xubin diiwaangali si aad lacag ugu qorto!")
    else:
        with st.form("money_form", clear_on_submit=True):
            member_choice = st.selectbox("Dooro Xubinta Tolka", df_members['Magaca'].tolist())
            nooca = st.radio("Nooca Lacagta", ["Deposit", "Expense"], horizontal=True)
            lacag = st.number_input("Cadadka Lacagta ($)", min_value=0.0, step=1.0)
            date_hore = st.date_input("Taariikhda (Manual)", datetime.now())
            faahfaahin = st.text_input("Note (Ex: Qaaraanka 2024)")
            
            if st.form_submit_button("Xaqiiji & Kaydi", use_container_width=True):
                if lacag > 0 and connection_success:
                    m_id = df_members[df_members['Magaca'] == member_choice]['ID'].values[0]
                    new_tx = pd.DataFrame([[str(date_hore), int(m_id), nooca, float(lacag), faahfaahin]], columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
                    df_tx_updated = pd.concat([df_tx, new_tx], ignore_index=True)
                    conn.update(worksheet="Transactions", data=df_tx_updated)
                    st.success(f"Waxaa la xareeyay ${lacag} oo {nooca} ah!")
                    st.rerun()

# --- 4. LIISKA & MAAMULKA ---
elif menu == "📋 Liiska & WhatsApp":
    st.subheader("Maamulka Tolka & Xusuusinta")
    if df_members.empty:
        st.info("Liisku waa maran yahay hadda.")
    else:
        for idx, row in df_members.iterrows():
            with st.expander(f"👤 {row['Magaca']}"):
                st.write(f"📍 Degmada: {row.get('Degmada', '')} | Xaafada: {row.get('Xaafada', '')}")
                st.write(f"📞 Tel: {row.get('Telefoonka', '')}")
                
                msg = f"Asc {row['Magaca']}, nidaamka Sanduuqa Wargale wuxuu kuu xasuusinayaa qaaraanka bilaha ah. Fadlan ku soo shub xisaabta sanduuqa. Mahadsanid."
                url = f"https://wa.me/{row.get('Telefoonka', '')}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[📢 Soo dir Xusuusin WhatsApp]({url})")
                
                st.write("---")
                if st.button(f"Masax Xubintaan ❌", key=f"del_{row.get('ID', idx)}"):
                    if connection_success:
                        df_members_updated = df_members[df_members['Magaca'] != row['Magaca']]
                        conn.update(worksheet="Members", data=df_members_updated)
                        st.success(f"Waa laga tirtiray Drive-ka!")
                        st.rerun()
