import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

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

# --- INITIALIZE VARIABLES TO PREVENT NAMEERROR ---
worksheet_members = None
worksheet_tx = None
connection_success = False

# --- XIRIIRKA GOOGLE SHEETS (VIA GSPREAD) ---
try:
    from google.oauth2.service_account import Credentials
    import gspread
    
    # Helitaanka ogolaanshaha Secrets-ka nidaamka
    creds_dict = st.secrets["gspread_credentials"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    # LINK-GAAGA RASMIGA AH EE SAXDA AH
    sheet_url = "https://docs.google.com/spreadsheets/d/1_hGit5rDff32GsFwMqFg21ZU-va8qI-4Dw4EejsjcDY/edit"
    sh = gc.open_by_url(sheet_url)
    
    worksheet_members = sh.worksheet("Members")
    worksheet_tx = sh.worksheet("Transactions")
    
    # Soo akhrinta xogta hadda jirta
    df_members = pd.DataFrame(worksheet_members.get_all_records())
    df_tx = pd.DataFrame(worksheet_tx.get_all_records())
    connection_success = True
except Exception as e:
    # Haddii xiriirku go'o, fariintaan guduudka ah kaliya ayaa muuqanaysa laakiin app-ku ma hakanayo
    st.error(f"⚠️ Cillad dhanka isku xirka Google Drive ah: Fadlan hubi Secrets-ka Streamlit ama in Email-ka robot-ka uu Editor ka yahay Sheet-ka.")
    
    # Nidaamku wuxuu samaysanayaa meel ku-meel-gaar ah oo xogta lagu hayo si uusan error u bixin
    if 'backup_members' not in st.session_state:
        st.session_state.backup_members = pd.DataFrame(columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])
    if 'backup_tx' not in st.session_state:
        st.session_state.backup_tx = pd.DataFrame(columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
        
    df_members = st.session_state.backup_members
    df_tx = st.session_state.backup_tx

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
                
                # Xisaabinta ID-ga cusub
                if not df_members.empty and 'ID' in df_members.columns:
                    try:
                        new_id = int(pd.to_numeric(df_members['ID'], errors='coerce').max()) + 1
                    except:
                        new_id = len(df_members) + 1
                else:
                    new_id = 1
                
                # Haddii Google Drive uu shaqaynayo, toos ugu qor Sheet-ka
                if connection_success and worksheet_members is not None:
                    try:
                        worksheet_members.append_row([int(new_id), full_name, degmo, xaafad, str(tel)])
                        st.success(f"Si guul leh ayaa loogu kaydiyay Google Sheet-ka: {full_name}")
                    except Exception as e:
                        st.error(f"⚠️ Koodhku wuu xiriiray laakiin wuxuu ku guuldareystay inuu wax u qoro Sheet-ka.")
                else:
                    # Haddii kale, ku kaydi xogta ku-meel-gaarka ah si uusan nidaamku u jabin
                    new_row = pd.DataFrame([[int(new_id), full_name, degmo, xaafad, str(tel)]], columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka'])
                    st.session_state.backup_members = pd.concat([st.session_state.backup_members, new_row], ignore_index=True)
                    st.success(f"Si ku-meel-gaar ah ayaa loogu kaydiyay nidaamka (Laakiin kuma kaydsan Google Drive): {full_name}")
                
                st.rerun()
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
                if lacag > 0:
                    m_id = df_members[df_members['Magaca'] == member_choice]['ID'].values[0]
                    
                    if connection_success and worksheet_tx is not None:
                        try:
                            worksheet_tx.append_row([str(date_hore), int(m_id), nooca, float(lacag), faahfaahin])
                            st.success(f"Waxaa la xareeyay ${lacag} oo {nooca} ah!")
                        except:
                            st.error("Cillad ayaa dhacday markii loo qorayay Google Sheet-ka.")
                    else:
                        new_tx_row = pd.DataFrame([[str(date_hore), int(m_id), nooca, float(lacag), faahfaahin]], columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
                        st.session_state.backup_tx = pd.concat([st.session_state.backup_tx, new_tx_row], ignore_index=True)
                        st.success(f"Si ku-meel-gaar ah ayaa lacagta loogu xareeyay nidaamka!")
                    st.rerun()

# --- 4. LIISKA & MAAMULKA ---
elif menu == "📋 Liiska & WhatsApp":
    st.subheader("Maamulka Tolka & Xusuusinta")
    if df_members.empty:
        st.info("Liisku waa maran yahay hadda.")
    else:
        for idx, row in df_members.iterrows():
            with st.expander(f"👤 {row['Magaca']}"):
                st.write(f"📍 Degmada: {row.get('Degmada', row.get('Dagmada', ''))} | Xaafada: {row.get('Xaafada', '')}")
                st.write(f"📞 Tel: {row.get('Telefoonka', row.get('Telefonka', ''))}")
                
                msg = f"Asc {row['Magaca']}, nidaamka Sanduuqa Wargale wuxuu kuu xasuusinayaa qaaraanka bilaha ah ee dib ula soo dhacday. Fadlan ku soo shub xisaabta sanduuqa. Mahadsanid."
                url = f"https://wa.me/{row.get('Telefoonka', row.get('Telefonka', ''))}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[📢 Soo dir Xusuusin WhatsApp]({url})")
                
                st.write("---")
                if st.button(f"Masax Xubintaan ❌", key=f"del_{row.get('ID', idx)}"):
                    if connection_success and worksheet_members is not None:
                        try:
                            cell = worksheet_members.find(str(row['Magaca']))
                            worksheet_members.delete_rows(cell.row)
                            st.success(f"Waa laga tirtiray Drive-ka!")
                        except:
                            st.error("Waa ku guuldareystay in laga masaxo Google Drive-ka.")
                    else:
                        st.session_state.backup_members = st.session_state.backup_members[st.session_state.backup_members['Magaca'] != row['Magaca']]
                        st.success(f"Waa laga masaxay liiska hadda muuqda.")
                    st.rerun()
