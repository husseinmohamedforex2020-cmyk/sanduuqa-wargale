import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
from google.oauth2.service_account import Credentials
import gspread

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

# --- FRESH DIRECT CONNECTION ---
try:
    creds_dict = st.secrets["gspread_credentials"]
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/10g6hDn_OxyyOthefSoZ0M6s3Rr3rZZrRpdPZUnkJYIc/edit"
    sh = gc.open_by_url(sheet_url)
    
    worksheet_members = sh.worksheet("Members")
    worksheet_tx = sh.worksheet("Transactions")
    
    # Soo akhrinta xogta hadda jirta
    df_members = pd.DataFrame(worksheet_members.get_all_records())
    df_tx = pd.DataFrame(worksheet_tx.get_all_records())
    
    # Haddii tiirka Status uusan ku jirin Members, si otomaatig ah u samee
    if 'Status' not in df_members.columns and not df_members.empty:
        df_members['Status'] = 'Active'
    
    connection_success = True
except Exception as e:
    st.error("⚠️ Cilad dhanka isku xirka Google Sheets ah: Fadlan hubi Secrets-ka ama in Email-ka robot-ka uu Editor ka yahay Sheet-ka cusub.")
    df_members = pd.DataFrame(columns=['ID', 'Magaca', 'Degmada', 'Xaafada', 'Telefoonka', 'Status'])
    df_tx = pd.DataFrame(columns=['Date', 'Member_ID', 'Type', 'Amount', 'Note'])
    connection_success = False

# --- NAVIGATION MENU ---
menu = st.radio("MENU:", ["📊 Dashboard", "📝 Add Member", "💵 Gali Lacag", "📅 Gali Bile (Manual)", "📋 Liiska & WhatsApp", "⚙️ Admin Panel"], horizontal=True)

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>Sanduuqa Wargale</h3>", unsafe_allow_html=True)
    
    # Kaliya tiri xubnaha Active-ka ah
    active_members_df = df_members[df_members['Status'] == 'Active'] if 'Status' in df_members.columns else df_members
    total_members = len(active_members_df)
    
    if not df_tx.empty and 'Amount' in df_tx.columns:
        df_tx['Amount'] = pd.to_numeric(df_tx['Amount'], errors='coerce').fillna(0)
        total_deposit = df_tx[df_tx['Type'] == 'Deposit']['Amount'].sum()
        total_expense = df_tx[df_tx['Type'] == 'Expense']['Amount'].sum()
    else:
        total_deposit = 0
        total_expense = 0
        
    current_balance = total_deposit - total_expense

    st.metric(label="👥 Wadarta Tolka Active-ka ah", value=f"{total_members} Qof")
    st.metric(label="📥 Total Deposit (Lacagta Gashto)", value=f"${total_deposit:,.2f}", delta="Guud ahaan")
    st.metric(label="📤 Total Expense (Lacagta Baxday)", value=f"${total_expense:,.2f}", delta="- Kharash", delta_color="inverse")
    st.markdown("---")
    st.metric(label="💰 LACAGTA SANDUUQA KU JIRTA (HADA)", value=f"${current_balance:,.2f}")
    
    # --- CUSBOONAYSIIN: LIISKA DEPOSIT-KA SANAD KASTA ---
    st.markdown("---")
    st.markdown("### 📅 Liiska Deposit-ka ee Sannad kasta")
    if not df_tx.empty:
        df_deposits_only = df_tx[df_tx['Type'] == 'Deposit'].copy()
        if not df_deposits_only.empty:
            df_deposits_only['Date'] = pd.to_datetime(df_deposits_only['Date'], errors='coerce')
            df_deposits_only['Sannad'] = df_deposits_only['Date'].dt.year.fillna(2026).astype(int)
            
            years = sorted(df_deposits_only['Sannad'].unique(), reverse=True)
            selected_year = st.selectbox("Dooro Sannadka:", years)
            
            df_year = df_deposits_only[df_deposits_only['Sannad'] == selected_year]
            
            # Soo bandhig xogta sannadkaas
            st.dataframe(df_year[['Date', 'Member_ID', 'Amount', 'Note']], use_container_width=True)
            st.metric(label=f"Wadarta Deposit-ka Sannadkii {selected_year}", value=f"${df_year['Amount'].sum():,.2f}")
        else:
            st.info("Wax deposit ah wali lama gelin.")
    else:
        st.info("Wax xog ah oo ku jirta Transactions lama helin.")

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
                
                if connection_success and worksheet_members is not None:
                    # Marka xubin cusub la darayo, Status-keedu wuxuu noqonayaa Active
                    worksheet_members.append_row([int(new_id), full_name, degmo, xaafad, str(tel), "Active"])
                    st.success(f"Si guul leh ayaa loo kaydiyay: {full_name}")
                    st.rerun()
                else:
                    st.error("Xiriirka Google Sheet-ka ma jiro, dib u tijaabi.")
            else:
                st.error("Fadlan Magaca iyo Telefoonka waa muhiim!")

# --- 3. GALI LACAG (XUBNAHA) ---
elif menu == "💵 Gali Lacag":
    st.subheader("Diiwaangali Lacag (Hore ama Hada)")
    # Kaliya u ogolaaw xubnaha Active-ka ah inay lacag galaan
    active_members = df_members[df_members['Status'] == 'Active'] if 'Status' in df_members.columns else df_members
    
    if active_members.empty:
        st.warning("Fadlan marka hore xubin Active ah diiwaangali si aad lacag ugu qorto!")
    else:
        with st.form("money_form", clear_on_submit=True):
            member_choice = st.selectbox("Dooro Xubinta Tolka", active_members['Magaca'].tolist())
            nooca = st.radio("Nooca Lacagta", ["Deposit", "Expense"], horizontal=True)
            lacag = st.number_input("Cadadka Lacagta ($)", min_value=0.0, step=1.0)
            date_hore = st.date_input("Taariikhda (Manual)", datetime.now())
            faahfaahin = st.text_input("Note (Ex: Qaaraanka 2024)")
            
            if st.form_submit_button("Xaqiiji & Kaydi", use_container_width=True):
                if lacag > 0 and connection_success and worksheet_tx is not None:
                    m_id = df_members[df_members['Magaca'] == member_choice]['ID'].values[0]
                    worksheet_tx.append_row([str(date_hore), int(m_id), nooca, float(lacag), faahfaahin])
                    st.success(f"Waxaa la xareeyay ${lacag} oo {nooca} Bh!")
                    st.rerun()

# --- 4. GALI BILE (MANUAL DEPOSIT & EXPENSE) ---
elif menu == "📅 Gali Bile (Manual)":
    st.subheader("Diiwaengelinta Bile ah (Deposit / Expense)")
    st.caption("Qaybtani waxay kuu ogolaanaysaa inaad lacag xarayso adigoo dooranaya bisha iyo sanadka, oon xubnaha ku xirnayn.")
    
    with st.form("manual_billing_form", clear_on_submit=True):
        bilaha = ["Janaayo", "Feberaayo", "Maarso", "Abriil", "Maajo", "Juun", 
                  "Luulyo", "Agoosto", "Sebtembar", "Oktoobar", "Nofeembar", "Diisambar"]
        current_year = datetime.now().year
        sanadaha = [str(y) for y in range(2015, current_year + 3)]
        
        col1, col2 = st.columns(2)
        with col1:
            dooro_bisha = st.selectbox("Dooro Bisha", bilaha)
        with col2:
            dooro_sanadka = st.selectbox("Dooro Sanadka", sanadaha)
            
        nooca_manual = st.radio("Nooca Lacagta (Manual)", ["Deposit", "Expense"], horizontal=True)
        lacag_manual = st.number_input("Cadadka Lacagta ($)", min_value=0.0, step=1.0)
        faahfaahin_manual = st.text_input("Faahfaahinta / Note (Ex: Lacag guud ee bisha)")
        
        if st.form_submit_button("Xaqiiji & Kaydi Bile", use_container_width=True):
            if lacag_manual > 0 and connection_success and worksheet_tx is not None:
                m_id_manual = "MANUAL"
                note_final = f"[{dooro_bisha} - {dooro_sanadka}] {faahfaahin_manual}".strip()
                date_today = datetime.now().strftime("%Y-%m-%d")
                
                worksheet_tx.append_row([str(date_today), str(m_id_manual), nooca_manual, float(lacag_manual), note_final])
                st.success(f"Si guul leh ayaa loo kaydiyay {nooca_manual} bisha {dooro_bisha}/{dooro_sanadka} oo dhan ${lacag_manual}!")
                st.rerun()
            elif lacag_manual <= 0:
                st.error("Fadlan geli lacag ka badan $0!")
            else:
                st.error("Xiriirka Google Sheet-ka ma jiro, dib u tijaabi.")

# --- 5. LIISKA & WHATSAPP ---
elif menu == "📋 Liiska & WhatsApp":
    st.subheader("Maamulka Tolka & Xusuusinta")
    if df_members.empty:
        st.info("Liisku waa maran yahay hadda.")
    else:
        for idx, row in df_members.iterrows():
            status_tag = "🟢 Active" if row.get('Status', 'Active') == 'Active' else "🔴 Inactive"
            with st.expander(f"👤 {row['Magaca']} ({status_tag})"):
                st.write(f"📍 Degmada: {row.get('Degmada', '')} | Xaafada: {row.get('Xaafada', '')}")
                st.write(f"📞 Tel: {row.get('Telefoonka', '')}")
                
                msg = f"Asc {row['Magaca']}, nidaamka Sanduuqa Wargale wuxuu kuu xasuusinayaa qaaraanka bilaha ah. Fadlan ku soo shub xisaabta sanduuqa. Mahadsanid."
                url = f"https://wa.me/{row.get('Telefoonka', '')}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[📢 Soo dir Xusuusin WhatsApp]({url})")

# --- 6. CUSBOONAYSIIN: ADMIN PANEL (EDIT / DELETE) ---
elif menu == "⚙️ Admin Panel":
    st.markdown("<h2 style='color: #1E3A8A;'>⚙️ Guddiga Maamulka (Admin Panel)</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👥 Maamulka Xubnaha", "📥 Sixidda Deposits", "📤 Sixidda Expenses"])
    
    # --- TAB 1: MAAMULKA XUBNAHA ---
    with tab1:
        st.subheader("Wax ka baddal, Tiri ama Beddel Status-ka Member-ka")
        if df_members.empty:
            st.info("Wali wax xubin ah ma diiwaangashna.")
        else:
            selected_m_name = st.selectbox("Dooro Xubinta:", df_members['Magaca'].tolist(), key="admin_m_select")
            m_row_idx = df_members[df_members['Magaca'] == selected_m_name].index[0]
            m_data = df_members.iloc[m_row_idx]
            sheet_row_num = m_row_idx + 2 # +2 sababtoo ah Header-ka Google Sheet iyo Index-ka 0-da ka bilaabma
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📝 Edit / Status")
                edit_name = st.text_input("Magaca Xubinta", value=m_data['Magaca'])
                edit_degmo = st.text_input("Degmada", value=m_data.get('Degmada', ''))
                edit_xaafad = st.text_input("Xaafada", value=m_data.get('Xaafada', ''))
                edit_tel = st.text_input("Telefoonka", value=m_data.get('Telefoonka', ''))
                
                current_status = m_data.get('Status', 'Active')
                status_options = ["Active", "Inactive"]
                edit_status = st.selectbox("Heerka Xubinta (Status):", status_options, index=status_options.index(current_status))
                
                if st.button("Badbaadi Isbeddelka Xubinta", use_container_width=True):
                    if connection_success:
                        # Cusboonaysii safka xubinta ee Google Sheets
                        worksheet_members.update(range_name=f"A{sheet_row_num}:F{sheet_row_num}", 
                                                 values=[[int(m_data['ID']), edit_name, edit_degmo, edit_xaafad, str(edit_tel), edit_status]])
                        st.success(f"Isbeddelka xogta {edit_name} waa la kaydiyay!")
                        st.rerun()
            
            with col2:
                st.markdown("### 🗑️ Tiri Xubinta")
                st.warning(f"Ma hubtaa inaad tirtirto {selected_m_name}?")
                if st.button("Haa, Gabi ahaanba Tiri Xubinta", key="del_member_admin", use_container_width=True):
                    if connection_success:
                        worksheet_members.delete_rows(sheet_row_num)
                        st.error(f"Xubintii {selected_m_name} waa la tirtiray!")
                        st.rerun()

    # --- TAB 2: SIXIDDA DEPOSITS ---
    with tab2:
        st.subheader("Sixidda iyo Tirtirista Deposits-ka qaldan")
        df_dep = df_tx[df_tx['Type'] == 'Deposit'].copy() if f'Type' in df_tx.columns else pd.DataFrame()
        
        if df_dep.empty:
            st.info("Ma jiraan wax xog Deposit ah oo hadda diiwaangashan.")
        else:
            # Samee magac ka kooban taariikh, ID iyo lacag si loo doorto safka saxda ah
            df_dep['Selector'] = df_dep['Date'].astype(str) + " - Member: " + df_dep['Member_ID'].astype(str) + " - $" + df_dep['Amount'].astype(str) + " (" + df_dep['Note'].astype(str) + ")"
            selected_dep_str = st.selectbox("Dooro Entry-ga khaldan:", df_dep['Selector'].tolist(), key="dep_select")
            
            # Hel index-ka saxda ah ee df_tx dhexdiisa
            original_idx = df_tx[df_tx['Date'].astype(str) + " - Member: " + df_tx['Member_ID'].astype(str) + " - $" + df_tx['Amount'].astype(str) + " (" + df_tx['Note'].astype(str) + ")" == selected_dep_str].index[0]
            tx_row_num = original_idx + 2
            dep_data = df_tx.iloc[original_idx]
            
            c_dep1, c_dep2 = st.columns(2)
            with c_dep1:
                st.markdown("### 📝 Edit Deposit")
                edit_dep_amount = st.number_input("Cadadka Lacagta Saxda ah ($):", value=float(dep_data['Amount']), key="edit_dep_amt")
                edit_dep_note = st.text_input("Note-ka Saxda ah:", value=str(dep_data['Note']), key="edit_dep_nt")
                edit_dep_date = st.text_input("Taariikhda (YYYY-MM-DD):", value=str(dep_data['Date']), key="edit_dep_dt")
                
                if st.button("Cusboonaysii Deposit-ka", use_container_width=True):
                    if connection_success:
                        worksheet_tx.update(range_name=f"A{tx_row_num}:E{tx_row_num}", 
                                             values=[[str(edit_dep_date), str(dep_data['Member_ID']), "Deposit", float(edit_dep_amount), edit_dep_note]])
                        st.success("Deposit-ka si guul leh ayaa loo saxay!")
                        st.rerun()
            
            with c_dep2:
                st.markdown("### 🗑️ Tiri Deposit")
                st.warning("Haddii aad tirtirto entry-gan, lacagta sanduuqa dib ayay uga bixi doontaa.")
                if st.button("Haa, Tiri Deposit-kan", key="del_dep_btn", use_container_width=True):
                    if connection_success:
                        worksheet_tx.delete_rows(tx_row_num)
                        st.error("Deposit-ka waa la tirtiray!")
                        st.rerun()

    # --- TAB 3: SIXIDDA EXPENSES ---
    with tab3:
        st.subheader("Sixidda iyo Tirtirista Expenses-ka qaldan")
        df_exp = df_tx[df_tx['Type'] == 'Expense'].copy() if f'Type' in df_tx.columns else pd.DataFrame()
        
        if df_exp.empty:
            st.info("Ma jiraan wax xog Expense (Kharash) ah oo hadda diiwaangashan.")
        else:
            df_exp['Selector'] = df_exp['Date'].astype(str) + " - Ref: " + df_exp['Member_ID'].astype(str) + " - $" + df_exp['Amount'].astype(str) + " (" + df_exp['Note'].astype(str) + ")"
            selected_exp_str = st.selectbox("Dooro Entry-ga khaldan:", df_exp['Selector'].tolist(), key="exp_select")
            
            original_idx = df_tx[df_tx['Date'].astype(str) + " - Ref: " + df_tx['Member_ID'].astype(str) + " - $" + df_tx['Amount'].astype(str) + " (" + df_tx['Note'].astype(str) + ")" == selected_exp_str].index[0]
            tx_row_num = original_idx + 2
            exp_data = df_tx.iloc[original_idx]
            
            c_exp1, c_exp2 = st.columns(2)
            with c_exp1:
                st.markdown("### 📝 Edit Expense")
                edit_exp_amount = st.number_input("Cadadka Lacagta Saxda ah ($):", value=float(exp_data['Amount']), key="edit_exp_amt")
                edit_exp_note = st.text_input("Note-ka Saxda ah:", value=str(exp_data['Note']), key="edit_exp_nt")
                edit_exp_date = st.text_input("Taariikhda (YYYY-MM-DD):", value=str(exp_data['Date']), key="edit_exp_dt")
                
                if st.button("Cusboonaysii Kharashka", use_container_width=True):
                    if connection_success:
                        worksheet_tx.update(range_name=f"A{tx_row_num}:E{tx_row_num}", 
                                             values=[[str(edit_exp_date), str(exp_data['Member_ID']), "Expense", float(edit_exp_amount), edit_exp_note]])
                        st.success("Kharashka si guul leh ayaa loo saxay!")
                        st.rerun()
            
            with c_exp2:
                st.markdown("### 🗑️ Tiri Expense")
                st.warning("Kharashkan haddii aad tirtirto, lacagta sanduuqa dib ayay ugu soo laaban doontaa.")
                if st.button("Haa, Tiri Kharashkan", key="del_exp_btn", use_container_width=True):
                    if connection_success:
                        worksheet_tx.delete_rows(tx_row_num)
                        st.error("Kharashka waa la tirtiray!")
                        st.rerun()
