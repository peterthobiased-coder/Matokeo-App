import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ------------------------------------------------------------------
# 1. Mipangilio ya Msingi na Caching
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
def calculate_division(total_points, selected_subjects_count):
    if selected_subjects_count < 7: return 'I-VII (Chini ya 7)'
    if total_points >= 7 and total_points <= 17: return 'I'
    elif total_points <= 21: return 'II'
    elif total_points <= 25: return 'III'
    elif total_points <= 33: return 'IV'
    else: return '0'

# Initialize session states kama hazipo
if 'shule_info' not in st.session_state:
    st.session_state.shule_info = {"wizara": "PRIME MINISTER'S OFFICE", "mkoa": "MWANZA", "wilaya": "BUCHOSA DISTRICT COUNCIL", "shule": "CHEMA SECONDARY SCHOOL", "namba_shule": "S7647", "aina_mtihani": "FORM FOUR LAKE ZONE MOCK EXAMINATION", "mwaka": "MAY 2026"}
if 'masomo_shule' not in st.session_state:
    st.session_state.masomo_shule = ['CIVICS', 'HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS', 'LITERATURE IN ENGLISH']
if 'wanafunzi_db' not in st.session_state:
    st.session_state.wanafunzi_db = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
if 'masomo_wanafunzi' not in st.session_state:
    st.session_state.masomo_wanafunzi = {}
if 'almar_majaribio' not in st.session_state:
    st.session_state.almar_majaribio = pd.DataFrame()
if 'almar_mitihani' not in st.session_state:
    st.session_state.almar_mitihani = pd.DataFrame()

# ------------------------------------------------------------------
# Navigation - Tenganisha Vipengele 11
# ------------------------------------------------------------------
st.sidebar.title("MENU KUU")
chaguo = st.sidebar.radio("Nenda kwenye kipengele:", [
    "1. Taarifa Binafsi za Mtihani",
    "2. Usajili wa Masomo ya Shule",
    "3. Sajili Majina (Upload/Download Template)",
    "4. Kumsajilia Mwanafunzi Masomo",
    "5. Kujaza Majaribio (30%)",
    "6. Kujaza Mitihani (70%)",
    "7. Matokeo ya Majaribio Pekee",
    "8. Matokeo ya Mitihani Pekee",
    "9. Matokeo ya Majaribio & Mitihani (Average)",
    "10. Matokeo ya NECTA Format & Summary",
    "11. Ripoti Binafsi ya Mwanafunzi (PDF)"
])

# Data sync / backup to handle schema changes dynamic
names_list = st.session_state.wanafunzi_db['Jina la Mwanafunzi'].tolist()

# ------------------------------------------------------------------
# KIPENGELE 1: TAARIFA BINAFSI ZA MTIHANI
# ------------------------------------------------------------------
if chaguo == "1. Taarifa Binafsi za Mtihani":
    st.header("1. Taarifa Binafsi za Shule na Mtihani")
    st.session_state.shule_info["wizara"] = st.text_input("Wizara", st.session_state.shule_info["wizara"])
    st.session_state.shule_info["mkoa"] = st.text_input("Mkoa", st.session_state.shule_info["mkoa"])
    st.session_state.shule_info["wilaya"] = st.text_input("Wilaya / Halmashauri", st.session_state.shule_info["wilaya"])
    st.session_state.shule_info["shule"] = st.text_input("Jina la Shule", st.session_state.shule_info["shule"])
    st.session_state.shule_info["namba_shule"] = st.text_input("Namba ya Kituo (Centre No)", st.session_state.shule_info["namba_shule"])
    st.session_state.shule_info["aina_mtihani"] = st.text_input("Aina ya Mtihani", st.session_state.shule_info["aina_mtihani"])
    st.session_state.shule_info["mwaka"] = st.text_input("Mwaka / Mwezi", st.session_state.shule_info["mwaka"])
    st.success("Taarifa zimehifadhiwa kikamilifu!")

# ------------------------------------------------------------------
# KIPENGELE 2: USAJILI WA MASOMO YA SHULE
# ------------------------------------------------------------------
elif chaguo == "2. Usajili wa Masomo ya Shule":
    st.header("2. Usajili wa Masomo Yanayofundishwa Shuleni kwa Ujumla")
    masomo_makuu = ['CIVICS', 'HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS', 'LITERATURE IN ENGLISH', 'COMMERCE', 'BOOK-KEEPING', 'BIBLE KNOWLEDGE', 'ISLAMIC KNOWLEDGE']
    st.session_state.masomo_shule = st.multiselect("Chagua masomo yote yanayochakatwa katika kituo chako:", masomo_makuu, default=[m for m in st.session_state.masomo_shule if m in masomo_makuu])
    st.write("Masomo yaliyosajiliwa sasa:", st.session_state.masomo_shule)

# ------------------------------------------------------------------
# KIPENGELE 3: SAJILI MAJINA (UPLOAD/DOWNLOAD TEMPLATE)
# ------------------------------------------------------------------
elif chaguo == "3. Sajili Majina (Upload/Download Template)":
    st.header("3. Sajili Majina ya Wanafunzi")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Hatua ya A: Pakua Template ya Excel")
        df_temp = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
        # Mfano wa data
        df_temp.loc[0] = ["JUMA HAMIS", "M", f"{st.session_state.shule_info['namba_shule']}/0001"]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_temp.to_excel(writer, index=False, sheet_name='Template')
        st.download_button(label="Pakua Excel Template", data=output.getvalue(), file_name="template_wanafunzi.xlsx", mime="application/vnd.ms-excel")
        
    with col2:
        st.subheader("Hatua ya B: Pandisha (Upload) Excel Iliyojazwa")
        uploaded_file = st.file_uploader("Chagua faili la Excel lenye majina", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                df_uploaded = pd.read_excel(uploaded_file)
                if 'Jina la Mwanafunzi' in df_uploaded.columns and 'Jinsia (M/F)' in df_uploaded.columns:
                    st.session_state.wanafunzi_db = df_uploaded[['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili']].dropna(subset=['Jina la Mwanafunzi']).reset_index(drop=True)
                    st.success(f"Wanafunzi {len(st.session_state.wanafunzi_db)} wamepakiwa kikamilifu!")
                else:
                    st.error("Hakikisha Excel ina nguzo za: 'Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'")
            except Exception as e:
                st.error(f"Hitilafu imetokea kusoma faili: {e}")

    st.subheader("Orodha ya Wanafunzi Waliosajiliwa kwa Sasa")
    st.dataframe(st.session_state.wanafunzi_db, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 4: KUMSAJILIA MWANAFUNZI MASOMO
# ------------------------------------------------------------------
elif chaguo == "4. Kumsajilia Mwanafunzi Masomo":
    st.header("4. Kumsajilia Mwanafunzi Masomo Yake Maalum")
    if len(names_list) == 0:
        st.warning("Tafadhali sajili majina ya wanafunzi kwanza kwenye kipengele cha 3.")
    else:
        mwanafunzi_sel = st.selectbox("Chagua Mwanafunzi:", names_list)
        
        # Kama hajawahi kusajiliwa kabisa, apewe masomo yote kama default
        if mwanafunzi_sel not in st.session_state.masomo_wanafunzi:
            st.session_state.masomo_wanafunzi[mwanafunzi_sel] = st.session_state.masomo_shule.copy()
            
        masomo_yake = st.multiselect(f"Chagua Masomo anayosoma {mwanafunzi_sel}:", st.session_state.masomo_shule, default=st.session_state.masomo_wanafunzi[mwanafunzi_sel])
        if st.button(f"Hifadhi Masomo ya {mwanafunzi_sel}"):
            st.session_state.masomo_wanafunzi[mwanafunzi_sel] = masomo_yake
            st.success(f"Masomo ya {mwanafunzi_sel} yamehifadhiwa!")

# ------------------------------------------------------------------
# KIPENGELE 5: KUJAZA MAJARIBIO (30%)
# ------------------------------------------------------------------
elif chaguo == "5. Kujaza Majaribio (30%)":
    st.header("5. Kujaza Alama za Majaribio (Upeo 30%)")
    if len(names_list) == 0:
        st.warning("Sajili majina kwanza.")
    else:
        # Andaa nguzo za jedwali la majaribio
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (30%)" for s in st.session_state.masomo_shule]
        if st.session_state.almar_majaribio.empty or not all(c in st.session_state.almar_majaribio.columns for c in cols):
            st.session_state.almar_majaribio = st.session_state.wanafunzi_db.copy()
            for s in st.session_state.masomo_shule:
                st.session_state.almar_majaribio[f"{s} (30%)"] = np.nan
        
        st.info("Ingiza alama za majaribio (0 - 30) kwenye jedwali hapa chini:")
        edited_maj = st.data_editor(st.session_state.almar_majaribio[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama za Majaribio"):
            st.session_state.almar_majaribio = edited_maj
            st.success("Alama za majaribio zimehifadhiwa kwa usalama!")

# ------------------------------------------------------------------
# KIPENGELE 6: KUJAZA MITIHANI (70%)
# ------------------------------------------------------------------
elif chaguo == "6. Kujaza Mitihani (70%)":
    st.header("6. Kujaza Alama za Mitihani (Upeo 70%)")
    if len(names_list) == 0:
        st.warning("Sajili majina kwanza.")
    else:
        cols = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'] + [f"{s} (70%)" for s in st.session_state.masomo_shule]
        if st.session_state.almar_mitihani.empty or not all(c in st.session_state.almar_mitihani.columns for c in cols):
            st.session_state.almar_mitihani = st.session_state.wanafunzi_db.copy()
            for s in st.session_state.masomo_shule:
                st.session_state.almar_mitihani[f"{s} (70%)"] = np.nan
                
        st.info("Ingiza alama za mitihani (0 - 70) kwenye jedwali hapa chini:")
        edited_mit = st.data_editor(st.session_state.almar_mitihani[cols], use_container_width=True, num_rows="fixed")
        if st.button("Hifadhi Alama za Mitihani"):
            st.session_state.almar_mitihani = edited_mit
            st.success("Alama za mitihani zimehifadhiwa kwa usalama!")

# ------------------------------------------------------------------
# KIPENGELE 7: MATOKEO YA MAJARIBIO PEKEE
# ------------------------------------------------------------------
elif chaguo == "7. Matokeo ya Majaribio Pekee":
    st.header("7. Jedwali la Matokeo ya Majaribio Pekee")
    if st.session_state.almar_majaribio.empty:
        st.warning("Hakuna data ya majaribio.")
    else:
        st.dataframe(st.session_state.almar_majaribio, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 8: MATOKEO YA MITIHANI PEKEE
# ------------------------------------------------------------------
elif chaguo == "8. Matokeo ya Mitihani Pekee":
    st.header("8. Jedwali la Matokeo ya Mitihani Pekee")
    if st.session_state.almar_mitihani.empty:
        st.warning("Hakuna data ya mitihani.")
    else:
        st.dataframe(st.session_state.almar_mitihani, use_container_width=True)

# ------------------------------------------------------------------
# KIPENGELE 9: MATOKEO YA MAJARIBIO & MITIHANI (AVERAGE)
# ------------------------------------------------------------------
elif chaguo == "9. Matokeo ya Majaribio & Mitihani (Average)":
    st.header("9. Wastani wa Majaribio (30%) na Mitihani (70%)")
    if st.session_state.almar_majaribio.empty or st.session_state.almar_mitihani.empty:
        st.warning("Hakikisha umejaza majaribio na mitihani kikamilifu.")
    else:
        df_avg = st.session_state.wanafunzi_db.copy()
        for s in st.session_state.masomo_shule:
            maj_vals = pd.to_numeric(st.session_state.almar_majaribio[f"{s} (30%)"], errors='coerce').fillna(0)
            mit_vals = pd.to_numeric(st.session_state.almar_mitihani[f"{s} (70%)"], errors='coerce').fillna(0)
            df_avg[s] = np.round(maj_vals + mit_vals, 1)
            
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

            for somo in st.session_state.masomo_shule:
                if somo not in masomo_yake:
                    taarifa[f"{somo} MK"] = "-"
                    taarifa[f"{somo} GR"] = "-"
                    continue

                cwt = pd.to_numeric(st.session_state.almar_majaribio.loc[idx, f"{somo} (30%)"], errors='coerce')
                eet = pd.to_numeric(st.session_state.almar_mitihani.loc[idx, f"{somo} (70%)"], errors='coerce')
                
                if pd.isna(cwt) and pd.isna(eet):
                    taarifa[f"{somo} MK"] = "-"
                    taarifa[f"{somo} GR"] = "-"
                    continue
                    
                wastani = round(float(cwt if not pd.isna(cwt) else 0) + float(eet if not pd.isna(eet) else 0), 1)
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

            if len(pointi_za_masomo) >= 7:
                pointi_za_masomo.sort()
                pointi_saba = sum(pointi_za_masomo[:7])
                div = calculate_division(pointi_saba, len(pointi_za_masomo))
            else:
                pointi_saba = sum(pointi_za_masomo)
                div = 'IV' if len(pointi_za_masomo) > 0 else '0'
                
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
        
        # SUMMARY YA MASOMO
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
    st.header("11. Pakua Ripoti ya Mwanafunzi Mmoja mmoja (Ukurasa Mmoja wa PDF)")
    
    if len(names_list) == 0 or st.session_state.almar_majaribio.empty:
        st.warning("Hakikisha majina na alama zote zimejazwa kwanza.")
    else:
        mwanafunzi_sel = st.selectbox("Chagua mwanafunzi wa kumtengenezea PDF:", names_list)
        idx_mwa = names_list.index(mwanafunzi_sel)
        
        info = st.session_state.shule_info
        
        # Kusanya alama za mwanafunzi huyu mahususi
        data_somo_pdf = [["Somo", "Majaribio (30%)", "Mtihani (70%)", "Jumla (100%)", "Daraja"]]
        masomo_yake = st.session_state.masomo_wanafunzi.get(mwanafunzi_sel, st.session_state.masomo_shule)
        
        pointi_list = []
        for somo in st.session_state.masomo_shule:
            if somo in masomo_yake:
                cwt = pd.to_numeric(st.session_state.almar_majaribio.loc[idx_mwa, f"{somo} (30%)"], errors='coerce')
                eet = pd.to_numeric(st.session_state.almar_mitihani.loc[idx_mwa, f"{somo} (70%)"], errors='coerce')
                cwt = float(cwt) if not pd.isna(cwt) else 0.0
                eet = float(eet) if not pd.isna(eet) else 0.0
                tot = round(cwt + eet, 1)
                gr, pt = calculate_grade_and_points(tot)
                if gr: pointi_list.append(pt)
                data_somo_pdf.append([somo, str(cwt), str(eet), str(tot), gr if gr else "-"])
            else:
                data_somo_pdf.append([somo, "-", "-", "-", "Hajachagua"])
                
        # Kokotoa Div na Pointi
        if len(pointi_list) >= 7:
            pointi_list.sort()
            pts_saba = sum(pointi_list[:7])
            div_final = calculate_division(pts_saba, len(pointi_list))
        else:
            pts_saba = sum(pointi_list)
            div_final = "IV" if len(pointi_list) > 0 else "0"

        # Kazi ya kutengeneza ReportLab PDF kwenye kumbukumbu (Memory Buffer)
        def tengeneza_pdf_mwanafunzi():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
            story = []
            
            styles = getSampleStyleSheet()
            style_head = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], alignment=1, spaceAfter=5)
            style_normal = ParagraphStyle('NormalStyle', parent=styles['Normal'], spaceAfter=15, fontSize=11)
            
            # Vichwa vya Habari vya Shule
            story.append(Paragraph(f"<b>{info['wizara']}</b>", style_head))
            story.append(Paragraph(f"<b>{info['wilaya']} | {info['mkoa']}</b>", style_head))
            story.append(Paragraph(f"<b>{info['shule']} (CENTRE: {info['namba_shule']})</b>", style_head))
            story.append(Paragraph(f"<u>{info['aina_mtihani']} ({info['mwaka']})</u>", style_head))
            story.append(Spacer(1, 15))
            
            # Taarifa Binafsi
            jinsia_mwa = st.session_state.wanafunzi_db.loc[idx_mwa, 'Jinsia (M/F)']
            namba_mwa = st.session_state.wanafunzi_db.loc[idx_mwa, 'Namba ya Usajili']
            txt_binafsi = f"<b>Jina la Mwanafunzi:</b> {mwanafunzi_sel} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Jinsia:</b> {jinsia_mwa} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Namba ya Usajili:</b> {namba_mwa}"
            story.append(Paragraph(txt_binafsi, style_normal))
            
            # Jedwali la Alama
            t = Table(data_somo_pdf, colWidths=[200, 80, 80, 80, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (0,1), (0,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
            
            # Muhtasari wa Mwanafunzi
            txt_summary = f"<b>JUMLA YA POINTI (TOP 7):</b> {pts_saba} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>DARASA (DIVISION):</b> DIVISION {div_final}"
            story.append(Paragraph(txt_summary, style_normal))
            
            # Saini
            story.append(Spacer(1, 40))
            data_saini = [["..........................................", ".........................................."],
                          ["Saini ya Mkuu wa Shule", "Saini ya Mzazi/Mlezi"]]
            tsaini = Table(data_saini, colWidths=[260, 260])
            tsaini.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            story.append(tsaini)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        # Pakua PDF ya mwanafunzi huyu
        pdf_data = tengeneza_pdf_mwanafunzi()
        st.download_button(
            label=f"Pakua Ripoti ya {mwanafunzi_sel} (PDF)",
            data=pdf_data,
            file_name=f"Ripoti_{mwanafunzi_sel.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
