import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ------------------------------------------------------------------
# 1. MIPANGILIO YA MFUMO NA CACHING
# ------------------------------------------------------------------
st.set_page_config(page_title="Mfumo wa Matokeo O-Level", layout="wide")

@st.cache_data
def calculate_grade_and_points(score):
    if score is None or pd.isna(score) or score == '': return None, None
    try:
        score = float(score)
        if score >= 75: return 'A', 1
        elif score >= 65: return 'B', 2
        elif score >= 45: return 'C', 3
        elif score >= 30: return 'D', 4
        else: return 'F', 5
    except ValueError:
        return None, None

@st.cache_data
def calculate_division(pointi_za_masomo, valid_subjects, total_registered_subjects):
    if valid_subjects == 0:
        return 'ABS', 0
    if valid_subjects < 7:
        return 'INC', sum(pointi_za_masomo)
    
    pointi_za_masomo.sort()
    pointi_saba = sum(pointi_za_masomo[:7])
    
    if 7 <= pointi_saba <= 17: return 'I', pointi_saba
    elif pointi_saba <= 21: return 'II', pointi_saba
    elif pointi_saba <= 25: return 'III', pointi_saba
    elif pointi_saba <= 33: return 'IV', pointi_saba
    else: return '0', pointi_saba

# ------------------------------------------------------------------
# 2. SESSION STATE & SETUP
# ------------------------------------------------------------------
st.sidebar.title("MIPANGILIO YA MFUMO")
kidato_kilichochaguliwa = st.sidebar.selectbox(
    "Chagua Kidato:", 
    ["KIDATO CHA KWANZA", "KIDATO CHA PILI", "KIDATO CHA TATU", "KIDATO CHA NNE"]
)
darasa_id = kidato_kilichochaguliwa.replace(" ", "_")

if f'shule_info_{darasa_id}' not in st.session_state:
    st.session_state[f'shule_info_{darasa_id}'] = {
        "wizara": "PRIME MINISTER'S OFFICE",
        "idara": "REGIONAL ADMINISTRATION AND LOCAL GOVERNMENT",
        "mkoa": "MWANZA REGION", 
        "wilaya": "BUCHOSA DISTRICT COUNCIL", 
        "shule": "CHEMA SECONDARY SCHOOL", 
        "namba_shule": "S7647", 
        "aina_mtihani": "TERMINAL JOINT EXAMINATION", 
        "mwaka": "2026, MAY-2026"
    }

if f'masomo_shule_{darasa_id}' not in st.session_state:
    st.session_state[f'masomo_shule_{darasa_id}'] = ['HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS', 'IT SUPPORT SERVICES']

if f'remarks_dict_{darasa_id}' not in st.session_state:
    st.session_state[f'remarks_dict_{darasa_id}'] = {'A': 'Bora Sana', 'B': 'Bora', 'C': 'Vizuri', 'D': 'Inaridhisha', 'F': 'Imefeli'}

if f'wanafunzi_db_{darasa_id}' not in st.session_state:
    st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])

if f'masomo_wanafunzi_{darasa_id}' not in st.session_state:
    st.session_state[f'masomo_wanafunzi_{darasa_id}'] = {}

if f'alama_majaribio_db_{darasa_id}' not in st.session_state:
    st.session_state[f'alama_majaribio_db_{darasa_id}'] = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Somo', 'Alama'])

if f'alama_mitihani_db_{darasa_id}' not in st.session_state:
    st.session_state[f'alama_mitihani_db_{darasa_id}'] = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Somo', 'Alama'])

if f'mfumo_umefungwa_{darasa_id}' not in st.session_state:
    st.session_state[f'mfumo_umefungwa_{darasa_id}'] = False

shule_info = st.session_state[f'shule_info_{darasa_id}']
masomo_shule = st.session_state[f'masomo_shule_{darasa_id}']
remarks_dict = st.session_state[f'remarks_dict_{darasa_id}']
wanafunzi_db = st.session_state[f'wanafunzi_db_{darasa_id}']
masomo_wanafunzi = st.session_state[f'masomo_wanafunzi_{darasa_id}']

for jina in wanafunzi_db['Jina la Mwanafunzi'].tolist():
    if jina not in masomo_wanafunzi:
        masomo_wanafunzi[jina] = masomo_shule.copy()

def get_student_subject_average(jina, somo, db_maj, db_mit):
    maj_val = db_maj[(db_maj['Jina la Mwanafunzi'] == jina) & (db_maj['Somo'] == somo)]['Alama'].values
    mit_val = db_mit[(db_mit['Jina la Mwanafunzi'] == jina) & (db_mit['Somo'] == somo)]['Alama'].values
    
    has_maj = len(maj_val) > 0 and pd.notna(maj_val[0])
    has_mit = len(mit_val) > 0 and pd.notna(mit_val[0])
    
    if has_maj and has_mit:
        return round((float(maj_val[0]) + float(mit_val[0])) / 2, 1)
    elif has_maj:
        return round(float(maj_val[0]), 1)
    elif has_mit:
        return round(float(mit_val[0]), 1)
    else:
        return None

# ------------------------------------------------------------------
# 3. UDHIBITI WA UFIKIAJI (ACCESS CONTROL)
# ------------------------------------------------------------------
hali_ya_mtumiaji = st.sidebar.selectbox("Aina ya Mtumiaji:", ["Mwalimu (Jaza Alama Tu)", "Admin (Mkuu wa Shule)"])
is_admin = False
if hali_ya_mtumiaji == "Admin (Mkuu wa Shule)":
    pin_ingizwa = st.sidebar.text_input("Ingiza PIN ya Admin:", type="password")
    if pin_ingizwa == "1234":
        is_admin = True
        st.sidebar.success(f"Umeingia kama Admin ({kidato_kilichochaguliwa})")
        
        st.sidebar.write("---")
        st.sidebar.subheader("Usimamizi wa Kufunga Alama")
        hali_ya_sasa = st.session_state[f'mfumo_umefungwa_{darasa_id}']
        if hali_ya_sasa:
            st.sidebar.error("🔒 Alama Zimefungwa Rasmi!")
            if st.sidebar.button("Fungua Alama (Unlock)"):
                st.session_state[f'mfumo_umefungwa_{darasa_id}'] = False
                st.rerun()
        else:
            st.sidebar.success("🔓 Alama ziko wazi.")
            if st.sidebar.button("Funga Alama Rasmi (Lock)"):
                st.session_state[f'mfumo_umefungwa_{darasa_id}'] = True
                st.rerun()
    elif pin_ingizwa != "":
        st.sidebar.error("PIN Si Sahihi!")

orodha_ya_menu = ["0. Kuhusu Mfumo"]
if is_admin:
    orodha_ya_menu.extend([
        "1. Taarifa za Shule na Mtihani",
        "2. Usajili wa Masomo ya Shule (Hadi 20)",
        "3. Sajili Majina ya Wanafunzi",
        "4. Kumsajilia Mwanafunzi Masomo"
    ])

orodha_ya_menu.extend([
    "5. Kujaza Alama za Majaribio (100%)",
    "6. Kujaza Alama za Mitihani (100%)",
    "7. Wastani wa Majaribio & Mitihani",
    "10. Matokeo ya NECTA Format & Summary",
    "11. Ripoti Binafsi ya Mwanafunzi (PDF)",
    "12. Pakua Fomu za CAL na ISAL"
])

st.sidebar.write("---")
st.sidebar.title("MENU KUU")
chaguo = st.sidebar.radio("Nenda kwenye kipengele:", orodha_ya_menu)
names_list = wanafunzi_db['Jina la Mwanafunzi'].tolist()

# KIPENGELE 0
if chaguo == "0. Kuhusu Mfumo":
    st.header(f"Mfumo wa Kuchakata Matokeo - {kidato_kilichochaguliwa}")
    st.info(f"Hivi sasa unashughulikia data za darasa la: **{kidato_kilichochaguliwa}** kwenye mfumo wa matokeo.app.")
    if st.session_state[f'mfumo_umefungwa_{darasa_id}']:
        st.error("Hali ya Mfumo: Alama zimefungwa na haziruhusiwi kubadilishwa.")
    else:
        st.success("Hali ya Mfumo: Alama ziko wazi kwa ajili ya kuingizwa na kuhaririwa.")

# KIPENGELE 1
elif chaguo == "1. Taarifa za Shule na Mtihani" and is_admin:
    st.header("1. Taarifa za Shule na Mtihani")
    with st.form("taarifa_shule_form"):
        shule_info["wizara"] = st.text_input("Wizara", shule_info["wizara"])
        shule_info["idara"] = st.text_input("Idara Kuu", shule_info["idara"])
        shule_info["mkoa"] = st.text_input("Mkoa", shule_info["mkoa"])
        shule_info["wilaya"] = st.text_input("Wilaya / Halmashauri", shule_info["wilaya"])
        shule_info["shule"] = st.text_input("Jina la Shule", shule_info["shule"])
        shule_info["namba_shule"] = st.text_input("Namba ya Kituo (Centre No)", shule_info["namba_shule"])
        shule_info["aina_mtihani"] = st.text_input("Aina ya Mtihani", shule_info["aina_mtihani"])
        shule_info["mwaka"] = st.text_input("Mwaka / Kipindi", shule_info["mwaka"])
        
        for key in remarks_dict.keys():
            remarks_dict[key] = st.text_input(f"Maelezo ya Gredi {key}:", remarks_dict[key])
            
        if st.form_submit_button("Hifadhi Taarifa Zote"):
            st.success("🎉 Taarifa za shule zimehifadhiwa!")

# KIPENGELE 2
elif chaguo == "2. Usajili wa Masomo ya Shule (Hadi 20)" and is_admin:
    st.header("2. Usajili wa Masomo ya Shule")
    with st.form("masomo_shule_form"):
        masomo_maandishi = st.text_area("Masomo (tenganisha kwa koma ,):", ", ".join(masomo_shule))
        if st.form_submit_button("Hifadhi Orodha ya Masomo"):
            masomo_yaliyosafishwa = [m.strip().upper() for m in masomo_maandishi.split(",") if m.strip()]
            if len(masomo_yaliyosafishwa) > 20:
                st.error("Umevuka kikomo cha masomo 20!")
            else:
                st.session_state[f'masomo_shule_{darasa_id}'] = masomo_yaliyosafishwa
                st.success(f"🎉 Jumla ya masomo {len(masomo_yaliyosafishwa)} yamehifadhiwa!")

# KIPENGELE 3
elif chaguo == "3. Sajili Majina ya Wanafunzi" and is_admin:
    st.header("3. Sajili Wanafunzi")
    tab1, tab2 = st.tabs(["Fomu ya Usajili", "Kupandisha Excel"])
    with tab1:
        with st.form(f"fomu_mwanafunzi_{darasa_id}"):
            mpya_jina = st.text_input("Jina Kamili:").upper()
            mpya_jinsia = st.selectbox("Jinsia:", ["M", "F"])
            mpya_namba = st.text_input("Namba ya Usajili:", f"{shule_info['namba_shule']}/{str(len(wanafunzi_db)+1).zfill(4)}")
            if st.form_submit_button("Hifadhi Mwanafunzi") and mpya_jina:
                mpya_row = pd.DataFrame([[mpya_jina, mpya_jinsia, mpya_namba]], columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
                st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.concat([wanafunzi_db, mpya_row], ignore_index=True)
                st.success(f"🎉 {mpya_jina} amesajiliwa!")
                st.rerun()
    with tab2:
        uploaded_file = st.file_uploader("Pandisha Excel ya Wanafunzi (.xlsx):", type=["xlsx"])
        if uploaded_file is not None:
            df_up = pd.read_excel(uploaded_file)
            df_up.columns = [str(c).strip() for c in df_up.columns]
            if 'Jina la Mwanafunzi' in df_up.columns:
                st.session_state[f'wanafunzi_db_{darasa_id}'] = df_up[['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili']].dropna(subset=['Jina la Mwanafunzi']).reset_index(drop=True)
                st.success("🎉 Wanafunzi wamehifadhiwa kutoka Excel!")
                st.rerun()
    
    st.write("---")
    st.dataframe(wanafunzi_db, use_container_width=True, hide_index=True)

# KIPENGELE 4: KIMERUDISHWA (Usajili wa Masomo kwa Mmoja-mmoja na kwa Excel)
elif chaguo == "4. Kumsajilia Mwanafunzi Masomo" and is_admin:
    st.header("4. Kusajili Masomo ya Wanafunzi")
    tab_moja, tab_excel = st.tabs(["Kusajili Mmoja-mmoja", "Kusajili kupitia Excel"])
    
    with tab_moja:
        if names_list:
            mwanafunzi_sel = st.selectbox("Chagua Mwanafunzi:", names_list)
            masomo_yake = st.multiselect(f"Masomo ya {mwanafunzi_sel}:", masomo_shule, default=masomo_wanafunzi.get(mwanafunzi_sel, masomo_shule))
            if st.button("Hifadhi Masomo ya Mwanafunzi Huyu"):
                st.session_state[f'masomo_wanafunzi_{darasa_id}'][mwanafunzi_sel] = masomo_yake
                st.success("🎉 Masomo yamehifadhiwa kikamilifu!")
        else:
            st.warning("Weka wanafunzi kwanza kwenye Kipengele 3.")
            
    with tab_excel:
        st.info("Pakia faili la Excel ambalo lina safu (columns) za 'Jina la Mwanafunzi' na masomo ambapo mwanafunzi anasoma yanawekewa alama ya V (Yes) au herufi 'Yes' au '1', au unaweza kupakua fomu ya mfano hapa chini.")
        
        # Kutoa template ya mfano ya Excel ya kusajili masomo
        if names_list:
            sample_data = {'Jina la Mwanafunzi': names_list}
            for s in masomo_shule:
                sample_data[s] = ['Yes'] * len(names_list)
            df_sample = pd.DataFrame(sample_data)
            
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='xlsxwriter') as writer:
                df_sample.to_excel(writer, index=False, sheet_name='Usajili_Masomo')
            buffer_excel.seek(0)
            
            st.download_button(
                label="📥 Pakua Fomu ya Mfano ya Excel ya Masomo",
                data=buffer_excel.getvalue(),
                file_name=f"Fomu_Usajili_Masomo_{darasa_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.write("---")
            uploaded_sub_file = st.file_uploader("Pandisha Excel Iliyojazwa ya Masomo (.xlsx):", type=["xlsx"], key="upload_sub")
            if uploaded_sub_file is not None:
                df_sub_up = pd.read_excel(uploaded_sub_file)
                df_sub_up.columns = [str(c).strip() for c in df_sub_up.columns]
                if 'Jina la Mwanafunzi' in df_sub_up.columns:
                    count_updated = 0
                    for _, row in df_sub_up.iterrows():
                        jina = row['Jina la Mwanafunzi']
                        if jina in names_list:
                            chaguo_huru = []
                            for s in masomo_shule:
                                if s in df_sub_up.columns:
                                    val = str(row[s]).strip().upper()
                                    if val in ['YES', 'Y', '1', 'TRUE', 'V']:
                                        chaguo_huru.append(s)
                            if chaguo_huru:
                                st.session_state[f'masomo_wanafunzi_{darasa_id}'][jina] = chaguo_huru
                                count_updated += 1
                    st.success(f"🎉 Imefanikiwa kusajili masomo kwa wanafunzi {count_updated} kupitia Excel!")
                    st.rerun()
                else:
                    st.error("Faili la Excel halina safu ya 'Jina la Mwanafunzi'.")

# KIPENGELE 5 & 6 (ZIMEUNGANISHWA NA UDHIBITI WA KUFUNGA MFUMO)
elif chaguo in ["5. Kujaza Alama za Majaribio (100%)", "6. Kujaza Alama za Mitihani (100%)"]:
    is_majaribio = "Majaribio" in chaguo
    db_key = f'alama_majaribio_db_{darasa_id}' if is_majaribio else f'alama_mitihani_db_{darasa_id}'
    st.header(f"Kujaza Alama za { 'Majaribio' if is_majaribio else 'Mitihani' }")
    
    mfumo_umefungwa = st.session_state.get(f'mfumo_umefungwa_{darasa_id}', False)
    
    if mfumo_umefungwa:
        st.error("🔒 Samahani, matokeo yameshafungwa na Mkuu wa Shule (Admin). Huwezi kubadilisha au kuongeza alama tena.")
    
    if names_list:
        somo_sel = st.selectbox("Chagua Somo:", masomo_shule)
        wanafunzi_wa_somo = [jina for jina in names_list if somo_sel in masomo_wanafunzi.get(jina, masomo_shule)]
        current_db = st.session_state[db_key]
        
        rows_to_edit = []
        for idx, jina in enumerate(wanafunzi_wa_somo):
            zilizopo = current_db[(current_db['Jina la Mwanafunzi'] == jina) & (current_db['Somo'] == somo_sel)]
            alama_iliyopo = zilizopo['Alama'].values[0] if not zilizopo.empty else np.nan
            m_info = wanafunzi_db[wanafunzi_db['Jina la Mwanafunzi'] == jina].iloc[0]
            rows_to_edit.append({'S/N': idx + 1, 'Jina la Mwanafunzi': jina, 'Jinsia (M/F)': m_info['Jinsia (M/F)'], 'Namba ya Usajili': m_info['Namba ya Usajili'], 'Alama (100%)': alama_iliyopo})
        
        df_editor = pd.DataFrame(rows_to_edit)
        
        edited_df = st.data_editor(
            df_editor, 
            use_container_width=True, 
            disabled=True if mfumo_umefungwa else ['S/N', 'Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'], 
            hide_index=True
        )
        
        if not mfumo_umefungwa:
            if st.button(f"Hifadhi Alama za {somo_sel}"):
                temp_db = current_db[current_db['Somo'] != somo_sel].copy()
                new_rows = []
                for _, r in edited_df.iterrows():
                    val = r['Alama (100%)']
                    if pd.notna(val) and str(val).strip() != "":
                        new_rows.append({'Jina la Mwanafunzi': r['Jina la Mwanafunzi'], 'Somo': somo_sel, 'Alama': float(val)})
                if new_rows:
                    temp_db = pd.concat([temp_db, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state[db_key] = temp_db
                st.success("🎉 Alama zimehifadhiwa kikamilifu!")

# KIPENGELE 7
elif chaguo == "7. Wastani wa Majaribio & Mitihani":
    st.header("7. Wastani wa Alama (Majaribio & Mitihani)")
    db_maj = st.session_state[f'alama_majaribio_db_{darasa_id}']
    db_mit = st.session_state[f'alama_mitihani_db_{darasa_id}']
    
    rows_avg = []
    for idx, mwa in wanafunzi_db.iterrows():
        jina = mwa['Jina la Mwanafunzi']
        stari = {'S/N': idx + 1, 'Jina la Mwanafunzi': jina, 'Jinsia': mwa['Jinsia (M/F)']}
        m_yake = masomo_wanafunzi.get(jina, masomo_shule)
        for s in masomo_shule:
            if s not in m_yake:
                stari[s] = "-"
                continue
            avg_val = get_student_subject_average(jina, s, db_maj, db_mit)
            stari[s] = avg_val if avg_val is not None else ""
        rows_avg.append(stari)
    if rows_avg:
        st.dataframe(pd.DataFrame(rows_avg), use_container_width=True, hide_index=True)

# KIPENGELE 10: NECTA FORMAT & PDF DOWNLOAD
elif chaguo == "10. Matokeo ya NECTA Format & Summary":
    st.header("10. Broadsheet ya Matokeo (NECTA Format)")
    db_maj = st.session_state[f'alama_majaribio_db_{darasa_id}']
    db_mit = st.session_state[f'alama_mitihani_db_{darasa_id}']
    
    pdf_aina_chaguo = st.selectbox("Chagua Aina ya Matokeo ya Kwenye PDF:", ["Matokeo ya Jumla (Wastani wa Majaribio & Mitihani)", "Majaribio Pekee", "Mitihani Pekee"])
    
    if len(names_list) == 0:
        st.warning("Tafadhali sajili wanafunzi kwanza.")
    else:
        st.markdown(f"<h3 style='text-align: center;'>{shule_info['wizara']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{shule_info['shule']} ({shule_info['namba_shule']})</h4>", unsafe_allow_html=True)
        
        orodha_ripoti = []
        for idx, mwanafunzi in wanafunzi_db.iterrows():
            jina = mwanafunzi['Jina la Mwanafunzi']
            taarifa = {'NAME OF CANDIDATE': jina, 'SEX': mwanafunzi['Jinsia (M/F)'], 'INDEX NO': mwanafunzi['Namba ya Usajili']}
            
            pointi_za_masomo = []
            jumla_alama = 0.0
            masomo_yaliyofanywa = 0
            masomo_yake = masomo_wanafunzi.get(jina, masomo_shule)

            for somo in masomo_shule:
                if somo not in masomo_yake:
                    taarifa[f"{somo} GR"] = "-"
                    continue

                if pdf_aina_chaguo == "Majaribio Pekee":
                    val_row = db_maj[(db_maj['Jina la Mwanafunzi'] == jina) & (db_maj['Somo'] == somo)]['Alama'].values
                    wastani = float(val_row[0]) if len(val_row) > 0 and pd.notna(val_row[0]) else None
                elif pdf_aina_chaguo == "Mitihani Pekee":
                    val_row = db_mit[(db_mit['Jina la Mwanafunzi'] == jina) & (db_mit['Somo'] == somo)]['Alama'].values
                    wastani = float(val_row[0]) if len(val_row) > 0 and pd.notna(val_row[0]) else None
                else:
                    wastani = get_student_subject_average(jina, somo, db_maj, db_mit)
                
                daraja, pointi = calculate_grade_and_points(wastani)
                taarifa[f"{somo} GR"] = daraja if daraja else "-"
                if daraja:
                    pointi_za_masomo.append(pointi)
                    jumla_alama += wastani
                    masomo_yaliyofanywa += 1

            div, pts = calculate_division(pointi_za_masomo, masomo_yaliyofanywa, len(masomo_yake))
            taarifa['TOTAL MARKS'] = round(jumla_alama, 1) if masomo_yaliyofanywa > 0 else ""
            taarifa['AVG'] = round(jumla_alama / masomo_yaliyofanywa, 1) if masomo_yaliyofanywa > 0 else ""
            taarifa['POINTS'] = pts if div not in ['ABS', 'INC'] else ""
            taarifa['DIV'] = div
            orodha_ripoti.append(taarifa)

        if orodha_ripoti:
            df_final = pd.DataFrame(orodha_ripoti)
            df_final.insert(0, 'S/N', range(1, len(df_final) + 1))
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            if st.button("📥 Pakua Matokeo haya ya NECTA Format (PDF)"):
                buffer_pdf = io.BytesIO()
                doc = SimpleDocTemplate(buffer_pdf, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                story = []
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle('TStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=1)
                normal_style = ParagraphStyle('NStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
                header_style = ParagraphStyle('HStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.whitesmoke)
                
                story.append(Paragraph(shule_info['wizara'], title_style))
                story.append(Paragraph(shule_info['wilaya'], title_style))
                story.append(Paragraph(f"{shule_info['shule']} - {shule_info['namba_shule']} ({kidato_kilichochaguliwa})", title_style))
                story.append(Paragraph(f"AINA YA RIPOTI: {pdf_aina_chaguo.upper()}", title_style))
                story.append(Spacer(1, 15))
                
                table_headers = ['S/N', 'INDEX NO', 'CANDIDATE NAME', 'SEX', 'DIV', 'PTS'] + [s[:4].upper() for s in masomo_shule]
                table_data = [[Paragraph(h, header_style) for h in table_headers]]
                
                for idx, row in df_final.iterrows():
                    r_data = [
                        str(row['S/N']),
                        str(row['INDEX NO']),
                        str(row['NAME OF CANDIDATE']),
                        str(row['SEX']),
                        str(row['DIV']),
                        str(row['POINTS'])
                    ]
                    for s in masomo_shule:
                        r_data.append(str(row.get(f"{s} GR", "-")))
                    table_data.append([Paragraph(cell, normal_style) for cell in r_data])
                
                t_necta = Table(table_data)
                t_necta.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(t_necta)
                doc.build(story)
                buffer_pdf.seek(0)
                
                st.download_button(
                    label="💾 Bonyeza Hapa Kupakua PDF ya NECTA Format",
                    data=buffer_pdf.getvalue(),
                    file_name=f"NECTA_Format_{darasa_id}_{pdf_aina_chaguo.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

# KIPENGELE 11
elif chaguo == "11. Ripoti Binafsi ya Mwanafunzi (PDF)":
    st.header("11. Pakua Ripoti ya Mwanafunzi Binafsi / Shule Nzima")
    db_maj = st.session_state[f'alama_majaribio_db_{darasa_id}']
    db_mit = st.session_state[f'alama_mitihani_db_{darasa_id}']

    if names_list:
        def andaa_data_mwanafunzi(jina_mwa):
            data_somo_pdf = [["Somo", "Majaribio", "Mitihani", "Wastani", "Gredi", "Maelezo"]]
            masomo_yake = masomo_wanafunzi.get(jina_mwa, masomo_shule)
            pointi_list = []
            
            for somo in masomo_shule:
                if somo in masomo_yake:
                    maj_val = db_maj[(db_maj['Jina la Mwanafunzi'] == jina_mwa) & (db_maj['Somo'] == somo)]['Alama'].values
                    mit_val = db_mit[(db_mit['Jina la Mwanafunzi'] == jina_mwa) & (db_mit['Somo'] == somo)]['Alama'].values
                    
                    cwt_str = str(round(float(maj_val[0]), 1)) if len(maj_val) > 0 and pd.notna(maj_val[0]) else "-"
                    eet_str = str(round(float(mit_val[0]), 1)) if len(mit_val) > 0 and pd.notna(mit_val[0]) else "-"
                    
                    tot = get_student_subject_average(jina_mwa, somo, db_maj, db_mit)
                    gr, pt = calculate_grade_and_points(tot)
                    
                    if gr: 
                        pointi_list.append(pt)
                        rem = remarks_dict.get(gr, '')
                    else:
                        rem = '-'
                    data_somo_pdf.append([somo, cwt_str, eet_str, str(tot) if tot is not None else "-", gr if gr else "-", rem])
                else:
                    data_somo_pdf.append([somo, "-", "-", "-", "-", "Hajachagua"])
            
            div_final, pts_saba = calculate_division(pointi_list, len(pointi_list), len(masomo_yake))
            return data_somo_pdf, pts_saba, div_final

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            mwanafunzi_sel = st.selectbox("Chagua mwanafunzi:", names_list)
            if st.button(f"Tengeneza PDF ya {mwanafunzi_sel}"):
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
                story = []
                styles = getSampleStyleSheet()
                style_head = ParagraphStyle('HHead', parent=styles['Heading2'], alignment=1, spaceAfter=4)
                style_normal = ParagraphStyle('NHead', parent=styles['Normal'], spaceAfter=12, fontSize=11)
                
                story.append(Paragraph(f"<b>{shule_info['wizara']}</b>", style_head))
                story.append(Paragraph(f"<b>{shule_info['shule']} (CENTRE: {shule_info['namba_shule']})</b>", style_head))
                story.append(Spacer(1, 15))
                
                m_info = wanafunzi_db[wanafunzi_db['Jina la Mwanafunzi'] == mwanafunzi_sel].iloc[0]
                story.append(Paragraph(f"<b>Jina:</b> {mwanafunzi_sel} | <b>Jinsia:</b> {m_info['Jinsia (M/F)']} | <b>Namba:</b> {m_info['Namba ya Usajili']}", style_normal))
                
                data_somo, pts, div = andaa_data_mwanafunzi(mwanafunzi_sel)
                t = Table(data_somo, colWidths=[160, 70, 70, 70, 50, 100])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
                ]))
                story.append(t)
                story.append(Spacer(1, 15))
                
                show_pts = pts if div not in ['ABS', 'INC'] else '-'
                story.append(Paragraph(f"<b>JUMLA YA POINTI:</b> {show_pts} &nbsp;&nbsp;&nbsp;&nbsp; <b>DIVISION:</b> {div}", style_normal))
                
                doc.build(story)
                buffer.seek(0)
                st.download_button(label="Pakua Faili la PDF", data=buffer.getvalue(), file_name=f"{mwanafunzi_sel.replace(' ', '_')}.pdf", mime="application/pdf")
    else:
        st.warning("Weka wanafunzi kwanza.")

# KIPENGELE 12
elif chaguo == "12. Pakua Fomu za CAL na ISAL":
    st.header("12. Pakua Fomu Rasmi za CAL na ISAL (NECTA Format)")
    if names_list:
        tab_cal, tab_isal = st.tabs(["📊 PAKUA CAL (Jumla)", "📝 PAKUA ISAL (Kila Somo)"])
        with tab_cal:
            rows_cal = []
            for idx, mwa in wanafunzi_db.iterrows():
                jina = mwa['Jina la Mwanafunzi']
                m_yake = masomo_wanafunzi.get(jina, masomo_shule)
                stari = {
                    'S/N': idx + 1,
                    'NAME OF CANDIDATE': jina,
                    'SEX': mwa['Jinsia (M/F)'],
                    'EXAM NO.': mwa['Namba ya Usajili'],
                    'SCHOOL NAME': shule_info['shule'].split()[0],
                    'TOTAL REGISTERED SUBJECTS': len(m_yake)
                }
                for s in masomo_shule:
                    stari[s] = "_" if s in m_yake else ""
                rows_cal.append(stari)
            df_cal_data = pd.DataFrame(rows_cal)
            st.dataframe(df_cal_data, use_container_width=True, hide_index=True)
    else:
        st.warning("Hakuna wanafunzi kwenye mfumo.")
