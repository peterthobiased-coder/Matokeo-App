import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ------------------------------------------------------------------
# 1. Mipangilio ya Ukurasa na Caching ya Vigezo vya NECTA
# ------------------------------------------------------------------
st.set_page_config(page_title="Mfumo wa Matokeo Kidato cha 1-4", layout="wide")

@st.cache_data
def calculate_grade_and_points(score):
    if pd.isna(score) or score == '': return None, None
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
def calculate_division(total_points, valid_subjects, total_registered_subjects):
    if total_registered_subjects == 0 or valid_subjects == 0:
        return 'ABS'
    if valid_subjects < 7:
        return 'INC'
    if total_points >= 7 and total_points <= 17: return 'I'
    elif total_points <= 21: return 'II'
    elif total_points <= 25: return 'III'
    elif total_points <= 33: return 'IV'
    else: return '0'

# ------------------------------------------------------------------
# 2. Uchaguzi wa Kidato na Kutenganisha Data (Sidebar)
# ------------------------------------------------------------------
st.sidebar.title("UCHAGUZI WA DARASA")
kidato_kilichochaguliwa = st.sidebar.selectbox(
    "Chagua Kidato:", 
    ["KIDATO CHA KWANZA", "KIDATO CHA PILI", "KIDATO CHA TATU", "KIDATO CHA NNE"]
)

# Tunatengeneza kitambulisho cha kipekee (ID) kwa ajili ya kila darasa
darasa_id = kidato_kilichochaguliwa.replace(" ", "_")

# Kila darasa linapewa stoo yake ya data ndani ya session_state
if f'shule_info_{darasa_id}' not in st.session_state:
    st.session_state[f'shule_info_{darasa_id}'] = {
        "wizara": "PRIME MINISTER'S OFFICE", "mkoa": "MWANZA", 
        "wilaya": "BUCHOSA DISTRICT COUNCIL", "shule": "CHEMA SECONDARY SCHOOL", 
        "namba_shule": "S7647", "aina_mtihani": f"MTIHANI WA UTAMBALI {kidato_kilichochaguliwa}", "mwaka": "AUGUST 2026"
    }

if f'masomo_{darasa_id}' not in st.session_state:
    st.session_state[f'masomo_{darasa_id}'] = ['CIVICS', 'HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS']

if f'wanafunzi_db_{darasa_id}' not in st.session_state:
    st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])

if f'df_maj_{darasa_id}' not in st.session_state:
    st.session_state[f'df_maj_{darasa_id}'] = pd.DataFrame()

if f'df_mit_{darasa_id}' not in st.session_state:
    st.session_state[f'df_mit_{darasa_id}'] = pd.DataFrame()

# ------------------------------------------------------------------
# 3. Ulinzi na Menu za Mfumo
# ------------------------------------------------------------------
st.sidebar.write("---")
st.sidebar.title("MIPANGILIO YA USALAMA")
hali_ya_mtumiaji = st.sidebar.selectbox("Aina ya Mtumiaji:", ["Mwalimu (Jaza Alama Tu)", "Admin (Mkuu wa Shule)"])

is_admin = False
if hali_ya_mtumiaji == "Admin (Mkuu wa Shule)":
    pin_ingizwa = st.sidebar.text_input("Ingiza PIN ya Admin:", type="password")
    if pin_ingizwa == "1234":  # PIN ya kuingia
        is_admin = True
        st.sidebar.success("Umeingia kama Admin!")
    elif pin_ingizwa != "":
        st.sidebar.error("PIN Si Sahihi!")

# Kujenga orodha ya menu kulingana na darasa lililochaguliwa
orodha_ya_menu = ["0. Kuhusu Darasa Hili"]
if is_admin:
    orodha_ya_menu.extend([
        "1. Taarifa za Shule na Mtihani",
        "2. Sajili Masomo ya Darasa",
        "3. Sajili Majina ya Wanafunzi"
    ])

orodha_ya_menu.extend([
    "4. Kujaza Alama za Majaribio (100%)",
    "5. Kujaza Alama za Mitihani (100%)",
    "6. Matokeo na Ripoti ya NECTA Format"
])

st.sidebar.write("---")
st.sidebar.title("MENU KUU")
chaguo = st.sidebar.radio("Nenda kwenye kipengele:", orodha_ya_menu)

# Data mahususi kwa ajili ya darasa lililochaguliwa kwa sasa
info_sasa = st.session_state[f'shule_info_{darasa_id}']
masomo_sasa = st.session_state[f'masomo_{darasa_id}']
wanafunzi_sasa = st.session_state[f'wanafunzi_db_{darasa_id}']
names_list = wanafunzi_sasa['Jina la Mwanafunzi'].tolist()

# ------------------------------------------------------------------
# INTERFACE YA VIPENGELE
# ------------------------------------------------------------------

if chaguo == "0. Kuhusu Darasa Hili":
    st.header(f"Mfumo wa Kuchakata Matokeo - {kidato_kilichochaguliwa}")
    st.write(f"""
    Karibu kwenye eneo la **{kidato_kilichochaguliwa}**. Hapa unaweza kusimamia masomo, majina, na alama za darasa hili pekee.
    
    *   **Kumbuka:** Data unazojaza sasa hivi zinakaa kwenye kumbukumbu ya muda ya kivinjari. Ukichagua kidato kingine kwenye sidebar, data zako hazifutiki, zinarudi kule ulikozicha.
    *   **Walimu:** Badili aina ya mtumiaji kuwa 'Mwalimu' kisha nenda kipengele namba 4 au 5 kujaza alama.
    """)

elif chaguo == "1. Taarifa za Shule na Mtihani" and is_admin:
    st.header(f"1. Mipangilio ya Kituo na Mtihani - {kidato_kilichochaguliwa}")
    info_sasa["wizara"] = st.text_input("Wizara", info_sasa["wizara"])
    info_sasa["mkoa"] = st.text_input("Mkoa", info_sasa["mkoa"])
    info_sasa["wilaya"] = st.text_input("Wilaya / Halmashauri", info_sasa["wilaya"])
    info_sasa["shule"] = st.text_input("Jina la Shule", info_sasa["shule"])
    info_sasa["namba_shule"] = st.text_input("Namba ya Kituo", info_sasa["namba_shule"])
    info_sasa["aina_mtihani"] = st.text_input("Aina ya Mtihani", info_sasa["aina_mtihani"])
    info_sasa["mwaka"] = st.text_input("Mwaka / Kipindi", info_sasa["mwaka"])
    st.session_state[f'shule_info_{darasa_id}'] = info_sasa
    st.success(f"Imehifadhiwa kwa ajili ya {kidato_kilichochaguliwa}!")

elif chaguo == "2. Sajili Masomo ya Darasa" and is_admin:
    st.header(f"2. Mipangilio ya Masomo Yanayofundishwa - {kidato_kilichochaguliwa}")
    masomo_txt = st.text_area("Ingiza masomo yakitenganishwa kwa alama ya mkato (,):", ", ".join(masomo_sasa))
    if st.button("Hifadhi Masomo"):
        yaliyosafishwa = [m.strip().upper() for m in masomo_txt.split(",") if m.strip()]
        st.session_state[f'masomo_{darasa_id}'] = yaliyosafishwa
        st.success(f"Orodha ya masomo ya {kidato_kilichochaguliwa} imesasishwa!")

elif chaguo == "3. Sajili Majina ya Wanafunzi" and is_admin:
    st.header(f"3. Usajili wa Wanafunzi wa {kidato_kilichochaguliwa}")
    
    with st.form("fomu_wanafunzi"):
        jina = st.text_input("Jina la Mwanafunzi:").upper()
        jinsia = st.selectbox("Jinsia:", ["M", "F"])
        namba = st.text_input("Namba ya Usajili:", f"{info_sasa['namba_shule']}/{str(len(names_list)+1).zfill(4)}")
        wasilisha = st.form_submit_button("Sajili Mwanafunzi")
        
        if wasilisha and jina:
            mpya = pd.DataFrame([[jina, jinsia, namba]], columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
            st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.concat([st.session_state[f'wanafunzi_db_{darasa_id}'], mpya], ignore_index=True)
            st.rerun()
            
    st.subheader(f"Orodha ya Wanafunzi Waliosajiliwa ({kidato_kilichochaguliwa})")
    st.dataframe(st.session_state[f'wanafunzi_db_{darasa_id}'], use_container_width=True)

elif chaguo == "4. Kujaza Alama za Majaribio (100%)":
    st.header(f"4. Alama za Majaribio (0-100) - {kidato_kilichochaguliwa}")
    if len(names_list) == 0:
        st.warning(f"Tafadhali sajili wanafunzi wa {kidato_kilichochaguliwa} kwanza kwenye kipengele cha Admin.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (100%)" for s in masomo_sasa]
        df_maj = st.session_state[f'df_maj_{darasa_id}']
        
        if df_maj.empty or not all(c in df_maj.columns for c in cols):
            df_maj = st.session_state[f'wanafunzi_db_{darasa_id}'].copy()
            for s in masomo_sasa:
                df_maj[f"{s} (100%)"] = np.nan
                
        edited = st.data_editor(df_maj[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama za Majaribio"):
            st.session_state[f'df_maj_{darasa_id}'] = edited
            st.success("Alama za majaribio zimehifadhiwa kwenye mfumo!")

elif chaguo == "5. Kujaza Alama za Mitihani (100%)":
    st.header(f"5. Alama za Mitihani ya Mwisho (0-100) - {kidato_kilichochaguliwa}")
    if len(names_list) == 0:
        st.warning(f"Tafadhali sajili wanafunzi wa {kidato_kilichochaguliwa} kwanza kwenye kipengele cha Admin.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (100%)" for s in masomo_sasa]
        df_mit = st.session_state[f'df_mit_{darasa_id}']
        
        if df_mit.empty or not all(c in df_mit.columns for c in cols):
            df_mit = st.session_state[f'wanafunzi_db_{darasa_id}'].copy()
            for s in masomo_sasa:
                df_mit[f"{s} (100%)"] = np.nan
                
        edited = st.data_editor(df_mit[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama za Mitihani"):
            st.session_state[f'df_mit_{darasa_id}'] = edited
            st.success("Alama za mitihani zimehifadhiwa kwenye mfumo!")

elif chaguo == "6. Matokeo na Ripoti ya NECTA Format":
    st.header(f"6. Ripoti ya Ufaulu wa Jumla (Broadsheet) - {kidato_kilichochaguliwa}")
    
    df_maj = st.session_state[f'df_maj_{darasa_id}']
    df_mit = st.session_state[f'df_mit_{darasa_id}']
    
    if df_maj.empty or df_mit.empty:
        st.error("Tafadhali jaza na uhifadhi alama za majaribio na mitihani kwanza ili kuona ripoti.")
    else:
        st.markdown(f"<h3 style='text-align: center;'>{info_sasa['shule']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{info_sasa['aina_mtihani']} ({info_sasa['mwaka']})</h4>", unsafe_allow_html=True)
        
        orodha_ripoti = []
        for idx, row in st.session_state[f'wanafunzi_db_{darasa_id}'].iterrows():
            jina = row['Jina la Mwanafunzi']
            taarifa = {'S/N': idx + 1, 'NAME OF CANDIDATE': jina, 'SEX': row['Jinsia (M/F)'], 'INDEX NO': row['Namba ya Usajili']}
            
            pointi_za_masomo = []
            jumla_alama = 0.0
            masomo_yaliyofanywa = 0
            
            for somo in masomo_sasa:
                cwt = pd.to_numeric(df_maj.loc[idx, f"{somo} (100%)"], errors='coerce') if idx in df_maj.index else np.nan
                eet = pd.to_numeric(df_mit.loc[idx, f"{somo} (100%)"], errors='coerce') if idx in df_mit.index else np.nan
                
                cwt_val = float(cwt) if not pd.isna(cwt) else 0.0
                eet_val = float(eet) if not pd.isna(eet) else 0.0
                
                # Formula ya kukokotoa Wastani (CA 40% + Exam 60%) au (CA+Exam)/2
                wastani = round((cwt_val + eet_val) / 2, 1)
                daraja, pointi = calculate_grade_and_points(wastani)
                
                taarifa[f"{somo} GR"] = daraja if daraja else "-"
                
                if daraja:
                    pointi_za_masomo.append(pointi)
                    jumla_alama += wastani
                    masomo_yaliyofanywa += 1
            
            # Mfumo wa NECTA wa kupata Division kwa masomo 7 bora
            if masomo_yaliyofanywa >= 7:
                pointi_za_masomo.sort()
                pointi_saba = sum(pointi_za_masomo[:7])
                div = calculate_division(pointi_saba, masomo_yaliyofanywa, len(masomo_sasa))
            else:
                pointi_saba = sum(pointi_za_masomo)
                div = "INC"
                
            taarifa['POINTS'] = pointi_saba
            taarifa['DIV'] = div
            taarifa['AVG'] = round(jumla_alama / masomo_yaliyofanywa, 1) if masomo_yaliyofanywa > 0 else 0
            
            orodha_ripoti.append(taarifa)
            
        df_final = pd.DataFrame(orodha_ripoti)
        st.dataframe(df_final, use_container_width=True)
