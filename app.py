import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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
    # Kama hajafanya somo hata moja kabisa
    if valid_subjects == 0:
        return 'ABS', 0
    # Kama amefanya lakini masomo ni pungufu ya 7
    if valid_subjects < 7:
        return 'INC', sum(pointi_za_masomo)
    
    pointi_za_masomo.sort()
    pointi_saba = sum(pointi_za_masomo[:7])
    
    if pointi_saba >= 7 and pointi_saba <= 17: return 'I', pointi_saba
    elif pointi_saba <= 21: return 'II', pointi_saba
    elif pointi_saba <= 25: return 'III', pointi_saba
    elif pointi_saba <= 33: return 'IV', pointi_saba
    else: return '0', pointi_saba

# ------------------------------------------------------------------
# 2. SEAMS NA KUTUNZA DATA KWA KILA DARASA (SESSION STATE)
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
    st.session_state[f'masomo_shule_{darasa_id}'] = ['HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS', 'COMPUTER SCIENCE']

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

shule_info = st.session_state[f'shule_info_{darasa_id}']
masomo_shule = st.session_state[f'masomo_shule_{darasa_id}']
remarks_dict = st.session_state[f'remarks_dict_{darasa_id}']
wanafunzi_db = st.session_state[f'wanafunzi_db_{darasa_id}']
masomo_wanafunzi = st.session_state[f'masomo_wanafunzi_{darasa_id}']

# Hakikisha wanafunzi wote wana masomo yao
for jina in wanafunzi_db['Jina la Mwanafunzi'].tolist():
    if jina not in masomo_wanafunzi:
        masomo_wanafunzi[jina] = masomo_shule.copy()

# Helper function kuhesabu wastani unaoumia pande zote mbili au mmoja
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
    elif pin_ingizwa != "":
        st.sidebar.error("PIN Si Sahihi!")

# Orodha ya Menu Kuu
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

# KIPENGELE 0: KUHUSU MFUMO
if chaguo == "0. Kuhusu Mfumo":
    st.header(f"Mfumo wa Kuchakata Matokeo - {kidato_kilichochaguliwa}")
    st.info(f"Hivi sasa unashughulikia data za darasa la: **{kidato_kilichochaguliwa}**.")

# KIPENGELE 1: TAARIFA BINAFSI ZA MTIHANI (ADMIN ONLY)
elif chaguo == "1. Taarifa za Shule na Mtihani" and is_admin:
    st.header("1. Taarifa za Shule na Mtihani")
    with st.form("taarifa_shule_form"):
        shule_info["wizara"] = st.text_input("Wizara", shule_info["wizara"])
        shule_info["idara"] = st.text_input("Idara Kuu (k.mf RALG)", shule_info["idara"])
        shule_info["mkoa"] = st.text_input("Mkoa", shule_info["mkoa"])
        shule_info["wilaya"] = st.text_input("Wilaya / Halmashauri", shule_info["wilaya"])
        shule_info["shule"] = st.text_input("Jina la Shule", shule_info["shule"])
        shule_info["namba_shule"] = st.text_input("Namba ya Kituo (Centre No)", shule_info["namba_shule"])
        shule_info["aina_mtihani"] = st.text_input("Aina ya Mtihani", shule_info["aina_mtihani"])
        shule_info["mwaka"] = st.text_input("Mwaka / Kipindi (k.mf. MAY-2026)", shule_info["mwaka"])
        
        st.subheader("Badili Maelezo ya Gredi (Remarks)")
        for key in remarks_dict.keys():
            remarks_dict[key] = st.text_input(f"Maelezo ya Gredi {key}:", remarks_dict[key])
            
        hifadhi_taarifa = st.form_submit_button("Hifadhi Taarifa Zote")
        if hifadhi_taarifa:
            st.success("🎉 Taarifa za shule na gredi zimehifadhiwa kikamilifu kwenye mfumo!")

# KIPENGELE 2: USAJILI WA MASOMO YA SHULE (ADMIN ONLY)
elif chaguo == "2. Usajili wa Masomo ya Shule (Hadi 20)" and is_admin:
    st.header("2. Usajili wa Masomo ya Shule")
    with st.form("masomo_shule_form"):
        masomo_maandishi = st.text_area("Ingiza masomo yote yakitenganishwa kwa alama ya mkato (,):", ", ".join(masomo_shule))
        wasilisha_masomo = st.form_submit_button("Hifadhi Orodha ya Masomo")
        
        if wasilisha_masomo:
            masomo_yaliyosafishwa = [m.strip().upper() for m in masomo_maandishi.split(",") if m.strip()]
            if len(masomo_yaliyosafishwa) > 20:
                st.error("Umevuka kikomo! Mfumo unaruhusu mwisho masomo 20 pekee.")
            else:
                st.session_state[f'masomo_shule_{darasa_id}'] = masomo_yaliyosafishwa
                st.success(f"🎉 Masomo yamehifadhiwa. Jumla ya masomo ya shule: {len(masomo_yaliyosafishwa)}")

# KIPENGELE 3: SAJILI MAJINA YA WANAFUNZI (ADMIN ONLY)
elif chaguo == "3. Sajili Majina ya Wanafunzi" and is_admin:
    st.header("3. Sajili Wanafunzi")
    tab1, tab2 = st.tabs(["Fomu ya Usajili", "Kupandisha Excel"])
    
    with tab1:
        with st.form(f"fomu_mwanafunzi_{darasa_id}"):
            mpya_jina = st.text_input("Jina Kamili la Mwanafunzi:").upper()
            mpya_jinsia = st.selectbox("Jinsia:", ["M", "F"])
            mpya_namba = st.text_input("Namba ya Usajili:", f"{shule_info['namba_shule']}/{str(len(wanafunzi_db)+1).zfill(4)}")
            wasilisha = st.form_submit_button("Hifadhi Mwanafunzi")
            if wasilisha and mpya_jina:
                mpya_row = pd.DataFrame([[mpya_jina, mpya_jinsia, mpya_namba]], columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
                st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.concat([wanafunzi_db, mpya_row], ignore_index=True)
                st.success(f"🎉 {mpya_jina} amesajiliwa na kuhifadhiwa!")
                st.rerun()

    with tab2:
        st.subheader("Pakua na Upakie Template ya Excel")
        template_df = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
        template_df.loc[0] = ["JUMA HAMISI", "M", f"{shule_info['namba_shule']}/0001"]
        
        buffer_template = io.BytesIO()
        with pd.ExcelWriter(buffer_template, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False)
        
        st.download_button(label="⬇️ Pakua Template ya Excel Hapa", data=buffer_template.getvalue(), file_name=f"Template_Wanafunzi_{darasa_id}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        uploaded_file = st.file_uploader("Pandisha Excel iliyojazwa (.xlsx):", type=["xlsx"])
        
        if uploaded_file is not None:
            try:
                df_up = pd.read_excel(uploaded_file)
                df_up.columns = [str(c).strip() for c in df_up.columns]
                if 'Jina la Mwanafunzi' in df_up.columns and 'Jinsia (M/F)' in df_up.columns:
                    df_up['Jina la Mwanafunzi'] = df_up['Jina la Mwanafunzi'].astype(str).str.upper().str.strip()
                    df_up['Jinsia (M/F)'] = df_up['Jinsia (M/F)'].astype(str).str.upper().str.strip()
                    if 'Namba ya Usajili' not in df_up.columns:
                        df_up['Namba ya Usajili'] = [f"{shule_info['namba_shule']}/{str(i+1).zfill(4)}" for i in range(len(df_up))]
                    st.session_state[f'wanafunzi_db_{darasa_id}'] = df_up[['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili']].dropna(subset=['Jina la Mwanafunzi']).reset_index(drop=True)
                    st.success("🎉 Wanafunzi kutoka Excel wamehifadhiwa kikamilifu!")
                    st.rerun()
            except Exception as e:
                st.error(f"Hitilafu: {e}")

    st.write("---")
    st.subheader("Orodha ya Wanafunzi Waliosajiliwa")
    wanafunzi_onyesho = st.session_state[f'wanafunzi_db_{darasa_id}'].copy()
    wanafunzi_onyesho.insert(0, 'S/N', range(1, len(wanafunzi_onyesho) + 1))
    st.dataframe(wanafunzi_onyesho, use_container_width=True, hide_index=True)

# KIPENGELE 4: KUMSAJILIA MWANAFUNZI MASOMO (ADMIN ONLY)
elif chaguo == "4. Kumsajilia Mwanafunzi Masomo" and is_admin:
    st.header("4. Kusajili Masomo Maalum ya Wanafunzi")
    if len(names_list) == 0:
        st.warning("Tafadhali sajili majina kwanza kwenye kipengele namba 3.")
    else:
        tab_direct, tab_excel = st.tabs(["Njia ya Kwanza: Moja kwa Moja", "Njia ya Pili: Kupitia Excel"])
        
        with tab_direct:
            mwanafunzi_sel = st.selectbox("Chagua Mwanafunzi:", names_list)
            masomo_yake = st.multiselect(f"Chagua Masomo ya {mwanafunzi_sel}:", masomo_shule, default=masomo_wanafunzi.get(mwanafunzi_sel, masomo_shule))
            if st.button(f"Hifadhi Masomo ya {mwanafunzi_sel}"):
                st.session_state[f'masomo_wanafunzi_{darasa_id}'][mwanafunzi_sel] = masomo_yake
                st.success(f"🎉 Masomo ya mwanafunzi {mwanafunzi_sel} yamehifadhiwa vizuri!")
                
        with tab_excel:
            st.subheader("Kusajili Masomo kwa Excel")
            rows_template = []
            for jina in names_list:
                m_yake = masomo_wanafunzi.get(jina, masomo_shule)
                stari = {'Jina la Mwanafunzi': jina}
                for s in masomo_shule:
                    stari[s] = "NDIO" if s in m_yake else "HAPANA"
                rows_template.append(stari)
            df_m_template = pd.DataFrame(rows_template)
            
            buffer_m = io.BytesIO()
            with pd.ExcelWriter(buffer_m, engine='openpyxl') as writer:
                df_m_template.to_excel(writer, index=False)
            
            st.download_button(label="⬇️ Pakua Template ya Excel ya Masomo", data=buffer_m.getvalue(), file_name=f"Usajili_Masomo_Template_{darasa_id}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            file_m_up = st.file_uploader("Pandisha Excel ya Usajili wa Masomo (.xlsx):", type=["xlsx"], key="masomo_excel_up")
            if file_m_up is not None:
                try:
                    df_m_up = pd.read_excel(file_m_up)
                    df_m_up.columns = [str(c).strip().upper() for c in df_m_up.columns]
                    
                    for _, row in df_m_up.iterrows():
                        jina_mwa = str(row['JINA LA MWANAFUNZI']).strip().upper()
                        if jina_mwa in names_list:
                            masomo_yaliyochaguliwa = []
                            for s in masomo_shule:
                                if s in df_m_up.columns and str(row[s]).strip().upper() == "NDIO":
                                    masomo_yaliyochaguliwa.append(s)
                            st.session_state[f'masomo_wanafunzi_{darasa_id}'][jina_mwa] = masomo_yaliyochaguliwa
                    st.success("🎉 Usajili wa masomo ya wanafunzi kutoka kwenye Excel umehifadhiwa kikamilifu!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Hitilafu wakati wa kusoma Excel ya masomo: {e}")

# KIPENGELE 5 & 6: KUJAZA ALAMA ZA MAJARIBIO / MITIHANI
elif chaguo in ["5. Kujaza Alama za Majaribio (100%)", "6. Kujaza Alama za Mitihani (100%)"]:
    is_majaribio = "Majaribio" in chaguo
    db_key = f'alama_majaribio_db_{darasa_id}' if is_majaribio else f'alama_mitihani_db_{darasa_id}'
    
    st.header(f"Kujaza Alama za { 'Majaribio' if is_majaribio else 'Mitihani' } (Upeo 100%)")
    
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa.")
    else:
        somo_sel = st.selectbox("Chagua Somo la Kujaza Alama:", masomo_shule)
        wanafunzi_wa_somo = [jina for jina in names_list if somo_sel in masomo_wanafunzi.get(jina, masomo_shule)]
        
        if not wanafunzi_wa_somo:
            st.warning(f"Hakuna mwanafunzi hata mmoja aliyesajiliwa kwenye somo la {somo_sel}.")
        else:
            st.info(f"Inaonyesha wanafunzi **{len(wanafunzi_wa_somo)}** waliosajiliwa somo la **{somo_sel}** pekee.")
            
            current_db = st.session_state[db_key]
            rows_to_edit = []
            for idx, jina in enumerate(wanafunzi_wa_somo):
                zilizopo = current_db[(current_db['Jina la Mwanafunzi'] == jina) & (current_db['Somo'] == somo_sel)]
                alama_iliyopo = zilizopo['Alama'].values[0] if not zilizopo.empty else np.nan
                
                m_info = wanafunzi_db[wanafunzi_db['Jina la Mwanafunzi'] == jina].iloc[0]
                rows_to_edit.append({
                    'S/N': idx + 1,
                    'Jina la Mwanafunzi': jina,
                    'Jinsia (M/F)': m_info['Jinsia (M/F)'],
                    'Namba ya Usajili': m_info['Namba ya Usajili'],
                    'Alama (100%)': alama_iliyopo
                })
            df_editor = pd.DataFrame(rows_to_edit)
            
            edited_df = st.data_editor(df_editor, use_container_width=True, num_rows="fixed", disabled=['S/N','Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'], hide_index=True)
            
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
                st.success(f"🎉 Alama zote za somo la {somo_sel} zimehifadhiwa kikamilifu kwenye mfumo!")

# KIPENGELE 7: WASTANI WA MAJARIBIO NA MITIHANI
elif chaguo == "7. Wastani wa Majaribio & Mitihani":
    st.header("7. Wastani wa Alama (Majaribio & Mitihani)")
    db_maj = st.session_state[f'alama_majaribio_db_{darasa_id}']
    db_mit = st.session_state[f'alama_mitihani_db_{darasa_id}']
    
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa.")
    else:
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
                # Kama hana alama yoyote, ibaki wazi kabisa ("")
                stari[s] = avg_val if avg_val is not None else ""
                
            rows_avg.append(stari)
            
        st.dataframe(pd.DataFrame(rows_avg), use_container_width=True, hide_index=True)

# KIPENGELE 10: MATOKEO YA NECTA FORMAT & SUMMARY
elif chaguo == "10. Matokeo ya NECTA Format & Summary":
    st.header("10. Broadsheet ya Matokeo (NECTA Format)")
    db_maj = st.session_state[f'alama_majaribio_db_{darasa_id}']
    db_mit = st.session_state[f'alama_mitihani_db_{darasa_id}']
    
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
            # Kupanga kwa Division (I, II, III, IV, 0, INC, ABS)
            df_final.insert(0, 'S/N', range(1, len(df_final) + 1))
            df_final['POSITION'] = df_final['S/N']
            st.dataframe(df_final, use_container_width=True, hide_index=True)

# KIPENGELE 11: RIPOTI BINAFSI YA MWANAFUNZI (PDF)
elif chaguo == "11. Ripoti Binafsi ya Mwanafunzi (PDF)":
    st.header("11. Pakua Ripoti ya Mwanafunzi Binafsi / Shule Nzima")
    db_maj = st.session_state[f'alama_majaribio_db_{darasa_id}']
    db_mit = st.session_state[f'alama_mitihani_db_{darasa_id}']

    if len(names_list) == 0:
        st.warning("Tafadhali hakikisha majina yamejazwa.")
    else:
        def andaa_data_mwanafunzi(jina_mwa):
            data_somo_pdf = [["Somo", "Majaribio", "Mtihani", "Wastani", "Gredi", "Maelezo"]]
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

        with col_p2:
            st.subheader("Pakua Ripoti za Shule Nzima")
            if st.button("Tengeneza PDF ya Shule Nzima"):
                buffer_all = io.BytesIO()
                doc_all = SimpleDocTemplate(buffer_all, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
                story_all = []
                styles = getSampleStyleSheet()
                style_head = ParagraphStyle('HHeadAll', parent=styles['Heading2'], alignment=1, spaceAfter=4)
                style_normal = ParagraphStyle('NHeadAll', parent=styles['Normal'], spaceAfter=12, fontSize=11)
                
                for jina_all in names_list:
                    story_all.append(Paragraph(f"<b>{shule_info['wizara']}</b>", style_head))
                    story_all.append(Paragraph(f"<b>{shule_info['shule']}</b>", style_head))
                    story_all.append(Spacer(1, 10))
                    
                    m_info = wanafunzi_db[wanafunzi_db['Jina la Mwanafunzi'] == jina_all].iloc[0]
                    story_all.append(Paragraph(f"<b>Mwanafunzi:</b> {jina_all} | <b>Jinsia:</b> {m_info['Jinsia (M/F)']} | <b>Namba:</b> {m_info['Namba ya Usajili']}", style_normal))
                    
                    data_somo, pts, div = andaa_data_mwanafunzi(jina_all)
                    t = Table(data_somo, colWidths=[160, 70, 70, 70, 50, 100])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('GRID', (0,0), (-1,-1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
                    ]))
                    story_all.append(t)
                    story_all.append(Spacer(1, 10))
                    show_pts_all = pts if div not in ['ABS', 'INC'] else '-'
                    story_all.append(Paragraph(f"<b>JUMLA YA POINTI:</b> {show_pts_all} | <b>DIVISION:</b> {div}", style_normal))
                    story_all.append(PageBreak())
                
                doc_all.build(story_all)
                buffer_all.seek(0)
                st.download_button(label="Pakua PDF ya Shule Nzima", file_name=f"Ripoti_Shule_Nzima_{darasa_id}.pdf", data=buffer_all.getvalue(), mime="application/pdf")

# KIPENGELE 12: PAKUA FOMU ZA CAL NA ISAL
elif chaguo == "12. Pakua Fomu za CAL na ISAL":
    st.header("12. Pakua Fomu Rasmi za CAL na ISAL (NECTA Format)")
    
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa kwenye mfumo hadi sasa.")
    else:
        tab_cal, tab_isal = st.tabs(["📊 PAKUA CAL (Jumla)", "📝 PAKUA ISAL (Kila Somo)"])
        
        # 1. ZALISHA FOMU YA CAL
        with tab_cal:
            st.write("Fomu hii inajumuisha masomo yote kwa pamoja kuonesha mtahiniwa amesajiliwa masomo gani.")
            
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
                    
                stari['SIGNATURE'] = ""
                rows_cal.append(stari)
                
            df_cal_data = pd.DataFrame(rows_cal)
            st.dataframe(df_cal_data, use_container_width=True, hide_index=True)
            
            buffer_cal = io.BytesIO()
            with pd.ExcelWriter(buffer_cal, engine='openpyxl') as writer:
                hdr_rows = [
                    [shule_info['wizara'], "", "", "", ""],
                    [shule_info['idara'], "", "", "", ""],
                    [shule_info['mkoa'], "", "", "", ""],
                    [shule_info['wilaya'], "", "", "", ""],
                    [f"{shule_info['aina_mtihani']} {shule_info['mwaka']}", "", "", "", ""],
                    [f"CENTER NO: {shule_info['namba_shule']}      CENTER NAME: {shule_info['shule']}", "", "", "", ""],
                    ["COLLECTIVE ATTENDANCE LIST (CAL)", "", "", "", ""],
                    ["", "", "", "", ""]
                ]
                df_hdr = pd.DataFrame(hdr_rows)
                
                df_hdr.to_excel(writer, index=False, header=False, sheet_name="CAL")
                df_cal_data.to_excel(writer, index=False, startrow=8, sheet_name="CAL")
                
                wb = writer.book
                for sheet in wb.worksheets:
                    sheet.views.sheetView[0].tabSelected = False
                wb.worksheets[0].views.sheetView[0].tabSelected = True
                wb.active = 0
                
            st.download_button(
                label="⬇️ Pakua Fomu ya CAL (Excel)",
                data=buffer_cal.getvalue(),
                file_name=f"CAL_{darasa_id}_{shule_info['namba_shule']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        # 2. ZALISHA FOMU YA ISAL
        with tab_isal:
            st.write("Chagua somo husika ili kuzalisha fomu ya mahudhurio ya chumbani kwa ajili ya somo hilo pekee.")
            somo_isal = st.selectbox("Chagua Somo la ISAL:", masomo_shule)
            
            wanafunzi_wa_somo = [jina for jina in names_list if somo_isal in masomo_wanafunzi.get(jina, masomo_shule)]
            
            if not wanafunzi_wa_somo:
                st.warning(f"Hakuna wanafunzi waliosajiliwa kwenye somo la {somo_isal}")
            else:
                rows_isal = []
                for idx, jina in enumerate(wanafunzi_wa_somo):
                    m_info = wanafunzi_db[wanafunzi_db['Jina la Mwanafunzi'] == jina].iloc[0]
                    rows_isal.append({
                        'S/N': idx + 1,
                        'NAME OF CANDIDATE': jina,
                        'SEX': m_info['Jinsia (M/F)'],
                        'EXAM NO.': m_info['Namba ya Usajili'],
                        'SIGNATURE': ""
                    })
                df_isal_data = pd.DataFrame(rows_isal)
                st.dataframe(df_isal_data, use_container_width=True, hide_index=True)
                
                buffer_isal = io.BytesIO()
                with pd.ExcelWriter(buffer_isal, engine='openpyxl') as writer:
                    hdr_rows_isal = [
                        [shule_info['wizara'], "", "", ""],
                        [shule_info['idara'], "", "", ""],
                        [shule_info['mkoa'], "", "", ""],
                        [shule_info['wilaya'], "", "", ""],
                        [f"{shule_info['aina_mtihani']} {shule_info['mwaka']}", "", "", ""],
                        ["INDIVIDUAL SUBJECT ATTENDANCE LIST (ISAL)", "", "", ""],
                        [f"CLASS: {kidato_kilichochaguliwa}    CENTER NO: {shule_info['namba_shule']}    CENTER NAME: {shule_info['shule']}", "", "", ""],
                        [f"SUBJECT NAME: {somo_isal}           DATE: ________", "", "", ""],
                        ["", "", "", ""]
                    ]
                    df_hdr_isal = pd.DataFrame(hdr_rows_isal)
                    
                    df_hdr_isal.to_excel(writer, index=False, header=False, sheet_name="ISAL")
                    df_isal_data.to_excel(writer, index=False, startrow=9, sheet_name="ISAL")
                    
                    wb_isal = writer.book
                    for sheet in wb_isal.worksheets:
                        sheet.views.sheetView[0].tabSelected = False
                    wb_isal.worksheets[0].views.sheetView[0].tabSelected = True
                    wb_isal.active = 0
                    
                st.download_button(
                    label=f"⬇️ Pakua Fomu ya ISAL - {somo_isal} (Excel)",
                    data=buffer_isal.getvalue(),
                    file_name=f"ISAL_{somo_isal}_{darasa_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
