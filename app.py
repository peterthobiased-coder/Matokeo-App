import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ------------------------------------------------------------------
# 1. Mipangilio na Caching
# ------------------------------------------------------------------
st.set_page_config(page_title="Mfumo wa Matokeo O-Level", layout="wide")

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

# Initialize session states
if 'shule_info' not in st.session_state:
    st.session_state.shule_info = {"wizara": "PRIME MINISTER'S OFFICE", "mkoa": "MWANZA", "wilaya": "BUCHOSA DISTRICT COUNCIL", "shule": "CHEMA SECONDARY SCHOOL", "namba_shule": "S7647", "aina_mtihani": "FORM FOUR LAKE ZONE MOCK EXAMINATION", "mwaka": "MAY 2026"}

if 'masomo_shule' not in st.session_state:
    st.session_state.masomo_shule = ['CIVICS', 'HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS', 'LITERATURE IN ENGLISH']

if 'remarks_dict' not in st.session_state:
    st.session_state.remarks_dict = {'A': 'Bora Sana', 'B': 'Bora', 'C': 'Vizuri', 'D': 'Inaridhisha', 'F': 'Imefeli'}

if 'wanafunzi_db' not in st.session_state:
    st.session_state.wanafunzi_db = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])

if 'masomo_wanafunzi' not in st.session_state:
    st.session_state.masomo_wanafunzi = {}

if 'almar_majaribio' not in st.session_state:
    st.session_state.almar_majaribio = pd.DataFrame()

if 'almar_mitihani' not in st.session_state:
    st.session_state.almar_mitihani = pd.DataFrame()

# ------------------------------------------------------------------
# UDHIBITI WA MILELE (ACCESS CONTROL)
# ------------------------------------------------------------------
st.sidebar.title("MIPANGILIO YA MFUMO")
hali_ya_mtumiaji = st.sidebar.selectbox("Aina ya Mtumiaji:", ["Mwalimu (Jaza Alama Tu)", "Admin (Mkuu wa Shule)"])

is_admin = False
if hali_ya_mtumiaji == "Admin (Mkuu wa Shule)":
    pin_ingizwa = st.sidebar.text_input("Ingiza PIN ya Admin:", type="password")
    if pin_ingizwa == "1234":  # Unaweza kubadili namba hii kuwa PIN yoyote uipendayo
        is_admin = True
        st.sidebar.success("Umeingia kama Admin!")
    elif pin_ingizwa != "":
        st.sidebar.error("PIN Si Sahihi!")

# Kutengeneza orodha ya menu kulingana na aina ya mtumiaji
orodha_ya_menu = ["0. Kuhusu Mfumo"]

if is_admin:
    orodha_ya_menu.extend([
        "1. Taarifa Binafsi za Mtihani",
        "2. Usajili wa Masomo ya Shule (Hadi 20)",
        "3. Sajili Majina ya Wanafunzi",
        "4. Kumsajilia Mwanafunzi Masomo"
    ])

# Menu hizi zinaonekana kwa kila mtu (Walimu na Admin)
orodha_ya_menu.extend([
    "5. Kujaza Alama za Majaribio (100%)",
    "6. Kujaza Alama za Mitihani (100%)",
    "7. Matokeo ya Majaribio Pekee",
    "8. Matokeo ya Mitihani Pekee",
    "9. Matokeo ya Majaribio & Mitihani (Average)",
    "10. Matokeo ya NECTA Format & Summary",
    "11. Ripoti Binafsi ya Mwanafunzi (PDF)"
])

st.sidebar.write("---")
st.sidebar.title("MENU KUU")
chaguo = st.sidebar.radio("Nenda kwenye kipengele:", orodha_ya_menu)

names_list = st.session_state.wanafunzi_db['Jina la Mwanafunzi'].tolist()

# ------------------------------------------------------------------
# KIPENGELE 0: KUHUSU MFUMO
# ------------------------------------------------------------------
if chaguo == "0. Kuhusu Mfumo":
    st.header("0. Mfumo wa Kuchakata Matokeo ya Mtihani (O-Level)")
    st.write("""
    Karibu kwenye mfumo ulioboreshwa wa uchakataji wa matokeo ya mitihani ya kidato cha nne kulingana na muundo wa NECTA.
    
    ### Mwongozo wa Mtumiaji:
    *   **Walimu:** Chagua hali ya '*Mwalimu (Jaza Alama Tu)*' kwenye menu ya kushoto. Utaweza kuona sehemu za kujaza alama (Namba 5 na 6) na kuona/kupakua ripoti za matokeo. Huwezi kubadilisha jina la shule, masomo wala majina ya wanafunzi waliosajiliwa.
    *   **Admin:** Ingiza PIN sahihi ili kufungua menu za usajili wa shule, masomo, na wanafunzi.
    """)

# ------------------------------------------------------------------
# KIPENGELE 1: TAARIFA BINAFSI ZA MTIHANI (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "1. Taarifa Binafsi za Mtihani" and is_admin:
    st.header("1. Taarifa Binafsi za Shule na Mtihani")
    st.session_state.shule_info["wizara"] = st.text_input("Wizara", st.session_state.shule_info["wizara"])
    st.session_state.shule_info["mkoa"] = st.text_input("Mkoa", st.session_state.shule_info["mkoa"])
    st.session_state.shule_info["wilaya"] = st.text_input("Wilaya / Halmashauri", st.session_state.shule_info["wilaya"])
    st.session_state.shule_info["shule"] = st.text_input("Jina la Shule", st.session_state.shule_info["shule"])
    st.session_state.shule_info["namba_shule"] = st.text_input("Namba ya Kituo (Centre No)", st.session_state.shule_info["namba_shule"])
    st.session_state.shule_info["aina_mtihani"] = st.text_input("Aina ya Mtihani", st.session_state.shule_info["aina_mtihani"])
    st.session_state.shule_info["mwaka"] = st.text_input("Mwaka / Mwezi", st.session_state.shule_info["mwaka"])
    
    st.write("---")
    st.subheader("8. Badili Maelezo ya Gredi (Remarks Customization)")
    for key in st.session_state.remarks_dict.keys():
        st.session_state.remarks_dict[key] = st.text_input(f"Maelezo ya Gredi {key}:", st.session_state.remarks_dict[key])
        
    st.success("Taarifa zote zimehifadhiwa kwa usalama!")

# ------------------------------------------------------------------
# KIPENGELE 2: USAJILI WA MASOMO YA SHULE (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "2. Usajili wa Masomo ya Shule (Hadi 20)" and is_admin:
    st.header("2. Usajili na Uhariri wa Masomo (Hadi Masomo 20)")
    
    masomo_maandishi = st.text_area("Ingiza masomo yote yakitenganishwa kwa alama ya mkato (,):", ", ".join(st.session_state.masomo_shule))
    masomo_yaliyosafishwa = [m.strip().upper() for m in masomo_maandishi.split(",") if m.strip()]
    
    if len(masomo_yaliyosafishwa) > 20:
        st.error("Umevuka kikomo! Mfumo unaruhusu kiwango cha mwisho cha masomo 20 pekee.")
    else:
        st.session_state.masomo_shule = masomo_yaliyosafishwa
        st.success(f"Umasajili umekamilika. Jumla ya masomo yaliyosajiliwa: {len(st.session_state.masomo_shule)}")
    
    st.write("Orodha ya masomo kwa sasa:", st.session_state.masomo_shule)

# ------------------------------------------------------------------
# KIPENGELE 3: SAJILI MAJINA YA WANAFUNZI (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "3. Sajili Majina ya Wanafunzi" and is_admin:
    st.header("3. Sajili Majina ya Wanafunzi (Mbinu Mbili)")
    
    tab1, tab2 = st.tabs(["Njia ya 1: Sajili Moja kwa Moja (Fomu)", "Njia ya 2: Kupandisha Excel File"])
    
    with tab1:
        st.subheader("Sajili Mwanafunzi Mmoja mmoja")
        with st.form("fomu_mwanafunzi"):
            mpya_jina = st.text_input("Jina Kamili la Mwanafunzi:").upper()
            mpya_jinsia = st.selectbox("Jinsia:", ["M", "F"])
            mpya_namba = st.text_input("Namba ya Usajili:", f"{st.session_state.shule_info['namba_shule']}/{str(len(st.session_state.wanafunzi_db)+1).zfill(4)}")
            wasilisha = st.form_submit_button("Sajili Mwanafunzi")
            if wasilisha and mpya_jina:
                mpya_row = pd.DataFrame([[mpya_jina, mpya_jinsia, mpya_namba]], columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
                st.session_state.wanafunzi_db = pd.concat([st.session_state.wanafunzi_db, mpya_row], ignore_index=True)
                st.success(f"{mpya_jina} amesajiliwa!")
                st.rerun()

    with tab2:
        st.subheader("Pakua Template nicotine na Upandishe Excel")
        col_a, col_b = st.columns(2)
        with col_a:
            df_temp = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
            df_temp.loc[0] = ["ANNA JUMA", "F", f"{st.session_state.shule_info['namba_shule']}/0001"]
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_temp.to_excel(writer, index=False, sheet_name='Wanafunzi')
            st.download_button(label="Pakua Excel Template ya Majina", data=output.getvalue(), file_name="template_majina.xlsx", mime="application/vnd.ms-excel")
            
        with col_b:
            uploaded_file = st.file_uploader("Pandisha Excel iliyojazwa majina:", type=["xlsx", "xls"])
            if uploaded_file is not None:
                try:
                    df_up = pd.read_excel(uploaded_file)
                    if 'Jina la Mwanafunzi' in df_up.columns and 'Jinsia (M/F)' in df_up.columns:
                        st.session_state.wanafunzi_db = df_up[['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili']].dropna(subset=['Jina la Mwanafunzi']).reset_index(drop=True)
                        st.success(f"Wanafunzi {len(st.session_state.wanafunzi_db)} wameongezwa kwa Excel!")
                    else:
                        st.error("Hakikisha Excel ina nguzo za: 'Jina la Mwanafunzi' na 'Jinsia (M/F)'")
                except Exception as e:
                    st.error(f"Hitilafu: {e}")

    st.subheader("Orodha ya Wanafunzi Waliosajiliwa")
    st.dataframe(st.session_state.wanafunzi_db, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 4: KUMSAJILIA MWANAFUNZI MASOMO (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "4. Kumsajilia Mwanafunzi Masomo" and is_admin:
    st.header("4. Kumsajilia Mwanafunzi Masomo Yake Maalum")
    if len(names_list) == 0:
        st.warning("Tafadhali sajili majina kwanza kwenye kipengele namba 3.")
    else:
        tab_m1, tab_m2 = st.tabs(["Njia ya 1: Sajili kwa Excel (Inashauriwa)", "Njia ya 2: Sajili Mmoja kwa Moja Shuleni"])
        
        with tab_m1:
            st.write("Pakua orodha ya wanafunzi tayari wenye majina yao, kisha weka namba 1 kwa somo mwanafunzi analosoma na 0 kama hasomi.")
            
            df_masomo_temp = st.session_state.wanafunzi_db.copy()
            for somo in st.session_state.masomo_shule:
                df_masomo_temp[somo] = 1
                
            out_m = io.BytesIO()
            with pd.ExcelWriter(out_m, engine='xlsxwriter') as writer:
                df_masomo_temp.to_excel(writer, index=False, sheet_name='Masomo')
            st.download_button(label="Pakua Excel ya Kusajilia Masomo", data=out_m.getvalue(), file_name="sajili_masomo_wanafunzi.xlsx", mime="application/vnd.ms-excel")
            
            st.write("---")
            file_masomo_up = st.file_uploader("Pandisha faili la Excel la masomo baada ya kulijaza:", type=["xlsx", "xls"])
            if file_masomo_up is not None:
                try:
                    df_m_up = pd.read_excel(file_masomo_up)
                    for idx, row in df_m_up.iterrows():
                        jina = row['Jina la Mwanafunzi']
                        masomo_yake = []
                        for somo in st.session_state.masomo_shule:
                            if str(row.get(somo, 1)) == '1' or row.get(somo, 1) == 1:
                                masomo_yake.append(somo)
                        st.session_state.masomo_wanafunzi[jina] = masomo_yake
                    st.success("Usajili wa masomo kwa kutumia Excel umekamilika kikamilifu!")
                except Exception as e:
                    st.error(f"Hitilafu wakati wa kusoma faili: {e}")
                    
        with tab_m2:
            mwanafunzi_sel = st.selectbox("Chagua Mwanafunzi:", names_list)
            if mwanafunzi_sel not in st.session_state.masomo_wanafunzi:
                st.session_state.masomo_wanafunzi[mwanafunzi_sel] = st.session_state.masomo_shule.copy()
            
            masomo_yake = st.multiselect(f"Chagua Masomo ya {mwanafunzi_sel}:", st.session_state.masomo_shule, default=st.session_state.masomo_wanafunzi[mwanafunzi_sel])
            if st.button(f"Hifadhi Masomo ya {mwanafunzi_sel}"):
                st.session_state.masomo_wanafunzi[mwanafunzi_sel] = masomo_yake
                st.success(f"Masomo ya {mwanafunzi_sel} yamehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 5: KUJAZA ALAMA ZA MAJARIBIO (100%) - WALIMU NA ADMIN
# ------------------------------------------------------------------
elif chaguo == "5. Kujaza Alama za Majaribio (100%)":
    st.header("5. Kujaza Alama za Majaribio (Upeo 100%)")
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa kwenye mfumo kwa sasa.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (100%)" for s in st.session_state.masomo_shule]
        if st.session_state.almar_majaribio.empty or not all(c in st.session_state.almar_majaribio.columns for c in cols):
            st.session_state.almar_majaribio = st.session_state.wanafunzi_db.copy()
            for s in st.session_state.masomo_shule:
                st.session_state.almar_majaribio[f"{s} (100%)"] = np.nan
        
        st.info("Ingiza alama za majaribio (0 - 100) kwenye jedwali:")
        edited_maj = st.data_editor(st.session_state.almar_majaribio[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama za Majaribio"):
            st.session_state.almar_majaribio = edited_maj
            st.success("Alama za majaribio zimehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 6: KUJAZA ALAMA ZA MITIHANI (100%) - WALIMU NA ADMIN
# ------------------------------------------------------------------
elif chaguo == "6. Kujaza Alama za Mitihani (100%)":
    st.header("6. Kujaza Alama za Mitihani (Upeo 100%)")
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa kwenye mfumo kwa sasa.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (100%)" for s in st.session_state.masomo_shule]
        if st.session_state.almar_mitihani.empty or not all(c in st.session_state.almar_mitihani.columns for c in cols):
            st.session_state.almar_mitihani = st.session_state.wanafunzi_db.copy()
            for s in st.session_state.masomo_shule:
                st.session_state.almar_mitihani[f"{s} (100%)"] = np.nan
                
        st.info("Ingiza alama za mitihani (0 - 100) kwenye jedwali:")
        edited_mit = st.data_editor(st.session_state.almar_mitihani[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama za Mitihani"):
            st.session_state.almar_mitihani = edited_mit
            st.success("Alama za mitihani zimehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 7: MATOKEO YA MAJARIBIO PEKEE
# ------------------------------------------------------------------
elif chaguo == "7. Matokeo ya Majaribio Pekee":
    st.header("7. Jedwali la Matokeo ya Majaribio Pekee (100%)")
    if st.session_state.almar_majaribio.empty:
        st.warning("Hakuna data ya majaribio.")
    else:
        st.dataframe(st.session_state.almar_majaribio, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 8: MATOKEO YA MITIHANI PEKEE
# ------------------------------------------------------------------
elif chaguo == "8. Matokeo ya Mitihani Pekee":
    st.header("8. Jedwali la Matokeo ya Mitihani Pekee (100%)")
    if st.session_state.almar_mitihani.empty:
        st.warning("Hakuna data ya mitihani.")
    else:
        st.dataframe(st.session_state.almar_mitihani, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 9: MATOKEO YA MAJARIBIO & MITIHANI (AVERAGE)
# ------------------------------------------------------------------
elif chaguo == "9. Matokeo ya Majaribio & Mitihani (Average)":
    st.header("9. Wastani wa Majaribio na Mitihani ((Majaribio + Mtihani) / 2)")
    if st.session_state.almar_majaribio.empty or st.session_state.almar_mitihani.empty:
        st.warning("Hakikisha umejaza majaribio na mitihani kikamilifu.")
    else:
        df_avg = st.session_state.wanafunzi_db.copy()
        for s in st.session_state.masomo_shule:
            maj_vals = pd.to_numeric(st.session_state.almar_majaribio[f"{s} (100%)"], errors='coerce').fillna(0)
            mit_vals = pd.to_numeric(st.session_state.almar_mitihani[f"{s} (100%)"], errors='coerce').fillna(0)
            df_avg[s] = np.round((maj_vals + mit_vals) / 2, 1)
            
        st.dataframe(df_avg, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 10: MATOKEO YA NECTA FORMAT & SUMMARY
# ------------------------------------------------------------------
elif chaguo == "10. Matokeo ya NECTA Format & Summary":
    st.header("10. Ripoti ya Jumla kwa Mfumo wa NECTA O-Level")
    
    if st.session_state.almar_majaribio.empty or st.session_state.almar_mitihani.empty:
        st.warning("Ingiza data ya majaribio na mitihani kwanza.")
    else:
        info = st.session_state.shule_info
        st.markdown(f"<h3 style='text-align: center;'>{info['wizara']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{info['wilaya']} | {info['mkoa']}</h4>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{info['shule']} (CENTRE NO: {info['namba_shule']})</h4>", unsafe_allow_html=True)
        st.markdown(f"<h5 style='text-align: center;'>{info['aina_mtihani']} - {info['mwaka']}</h5>", unsafe_allow_html=True)

        orodha_ripoti = []
        summary_masomo = {somo: {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0, 'Alama': 0.0, 'Wanafunzi': 0} for somo in st.session_state.masomo_shule}

        for idx, mwanafunzi in st.session_state.wanafunzi_db.iterrows():
            jina = mwanafunzi['Jina la Mwanafunzi']
            taarifa = {'S/N': idx + 1, 'NAME OF CANDIDATE': jina, 'SEX': mwanafunzi['Jinsia (M/F)'], 'INDEX NO': mwanafunzi['Namba ya Usajili']}
            
            pointi_za_masomo = []
            jumla_alama = 0.0
            masomo_yaliyofanywa = 0
            
            masomo_yake = st.session_state.masomo_wanafunzi.get(jina, st.session_state.masomo_shule)
            total_registered = len(masomo_yake)

            for somo in st.session_state.masomo_shule:
                if somo not in masomo_yake:
                    taarifa[f"{somo} MK"] = "-"
                    taarifa[f"{somo} GR"] = "-"
                    continue

                cwt = pd.to_numeric(st.session_state.almar_majaribio.loc[idx, f"{somo} (100%)"], errors='coerce')
                eet = pd.to_numeric(st.session_state.almar_mitihani.loc[idx, f"{somo} (100%)"], errors='coerce')
                
                if pd.isna(cwt) and pd.isna(eet):
                    taarifa[f"{somo} MK"] = "-"
                    taarifa[f"{somo} GR"] = "-"
                    continue
                    
                cwt_val = float(cwt) if not pd.isna(cwt) else 0.0
                eet_val = float(eet) if not pd.isna(eet) else 0.0
                
                wastani = round((cwt_val + eet_val) / 2, 1)
                daraja, pointi = calculate_grade_and_points(wastani)
                
                taarifa[f"{somo} MK"] = wastani
                taarifa[f"{somo} GR"] = daraja
                
                if daraja:
                    pointi_za_masomo.append(pointi)
                    jumla_alama += wastani
                    masomo_yaliyofanywa += 1
                    summary_masomo[somo][daraja] += 1
                    summary_masomo[somo]['Alama'] += wastani
                    summary_masomo[somo]['Wanafunzi'] += 1

            div = calculate_division(0, masomo_yaliyofanywa, total_registered)
            if div not in ['INC', 'ABS']:
                pointi_za_masomo.sort()
                pointi_saba = sum(pointi_za_masomo[:7])
                
                if pointi_saba >= 7 and pointi_saba <= 17: div = 'I'
                elif pointi_saba <= 21: div = 'II'
                elif pointi_saba <= 25: div = 'III'
                elif pointi_saba <= 33: div = 'IV'
                else: div = '0'
            else:
                pointi_saba = sum(pointi_za_masomo) if pointi_za_masomo else 0
                
            taarifa['TOTAL MARKS'] = round(jumla_alama, 2)
            taarifa['AVG'] = round(jumla_alama / masomo_yaliyofanywa, 1) if masomo_yaliyofanywa > 0 else 0
            taarifa['POINTS'] = pointi_saba
            taarifa['DIV'] = div
            taarifa['GPA'] = round(sum(pointi_za_masomo)/len(pointi_za_masomo), 4) if pointi_za_masomo else 5.0
            
            orodha_ripoti.append(taarifa)

        df_final = pd.DataFrame(orodha_ripoti)
        if 'POINTS' in df_final.columns:
            df_final = df_final.sort_values(by=['DIV', 'POINTS', 'AVG'], ascending=[True, True, False]).reset_index(drop=True)
            df_final['POSITION'] = df_final.index + 1
            df_final['S/N'] = df_final.index + 1

        st.dataframe(df_final, use_container_width=True)
        
        # SUMMARY YA UAFAULU
        st.write("---")
        st.subheader("SUMMARY YA UFAULU WA MASOMO")
        rows_summary = []
        for somo, takwimu in summary_masomo.items():
            if takwimu['Wanafunzi'] > 0:
                gpa_somo = round(((takwimu['A']*1)+(takwimu['B']*2)+(takwimu['C']*3)+(takwimu['D']*4)+(takwimu['F']*5))/takwimu['Wanafunzi'], 4)
                if gpa_somo < 2.0: gr_somo = 'A'
                elif gpa_somo < 3.0: gr_somo = 'B'
                elif gpa_somo < 4.0: gr_somo = 'C'
                elif gpa_somo < 4.8: gr_somo = 'D'
                else: gr_somo = 'F'
                
                rows_summary.append({
                    'SUBJECT NAME': somo, 'A': takwimu['A'], 'B': takwimu['B'], 'C': takwimu['C'], 'D': takwimu['D'], 'F': takwimu['F'],
                    'TOTAL REG': takwimu['Wanafunzi'], 'AVG MARKS': round(takwimu['Alama']/takwimu['Wanafunzi'], 1),
                    'GRADE': gr_somo, 'GPA': gpa_somo
                })
        df_sum = pd.DataFrame(rows_summary)
        if not df_sum.empty:
            df_sum = df_sum.sort_values(by='GPA').reset_index(drop=True)
            df_sum['RANK'] = df_sum.index + 1
            st.dataframe(df_sum, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 11: RIPOTI BINAFSI YA MWANAFUNZI (PDF)
# ------------------------------------------------------------------
elif chaguo == "11. Ripoti Binafsi ya Mwanafunzi (PDF)":
    st.header("11. Pakua Ripoti ya Mwanafunzi Mmoja Mmoja au Wote kwa Pamoja")
    
    if len(names_list) == 0 or st.session_state.almar_majaribio.empty or st.session_state.almar_mitihani.empty:
        st.warning("Hakikisha majina na alama zote zimejazwa kwanza kabla ya kutoa ripoti.")
    else:
        info = st.session_state.shule_info
        
        def andaa_data_mwanafunzi(idx_mwa, jina_mwa):
            data_somo_pdf = [["Somo", "Majaribio", "Mtihani", "Wastani", "Gredi", "Maelezo (Remarks)"]]
            masomo_yake = st.session_state.masomo_wanafunzi.get(jina_mwa, st.session_state.masomo_shule)
            
            pointi_list = []
            for somo in st.session_state.masomo_shule:
                if somo in masomo_yake:
                    cwt = pd.to_numeric(st.session_state.almar_majaribio.loc[idx_mwa, f"{somo} (100%)"], errors='coerce')
                    eet = pd.to_numeric(st.session_state.almar_mitihani.loc[idx_mwa, f"{somo} (100%)"], errors='coerce')
                    cwt_v = float(cwt) if not pd.isna(cwt) else 0.0
                    eet_v = float(eet) if not pd.isna(eet) else 0.0
                    tot = round((cwt_v + eet_v) / 2, 1)
                    gr, pt = calculate_grade_and_points(tot)
                    if gr: 
                        pointi_list.append(pt)
                        rem = st.session_state.remarks_dict.get(gr, '')
                    else:
                        rem = '-'
                    data_somo_pdf.append([somo, str(cwt_v), str(eet_v), str(tot), gr if gr else "-", rem])
                else:
                    data_somo_pdf.append([somo, "-", "-", "-", "-", "Hajachagua"])
            
            div_final = calculate_division(0, len(pointi_list), len(masomo_yake))
            if div_final not in ['INC', 'ABS']:
                pointi_list.sort()
                pts_saba = sum(pointi_list[:7])
                if pts_saba >= 7 and pts_saba <= 17: div_final = "I"
                elif pts_saba <= 21: div_final = "II"
                elif pts_saba <= 25: div_final = "III"
                elif pts_saba <= 33: div_final = "IV"
                else: div_final = "0"
            else:
                pts_saba = sum(pointi_list) if pointi_list else 0
                
            return data_somo_pdf, pts_saba, div_final

        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.subheader("Chaguo A: Pakua Mwanafunzi Mmoja Mmoja")
            mwanafunzi_sel = st.selectbox("Chagua mwanafunzi wa kumtengenezea PDF:", names_list)
            idx_mwa = names_list.index(mwanafunzi_sel)
            
            if st.button(f"Tengeneza PDF ya {mwanafunzi_sel}"):
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
                story = []
                styles = getSampleStyleSheet()
                style_head = ParagraphStyle('HHead', parent=styles['Heading2'], alignment=1, spaceAfter=4)
                style_normal = ParagraphStyle('NHead', parent=styles['Normal'], spaceAfter=12, fontSize=11)
                
                story.append(Paragraph(f"<b>{info['wizara']}</b>", style_head))
                story.append(Paragraph(f"<b>{info['wilaya']} | {info['mkoa']}</b>", style_head))
                story.append(Paragraph(f"<b>{info['shule']} (CENTRE: {info['namba_shule']})</b>", style_head))
                story.append(Paragraph(f"<u>{info['aina_mtihani']} ({info['mwaka']})</u>", style_head))
                story.append(Spacer(1, 15))
                
                jinsia_mwa = st.session_state.wanafunzi_db.loc[idx_mwa, 'Jinsia (M/F)']
                namba_mwa = st.session_state.wanafunzi_db.loc[idx_mwa, 'Namba ya Usajili']
                story.append(Paragraph(f"<b>Jina:</b> {mwanafunzi_sel} &nbsp;&nbsp;&nbsp;&nbsp; <b>Jinsia:</b> {jinsia_mwa} &nbsp;&nbsp;&nbsp;&nbsp; <b>Namba ya Usajili:</b> {namba_mwa}", style_normal))
                
                data_somo, pts, div = andaa_data_mwanafunzi(idx_mwa, mwanafunzi_sel)
                
                t = Table(data_somo, colWidths=[160, 70, 70, 70, 50, 100])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('ALIGN', (0,1), (0,-1), 'LEFT'),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
                ]))
                story.append(t)
                story.append(Spacer(1, 15))
                
                story.append(Paragraph(f"<b>JUMLA YA POINTI:</b> {pts} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>DARASA (DIVISION):</b> {div}", style_normal))
                story.append(Spacer(1, 30))
                
                data_saini = [["..........................................", ".........................................."], ["Saini ya Mkuu wa Shule", "Saini ya Mzazi/Mlezi"]]
                tsaini = Table(data_saini, colWidths=[260, 260])
                tsaini.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                story.append(tsaini)
                
                doc.build(story)
                buffer.seek(0)
                
                st.download_button(
                    label=f"Pakua PDF ya {mwanafunzi_sel}",
                    data=buffer.getvalue(),
                    file_name=f"Ripoti_{mwanafunzi_sel.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
        with col_p2:
            st.subheader("Chaguo B: Pakua Ripoti za Wote kwa Mara Moja")
            st.write("Bonyeza kitufe kilicho chini ili kuzalisha faili kubwa la PDF ambalo lina ripoti za wanafunzi wote shuleni.")
            
            if st.button("Tengeneza PDF ya Shule Nzima"):
                buffer_all = io.BytesIO()
                doc_all = SimpleDocTemplate(buffer_all, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
                story_all = []
                styles = getSampleStyleSheet()
                style_head = ParagraphStyle('HHeadAll', parent=styles['Heading2'], alignment=1, spaceAfter=4)
                style_normal = ParagraphStyle('NHeadAll', parent=styles['Normal'], spaceAfter=12, fontSize=11)
                
                for idx_all, jina_all in enumerate(names_list):
                    story_all.append(Paragraph(f"<b>{info['wizara']}</b>", style_head))
                    story_all.append(Paragraph(f"<b>{info['wilaya']} | {info['mkoa']}</b>", style_head))
                    story_all.append(Paragraph(f"<b>{info['shule']} (CENTRE: {info['namba_shule']})</b>", style_head))
                    story_all.append(Paragraph(f"<u>{info['aina_mtihani']} ({info['mwaka']})</u>", style_head))
                    story_all.append(Spacer(1, 15))
                    
                    jinsia_all = st.session_state.wanafunzi_db.loc[idx_all, 'Jinsia (M/F)']
                    namba_all = st.session_state.wanafunzi_db.loc[idx_all, 'Namba ya Usajili']
                    story_all.append(Paragraph(f"<b>Jina:</b> {jina_all} &nbsp;&nbsp;&nbsp;&nbsp; <b>Jinsia:</b> {jinsia_all} &nbsp;&nbsp;&nbsp;&nbsp; <b>Namba ya Usajili:</b> {namba_all}", style_normal))
                    
                    data_somo, pts, div = andaa_data_mwanafunzi(idx_all, jina_all)
                    
                    t = Table(data_somo, colWidths=[160, 70, 70, 70, 50, 100])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('ALIGN', (0,1), (0,-1), 'LEFT'),
                        ('GRID', (0,0), (-1,-1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
                    ]))
                    story_all.append(t)
                    story_all.append(Spacer(1, 15))
                    
                    story_all.append(Paragraph(f"<b>JUMLA YA POINTI:</b> {pts} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>DARASA (DIVISION):</b> {div}", style_normal))
                    story_all.append(Spacer(1, 30))
                    
                    data_saini = [["..........................................", ".........................................."], ["Saini ya Mkuu wa Shule", "Saini ya Mzazi/Mlezi"]]
                    tsaini = Table(data_saini, colWidths=[260, 260])
                    tsaini.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                    story_all.append(tsaini)
                    
                    if idx_all < len(names_list) - 1:
                        story_all.append(PageBreak())
                        
                doc_all.build(story_all)
                buffer_all.seek(0)
                
                st.download_button(
                    label="Pakua PDF ya Shule Nzima",
                    data=buffer_all.getvalue(),
                    file_name=f"Ripoti_Kamili_Wanafunzi_Wote.pdf",
                    mime="application/pdf"
                )
