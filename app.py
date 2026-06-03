import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. Page & Layout Config (Mobile Friendly)
st.set_page_config(page_title="Sanduuqa Wargale", page_icon="💰", layout="centered")

# --- LOGIN APP ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 Sanduuqa Wargale</h2>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Gal Nidaamka", use_container_width=True):
        if username == "admin" and password == "wargale2026": # Password-kaaga halkaan ka bedelo
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Username ama Password waa khalad!")
    st.stop()

# --- XIRIIRKA GOOGLE DRIVE (SHEETS) ---
# Nidaamku wuxuu si toos ah u xiriirayaa Google Sheet-ka loo fasaxay
conn = st.connection("gsheets", type=GSheetsConnection)

# Soo akhrinta xogta hadda jirta
try:
    df_members = conn.read(worksheet="Members", ttl=0)
except Exception:
    df_members = pd.DataFrame(columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])

try:
    df_tx = conn.read(worksheet="Transactions", ttl=0)
except Exception:
    df_tx = pd.DataFrame(columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])


# --- NAVIGATION MENU ---
menu = st.radio("MENU:", ["📊 Dashboard", "📝 Add Member", "💵 Gali Lacag", "📋 Liiska & WhatsApp"], horizontal=True)

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>Sanduuqa Wargale</h3>", unsafe_allow_html=True)
    
    total_members = len(df_members)
    
    # Xisaabinta lacagaha horta la hubiyo haddii xog jirto
    if not df_tx.empty and 'Type' in df_tx.columns and 'Amount' in df_tx.columns:
        # Hubi in column-ka Amount uu yahay nambar
        df_tx['Amount'] = pd.to_numeric(df_tx['Amount'], errors='coerce').fillna(0)
        total_deposit = df_tx[df_tx['Type'] == 'Deposit']['Amount'].sum()
        total_expense = df_tx[df_tx['Type'] == 'Expense']['Amount'].sum()
    else:
        total_deposit = 0
        total_expense = 0
        
    current_balance = total_deposit - total_expense

    # Muuqaalka Dashboard-ka ee Mobile-ka
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
                new_id = int(df_members['ID'].max()) + 1 if not df_members.empty else 1
                
                # Diyaarinta xogta cusub
                new_row = pd.DataFrame([[new_id, full_name, degmo, xaafad, tel]], columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])
                df_members = pd.concat([df_members, new_row], ignore_index=True)
                
                # Toos ugu qor Google Sheet-ka ku jira Drive-ka
                conn.update(worksheet="Members", data=df_members)
                st.success(f"Si guul leh ayaa loo kaydiyay: {full_name}")
            else:
                st.error("Fadlan Magaca iyo Telefoonka waa muhiim!")

# --- 3. GALI LACAG (DEPOSIT / EXPENSE & HISTORICAL DATA) ---
elif menu == "💵 Gali Lacag":
    st.subheader("Diiwaangali Lacag (Hore ama Hada)")
    if df_members.empty:
        st.warning("Fadlan marka hore xubin diiwaangali si aad lacag ugu qorto!")
    else:
        with st.form("money_form", clear_on_submit=True):
            member_choice = st.selectbox("Dooro Xubinta Tolka", df_members['Magaca'].tolist())
            nooca = st.radio("Nooca Lacagta", ["Deposit", "Expense"], horizontal=True)
            lacag = st.number_input("Cadadka Lacagta ($)", min_value=0.0, step=1.0)
            
            # Manual Date Entry ee xogta sanadihii hore
            date_hore = st.date_input("Taariikhda (Si manual ah u dooro haday hore tahay)", datetime.now())
            faahfaahin = st.text_input("Note (Ex: Qaaraanka 2024, Furitaan xafiis)")
            
            if st.form_submit_button("Xaqiiji & Kaydi", use_container_width=True):
                if lacag > 0:
                    m_id = df_members[df_members['Magaca'] == member_choice]['ID'].values[0]
                    
                    # Diyaarinta xogta lacagta
                    new_tx_row = pd.DataFrame([[str(date_hore), int(m_id), nooca, lacag, faahfaahin]], columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
                    df_tx = pd.concat([df_tx, new_tx_row], ignore_index=True)
                    
                    # Toos ugu qor Google Sheet-ka ku jira Drive-ka
                    conn.update(worksheet="Transactions", data=df_tx)
                    st.success(f"Waxaa Drive-ka lagu xareeyay ${lacag} oo {nooca} ah!")
                else:
                    st.error("Cadadka lacagta waa inuu ka weyn yahay 0!")

# --- 4. LIISKA & MAAMULKA (DELETE & WHATSAPP) ---
elif menu == "📋 Liiska & WhatsApp":
    st.subheader("Maamulka Tolka & Xusuusinta")
    if df_members.empty:
        st.info("Liisku waa maran yahay hadda.")
    else:
        for idx, row in df_members.iterrows():
            with st.expander(f"👤 {row['Magaca']}"):
                st.write(f"📍 Degmada: {row['Degmada']} | Xaafada: {row['Xaafada']}")
                st.write(f"📞 Tel: {row['Telefoonka']}")
                
                # 1. WhatsApp Automated Message
                msg = f"Asc {row['Magaca']}, nidaamka Sanduuqa Wargale wuxuu kuu xasuusinayaa qaaraanka bilaha ah ee dib ula soo dhacday. Fadlan ku soo shub xisaabta sanduuqa. Mahadsanid."
                url = f"https://wa.me/{row['Telefoonka']}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[📢 Soo dir Xusuusin WhatsApp]({url})")
                
                st.write("---")
                # 2. Toos uga tirtir Google Drive-ka (Delete Button)
                if st.button(f"Masax Xubintaan ❌", key=f"del_{row['ID']}"):
                    df_members = df_members[df_members['ID'] != row['ID']]
                    # Haddii uu lacag lahaa na xiriirkeeda waa la goyn karaa (ikhiyaari)
                    conn.update(worksheet="Members", data=df_members)
                    st.success(f"Waa laga tirtiray Drive-ka!")
                    st.rerun()
