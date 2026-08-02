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
def calculate_division(pointi_za_masomo, valid_subjects, total_registered_subjects):
    if total_registered_subjects == 0 or valid_subjects == 0:
        return 'ABS', 0
    if valid_subjects < 7:
        return 'INC', sum(pointi_za_masomo)
    
    # NECTA inachukua masomo 7 bora pekee
    pointi_za_masomo.sort()
    pointi_saba = sum(pointi_za_masomo[:7])
    
    if pointi_saba >= 7 and pointi_saba <= 17: return 'I', pointi_saba
    elif pointi_saba <= 21: return 'II', pointi_saba
    elif pointi_saba <= 25: return 'III', pointi_saba
    elif pointi_saba <= 33: return 'IV', pointi_saba
    else: return '0', pointi_saba

# ------------------------------------------------------------------
# 2. Uchaguzi wa Darasa na Kutenganisha Data (Sidebar)
# ------------------------------------------------------------------
st.sidebar.title("MIPANGILIO YA MFUMO")

kidato_kilichochaguliwa = st.sidebar.selectbox(
    "Chagua Kidato:", 
    ["KIDATO CHA KWANZA", "KIDATO CHA PILI", "KIDATO CHA TATU", "KIDATO CHA NNE"]
)
darasa_id = kidato_kilichochaguliwa.replace(" ", "_")

# Kila darasa linakuwa na hifadhi yake binafsi (Session State Isolation)
if f'shule_info_{darasa_id}' not in st.session_state:
    st.session_state[f'shule_info_{darasa_id}'] = {
        "wizara": "PRIME MINISTER'S OFFICE", 
        "mkoa": "MWANZA", 
        "wilaya": "BUCHOSA DISTRICT COUNCIL", 
        "shule": "CHEMA SECONDARY SCHOOL", 
        "namba_shule": "S7647", 
        "aina_mtihani": f"MOCK EXAMINATION - {kidato_kilichochaguliwa}", 
        "mwaka": "2026"
    }

if f'masomo_shule_{darasa_id}' not in st.session_state:
    st.session_state[f'masomo_shule_{darasa_id}'] = ['CIVICS', 'HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS']

if f'remarks_dict_{darasa_id}' not in st.session_state:
    st.session_state[f'remarks_dict_{darasa_id}'] = {'A': 'Bora Sana', 'B': 'Bora', 'C': 'Vizuri', 'D': 'Inaridhisha', 'F': 'Imefeli'}

if f'wanafunzi_db_{darasa_id}' not in st.session_state:
    st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])

if f'masomo_wanafunzi_{darasa_id}' not in st.session_state:
    st.session_state[f'masomo_wanafunzi_{darasa_id}'] = {}

if f'almar_majaribio_{darasa_id}' not in st.session_state:
    st.session_state[f'almar_majaribio_{darasa_id}'] = pd.DataFrame()

if f'almar_mitihani_{darasa_id}' not in st.session_state:
    st.session_state[f'almar_mitihani_{darasa_id}'] = pd.DataFrame()

# Njia za mkato za kuita data za darasa husika
shule_info = st.session_state[f'shule_info_{darasa_id}']
masomo_shule = st.session_state[f'masomo_shule_{darasa_id}']
remarks_dict = st.session_state[f'remarks_dict_{darasa_id}']
wanafunzi_db = st.session_state[f'wanafunzi_db_{darasa_id}']
masomo_wanafunzi = st.session_state[f'masomo_wanafunzi_{darasa_id}']

# ------------------------------------------------------------------
# Udhibiti wa Ufikiaji (Access Control)
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

# Orodha ya Menu
orodha_ya_menu = ["0. Kuhusu Mfumo"]
if is_admin:
    orodha_ya_menu.extend([
        "1. Taarifa Binafsi za Mtihani",
        "2. Usajili wa Masomo ya Shule (Hadi 20)",
        "3. Sajili Majina ya Wanafunzi",
        "4. Kumsajilia Mwanafunzi Masomo"
    ])

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

names_list = wanafunzi_db['Jina la Mwanafunzi'].tolist()

# ------------------------------------------------------------------
# KIPENGELE 0: KUHUSU MFUMO
# ------------------------------------------------------------------
if chaguo == "0. Kuhusu Mfumo":
    st.header(f"Mfumo wa Kuchakata Matokeo - {kidato_kilichochaguliwa}")
    st.info(f"Hivi sasa unafanya kazi kwenye data za: **{kidato_kilichochaguliwa}**. Ukitaka kubadilisha darasa, tumia menu iliyopo juu kabisa upande wa kushoto.")

# ------------------------------------------------------------------
# KIPENGELE 1: TAARIFA BINAFSI ZA MTIHANI (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "1. Taarifa Binafsi za Mtihani" and is_admin:
    st.header(f"1. Taarifa za Shule na Mtihani - {kidato_kilichochaguliwa}")
    shule_info["wizara"] = st.text_input("Wizara", shule_info["wizara"])
    shule_info["mkoa"] = st.text_input("Mkoa", shule_info["mkoa"])
    shule_info["wilaya"] = st.text_input("Wilaya / Halmashauri", shule_info["wilaya"])
    shule_info["shule"] = st.text_input("Jina la Shule", shule_info["shule"])
    shule_info["namba_shule"] = st.text_input("Namba ya Kituo (Centre No)", shule_info["namba_shule"])
    shule_info["aina_mtihani"] = st.text_input("Aina ya Mtihani", shule_info["aina_mtihani"])
    shule_info["mwaka"] = st.text_input("Mwaka / Mwezi", shule_info["mwaka"])
    
    st.write("---")
    st.subheader("Badili Maelezo ya Gredi (Remarks Customization)")
    for key in remarks_dict.keys():
        remarks_dict[key] = st.text_input(f"Maelezo ya Gredi {key}:", remarks_dict[key])
    st.success("Taarifa zimehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 2: USAJILI WA MASOMO YA SHULE (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "2. Usajili wa Masomo ya Shule (Hadi 20)" and is_admin:
    st.header(f"2. Usajili wa Masomo - {kidato_kilichochaguliwa}")
    masomo_maandishi = st.text_area("Ingiza masomo yote yakitenganishwa kwa alama ya mkato (,):", ", ".join(masomo_shule))
    masomo_yaliyosafishwa = [m.strip().upper() for m in masomo_maandishi.split(",") if m.strip()]
    
    if len(masomo_yaliyosafishwa) > 20:
        st.error("Umevuka kikomo! Mfumo unaruhusu mwisho masomo 20 pekee.")
    else:
        st.session_state[f'masomo_shule_{darasa_id}'] = masomo_yaliyosafishwa
        st.success(f"Usajili umekamilika. Jumla ya masomo: {len(masomo_yaliyosafishwa)}")

# ------------------------------------------------------------------
# KIPENGELE 3: SAJILI MAJINA YA WANAFUNZI (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "3. Sajili Majina ya Wanafunzi" and is_admin:
    st.header(f"3. Sajili Wanafunzi - {kidato_kilichochaguliwa}")
    tab1, tab2 = st.tabs(["Fomu ya Usajili", "Kupandisha Excel"])
    
    with tab1:
        with st.form("fomu_mwanafunzi"):
            mpya_jina = st.text_input("Jina Kamili la Mwanafunzi:").upper()
            mpya_jinsia = st.selectbox("Jinsia:", ["M", "F"])
            mpya_namba = st.text_input("Namba ya Usajili:", f"{shule_info['namba_shule']}/{str(len(wanafunzi_db)+1).zfill(4)}")
            wasilisha = st.form_submit_button("Sajili")
            if wasilisha and mpya_jina:
                mpya_row = pd.DataFrame([[mpya_jina, mpya_jinsia, mpya_namba]], columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
                st.session_state[f'wanafunzi_db_{darasa_id}'] = pd.concat([wanafunzi_db, mpya_row], ignore_index=True)
                st.rerun()

    with tab2:
        uploaded_file = st.file_uploader("Pandisha Excel (.xlsx):", type=["xlsx"])
        if uploaded_file is not None:
            df_up = pd.read_excel(uploaded_file)
            if 'Jina la Mwanafunzi' in df_up.columns and 'Jinsia (M/F)' in df_up.columns:
                st.session_state[f'wanafunzi_db_{darasa_id}'] = df_up[['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili']].dropna(subset=['Jina la Mwanafunzi']).reset_index(drop=True)
                st.success("Wanafunzi wameongezwa kikamilifu!")
                st.rerun()

    st.dataframe(st.session_state[f'wanafunzi_db_{darasa_id}'], use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 4: KUMSAJILIA MWANAFUNZI MASOMO (ADMIN ONLY)
# ------------------------------------------------------------------
elif chaguo == "4. Kumsajilia Mwanafunzi Masomo" and is_admin:
    st.header("4. Kusajili Masomo Maalum ya Wanafunzi")
    if len(names_list) == 0:
        st.warning("Tafadhali sajili majina kwanza kwenye kipengele namba 3.")
    else:
        mwanafunzi_sel = st.selectbox("Chagua Mwanafunzi:", names_list)
        if mwanafunzi_sel not in masomo_wanafunzi:
            masomo_wanafunzi[mwanafunzi_sel] = masomo_shule.copy()
            
        masomo_yake = st.multiselect(f"Chagua Masomo ya {mwanafunzi_sel}:", masomo_shule, default=masomo_wanafunzi[mwanafunzi_sel])
        if st.button(f"Hifadhi Masomo"):
            st.session_state[f'masomo_wanafunzi_{darasa_id}'][mwanafunzi_sel] = masomo_yake
            st.success(f"Masomo ya {mwanafunzi_sel} yamehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 5 & 6: KUJAZA ALAMA (WALIMU NA ADMIN)
# ------------------------------------------------------------------
elif chaguo == "5. Kujaza Alama za Majaribio (100%)":
    st.header("5. Kujaza Alama za Majaribio (Upeo 100%)")
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (100%)" for s in masomo_shule]
        db_maj = st.session_state[f'almar_majaribio_{darasa_id}']
        if db_maj.empty or not all(c in db_maj.columns for c in cols):
            db_maj = wanafunzi_db.copy()
            for s in masomo_shule: db_maj[f"{s} (100%)"] = np.nan
        
        edited = st.data_editor(db_maj[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama"):
            st.session_state[f'almar_majaribio_{darasa_id}'] = edited
            st.success("Zimehifadhiwa kikamilifu!")

elif chaguo == "6. Kujaza Alama za Mitihani (100%)":
    st.header("6. Kujaza Alama za Mitihani (Upeo 100%)")
    if len(names_list) == 0:
        st.warning("Hakuna wanafunzi waliosajiliwa.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (100%)" for s in masomo_shule]
        db_mit = st.session_state[f'almar_mitihani_{darasa_id}']
        if db_mit.empty or not all(c in db_mit.columns for c in cols):
            db_mit = wanafunzi_db.copy()
            for s in masomo_shule: db_mit[f"{s} (100%)"] = np.nan
            
        edited = st.data_editor(db_mit[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama"):
            st.session_state[f'almar_mitihani_{darasa_id}'] = edited
            st.success("Zimehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 7 & 8 & 9: PREVIEWS
# ------------------------------------------------------------------
elif chaguo == "7. Matokeo ya Majaribio Pekee":
    st.dataframe(st.session_state[f'almar_majaribio_{darasa_id}'], use_container_width=True)

elif chaguo == "8. Matokeo ya Mitihani Pekee":
    st.dataframe(st.session_state[f'almar_mitihani_{darasa_id}'], use_container_width=True)

elif chaguo == "9. Matokeo ya Majaribio & Mitihani (Average)":
    st.header("9. Wastani wa Majaribio na Mitihani")
    db_maj = st.session_state[f'almar_majaribio_{darasa_id}']
    db_mit = st.session_state[f'almar_mitihani_{darasa_id}']
    if db_maj.empty or db_mit.empty:
        st.warning("Data haijajazwa kikamilifu.")
    else:
        df_avg = wanafunzi_db.copy()
        for s in masomo_shule:
            maj_vals = pd.to_numeric(db_maj[f"{s} (100%)"], errors='coerce').fillna(0)
            mit_vals = pd.to_numeric(db_mit[f"{s} (100%)"], errors='coerce').fillna(0)
            df_avg[s] = np.round((maj_vals + mit_vals) / 2, 1)
        st.dataframe(df_avg, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 10: MATOKEO YA NECTA FORMAT & SUMMARY
# ------------------------------------------------------------------
elif chaguo == "10. Matokeo ya NECTA Format & Summary":
    st.header("10. Broadsheet ya Matokeo (NECTA Format)")
    db_maj = st.session_state[f'almar_majaribio_{darasa_id}']
    db_mit = st.session_state[f'almar_mitihani_{darasa_id}']
    
    if db_maj.empty or db_mit.empty:
        st.warning("Tafadhali jaza alama kwanza kwenye vipengele vya 5 na 6.")
    else:
        st.markdown(f"<h3 style='text-align: center;'>{shule_info['wizara']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{shule_info['shule']} ({shule_info['namba_shule']})</h4>", unsafe_allow_html=True)
        
        orodha_ripoti = []
        summary_masomo = {somo: {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0, 'Alama': 0.0, 'Wanafunzi': 0} for somo in masomo_shule}

        for idx, mwanafunzi in wanafunzi_db.iterrows():
            jina = mwanafunzi['Jina la Mwanafunzi']
            taarifa = {'S/N': idx + 1, 'NAME OF CANDIDATE': jina, 'SEX': mwanafunzi['Jinsia (M/F)'], 'INDEX NO': mwanafunzi['Namba ya Usajili']}
            
            pointi_za_masomo = []
            jumla_alama = 0.0
            masomo_yaliyofanywa = 0
            masomo_yake = masomo_wanafunzi.get(jina, masomo_shule)

            for somo in masomo_shule:
                if somo not in masomo_yake:
                    taarifa[f"{somo} GR"] = "-"
                    continue

                cwt = pd.to_numeric(db_maj.loc[idx, f"{somo} (100%)"], errors='coerce')
                eet = pd.to_numeric(db_mit.loc[idx, f"{somo} (100%)"], errors='coerce')
                
                cwt_val = float(cwt) if not pd.isna(cwt) else 0.0
                eet_val = float(eet) if not pd.isna(eet) else 0.0
                
                wastani = round((cwt_val + eet_val) / 2, 1)
                daraja, pointi = calculate_grade_and_points(wastani)
                
                taarifa[f"{somo} GR"] = daraja if daraja else "-"
                
                if daraja:
                    pointi_za_masomo.append(pointi)
                    jumla_alama += wastani
                    masomo_yaliyofanywa += 1
                    summary_masomo[somo][daraja] += 1
                    summary_masomo[somo]['Alama'] += wastani
                    summary_masomo[somo]['Wanafunzi'] += 1

            div, pts = calculate_division(pointi_za_masomo, masomo_yaliyofanywa, len(masomo_yake))
            
            taarifa['TOTAL MARKS'] = round(jumla_alama, 1)
            taarifa['AVG'] = round(jumla_alama / masomo_yaliyofanywa, 1) if masomo_yaliyofanywa > 0 else 0
            taarifa['POINTS'] = pts
            taarifa['DIV'] = div
            
            orodha_ripoti.append(taarifa)

        df_final = pd.DataFrame(orodha_ripoti)
        df_final = df_final.sort_values(by=['DIV', 'POINTS', 'AVG'], ascending=[True, True, False]).reset_index(drop=True)
        df_final['POSITION'] = df_final.index + 1
        df_final['S/N'] = df_final.index + 1
        st.dataframe(df_final, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 11: RIPOTI BINAFSI YA MWANAFUNZI (PDF)
# ------------------------------------------------------------------
elif chaguo == "11. Ripoti Binafsi ya Mwanafunzi (PDF)":
    st.header("11. Pakua Ripoti ya Mwanafunzi Binafsi / Shule Nzima")
    db_maj = st.session_state[f'almar_majaribio_{darasa_id}']
    db_mit = st.session_state[f'almar_mitihani_{darasa_id}']

    if len(names_list) == 0 or db_maj.empty or db_mit.empty:
        st.warning("Tafadhali hakikisha majina na alama zote zimejazwa kwanza.")
    else:
        def andaa_data_mwanafunzi(idx_mwa, jina_mwa):
            data_somo_pdf = [["Somo", "Majaribio", "Mtihani", "Wastani", "Gredi", "Maelezo"]]
            masomo_yake = masomo_wanafunzi.get(jina_mwa, masomo_shule)
            pointi_list = []
            
            for somo in masomo_shule:
                if somo in masomo_yake:
                    cwt = pd.to_numeric(db_maj.loc[idx_mwa, f"{somo} (100%)"], errors='coerce')
                    eet = pd.to_numeric(db_mit.loc[idx_mwa, f"{somo} (100%)"], errors='coerce')
                    cwt_v = float(cwt) if not pd.isna(cwt) else 0.0
                    eet_v = float(eet) if not pd.isna(eet) else 0.0
                    tot = round((cwt_v + eet_v) / 2, 1)
                    gr, pt = calculate_grade_and_points(tot)
                    if gr: 
                        pointi_list.append(pt)
                        rem = remarks_dict.get(gr, '')
                    else:
                        rem = '-'
                    data_somo_pdf.append([somo, str(cwt_v), str(eet_v), str(tot), gr if gr else "-", rem])
                else:
                    data_somo_pdf.append([somo, "-", "-", "-", "-", "Hajachagua"])
            
            div_final, pts_saba = calculate_division(pointi_list, len(pointi_list), len(masomo_yake))
            return data_somo_pdf, pts_saba, div_final

        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            mwanafunzi_sel = st.selectbox("Chagua mwanafunzi:", names_list)
            idx_mwa = names_list.index(mwanafunzi_sel)
            
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
                
                jinsia_mwa = wanafunzi_db.loc[idx_mwa, 'Jinsia (M/F)']
                namba_mwa = wanafunzi_db.loc[idx_mwa, 'Namba ya Usajili']
                story.append(Paragraph(f"<b>Jina:</b> {mwanafunzi_sel} | <b>Jinsia:</b> {jinsia_mwa} | <b>Namba:</b> {namba_mwa}", style_normal))
                
                data_somo, pts, div = andaa_data_mwanafunzi(idx_mwa, mwanafunzi_sel)
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
                story.append(Paragraph(f"<b>JUMLA YA POINTI:</b> {pts} &nbsp;&nbsp;&nbsp;&nbsp; <b>DIVISION:</b> {div}", style_normal))
                
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
                
                for idx_all, jina_all in enumerate(names_list):
                    story_all.append(Paragraph(f"<b>{shule_info['wizara']}</b>", style_head))
                    story_all.append(Paragraph(f"<b>{shule_info['shule']}</b>", style_head))
                    story_all.append(Spacer(1, 10))
                    
                    jinsia_all = wanafunzi_db.loc[idx_all, 'Jinsia (M/F)']
                    namba_all = wanafunzi_db.loc[idx_all, 'Namba ya Usajili']
                    story_all.append(Paragraph(f"<b>Mwanafunzi:</b> {jina_all} | <b>Jinsia:</b> {jinsia_all} | <b>Namba:</b> {namba_all}", style_normal))
                    
                    data_somo, pts, div = andaa_data_mwanafunzi(idx_all, jina_all)
                    t = Table(data_somo, colWidths=[160, 70, 70, 70, 50, 100])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('GRID', (0,0), (-1,-1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
                    ]))
                    story_all.append(t)
                    story_all.append(Spacer(1, 10))
                    story_all.append(Paragraph(f"<b>JUMLA YA POINTI:</b> {pts} | <b>DIVISION:</b> {div}", style_normal))
                    story_all.append(PageBreak()) # Inatenganisha kila mwanafunzi na ukurasa mpya
                
                doc_all.build(story_all)
                buffer_all.seek(0)
                st.download_button(label="Pakua PDF ya Shule Nzima", data=buffer_all.getvalue(), file_name=f"Ripoti_Shule_Nzima_{darasa_id}.pdf", mime="application/pdf")
