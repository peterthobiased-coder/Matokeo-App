import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="School Results & Report System", layout="wide")

# --- KAZI ZA ZIADA / UTANGAULIZI ---
def calculate_grade(score):
    if pd.isna(score) or score == "" or score == "-": return "-"
    try: score = float(score)
    except: return "-"
    if score >= 75: return "A"
    elif score >= 65: return "B"
    elif score >= 45: return "C"
    elif score >= 30: return "D"
    else: return "F"

def grade_points(grade):
    return {"A": 1, "B": 2, "C": 3, "D": 4, "F": 5}.get(grade, 0)

def calculate_division(total_points, subjects_counted):
    if subjects_counted < 7: return "N/A (< 7 Masomo)"
    if total_points >= 7 and total_points <= 17: return "I"
    elif total_points <= 21: return "II"
    elif total_points <= 25: return "III"
    elif total_points <= 29: return "IV"
    else: return "0"

# --- INITIALIZE SESSION STATES ---
if 'school_info' not in st.session_state:
    st.session_state.school_info = {
        "council": "KYERWA DISTRICT COUNCIL",
        "region": "KAGERA",
        "school": "S3060 KAMULI SECONDARY SCHOOL",
        "exam_title": "FORM THREE TERMINAL EXAMINATION RESULTS"
    }
if 'students' not in st.session_state:
    st.session_state.students = pd.DataFrame(columns=['S/N', 'NAME', 'SEX'])
if 'registered_subjects' not in st.session_state:
    st.session_state.registered_subjects = {}  # {'student_sn': [list of subjects]}
if 'test_marks' not in st.session_state:
    st.session_state.test_marks = pd.DataFrame()
if 'exam_marks' not in st.session_state:
    st.session_state.exam_marks = pd.DataFrame()

ALL_SUBJECTS = ["CIVICS", "HISTORY", "GEOGRAPHY", "KISWAHILI", "ENGLISH", "PHYSICS", "CHEMISTRY", "BIOLOGY", "BASIC MATH"]

# --- SIDEBAR MENU ---
st.sidebar.title("MENU YA MFUMO")
page = st.sidebar.radio("Nenda Sehemu:", [
    "⚙️ Mipangilio ya Shule", 
    "📝 Sajili Wanafunzi & Masomo", 
    "📊 Ingiza Alama (Majaribio)", 
    "✍️ Ingiza Alama (Mitihani)", 
    "📋 Ripoti ya Matokeo ya NECTA"
])

# --- 1. MIPANGILIO YA SHULE ---
if page == "⚙️ Mipangilio ya Shule":
    st.subheader("Usimamizi wa Vichwa vya Habari (Headers)")
    st.session_state.school_info["council"] = st.text_input("Halmashauri / Wilaya (DISTRICT COUNCIL):", st.session_state.school_info["council"])
    st.session_state.school_info["region"] = st.text_input("Mkoa (REGION):", st.session_state.school_info["region"])
    st.session_state.school_info["school"] = st.text_input("Jina la Shule (SCHOOL NAME):", st.session_state.school_info["school"])
    st.session_state.school_info["exam_title"] = st.text_input("Jina la Mtihani (EXAM TITLE):", st.session_state.school_info["exam_title"])
    st.success("Mipangilio imehifadhiwa!")

# --- 2. SAJILI WANAFUNZI & MASOMO ---
elif page == "📝 Sajili Wanafunzi & Masomo":
    st.subheader("Sajili Wanafunzi na Chagua Masomo Wanayosoma")
    
    with st.form("reg_form", clear_on_submit=True):
        sn = st.text_input("Namba ya Mwanafunzi (S/N):")
        name = st.text_input("Majina Kamili (NAME):")
        sex = st.selectbox("Jinsia (SEX):", ["M", "F"])
        chosen_subs = st.multiselect("Chagua Masomo anayosoma mwanafunzi huyu:", ALL_SUBJECTS, default=ALL_SUBJECTS)
        submitted = st.form_submit_button("Sajili Mwanafunzi")
        
        if submitted and sn and name:
            new_stud = pd.DataFrame([[sn, name.upper(), sex]], columns=['S/N', 'NAME', 'SEX'])
            st.session_state.students = pd.concat([st.session_state.students, new_stud], ignore_index=True)
            st.session_state.registered_subjects[sn] = chosen_subs
            st.success(f"{name.upper()} amesajiliwa na masomo yake!")

    st.write("### Orodha ya Wanafunzi Waliosajiliwa")
    st.dataframe(st.session_state.students, use_container_width=True)

# --- 3. INGIZA ALAMA (MAJARIBIO) ---
elif page == "📊 Ingiza Alama (Majaribio)":
    st.subheader("Jaza Alama za Majaribio / Test (Asilimia 100)")
    if st.session_state.students.empty:
        st.warning("Tafadhali sajili wanafunzi kwanza.")
    else:
        if st.session_state.test_marks.empty or len(st.session_state.test_marks) != len(st.session_state.students):
            st.session_state.test_marks = st.session_state.students[['S/N', 'NAME', 'SEX']].copy()
            for sub in ALL_SUBJECTS: st.session_state.test_marks[sub] = np.nan
        
        st.write("Ingiza alama hapa chini (Majaribio):")
        edited_test = st.data_editor(st.session_state.test_marks, use_container_width=True)
        if st.button("Hifadhi Alama za Majaribio"):
            st.session_state.test_marks = edited_test
            st.success("Alama za Majaribio zimehifadhiwa!")

# --- 4. INGIZA ALAMA (MITIHANI) ---
elif page == "✍️ Ingiza Alama (Mitihani)":
    st.subheader("Jaza Alama za Mitihani Kuu / NECTA Format (Asilimia 100)")
    if st.session_state.students.empty:
        st.warning("Tafadhali sajili wanafunzi kwanza.")
    else:
        if st.session_state.exam_marks.empty or len(st.session_state.exam_marks) != len(st.session_state.students):
            st.session_state.exam_marks = st.session_state.students[['S/N', 'NAME', 'SEX']].copy()
            for sub in ALL_SUBJECTS: st.session_state.exam_marks[sub] = np.nan
        
        st.write("Ingiza alama hapa chini (Mitihani):")
        edited_exam = st.data_editor(st.session_state.exam_marks, use_container_width=True)
        if st.button("Hifadhi Alama za Mitihani"):
            st.session_state.exam_marks = edited_exam
            st.success("Alama za Mitihani zimehifadhiwa!")

# --- 5. RIPOTI YA MATOKEO YA NECTA ---
elif page == "📋 Ripoti ya Matokeo ya NECTA":
    info = st.session_state.school_info
    st.markdown(f"<h3 style='text-align: center;'>{info['council']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>{info['school']} ({info['region']})</h4>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='text-align: center;'>{info['exam_title']}</h5>", unsafe_allow_html=True)
    
    if st.session_state.exam_marks.empty or st.session_state.test_marks.empty:
        st.warning("Hakuna alama zilizopatikana kwenye Majaribio au Mitihani.")
    else:
        # Piga wastani: 30% Test + 70% Exam
        final_df = st.session_state.students[['S/N', 'NAME', 'SEX']].copy()
        
        total_points_list = []
        division_list = []
        
        for index, row in final_df.iterrows():
            sn = row['S/N']
            allowed_subs = st.session_state.registered_subjects.get(sn, ALL_SUBJECTS)
            student_points = []
            
            for sub in ALL_SUBJECTS:
                if sub in allowed_subs:
                    t_mark = st.session_state.test_marks.loc[st.session_state.test_marks['S/N'] == sn, sub].values[0]
                    e_mark = st.session_state.exam_marks.loc[st.session_state.exam_marks['S/N'] == sn, sub].values[0]
                    
                    # Kama alama hazikujazwa, weka 0 au chukulia iliyopo
                    t_mark = float(t_mark) if not pd.isna(t_mark) else 0
                    e_mark = float(e_mark) if not pd.isna(e_mark) else 0
                    
                    # Fomula ya wastani wa jumla ya muhula: (Test*0.3) + (Exam*0.7)
                    final_score = (t_mark * 0.3) + (e_mark * 0.7)
                    grade = calculate_grade(final_score)
                    
                    final_df.at[index, sub] = round(final_score, 1)
                    final_df.at[index, f"{sub}_GD"] = grade
                    
                    pts = grade_points(grade)
                    if pts > 0: student_points.append(pts)
                else:
                    final_df.at[index, sub] = "-"
                    final_df.at[index, f"{sub}_GD"] = "-"
            
            student_points.sort()
            top_7 = sum(student_points[:7])
            subs_count = len(student_points)
            
            total_points_list.append(top_7 if subs_count >= 7 else np.nan)
            division_list.append(calculate_division(top_7, subs_count))
            
        final_df['TOTAL POINTS'] = total_points_list
        final_df['DIVISION'] = division_list
        
        st.dataframe(final_df, use_container_width=True)
        
        # DOWNLOAD BUTTON
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Pakua Ripoti Kamili (Excel / CSV)",
            data=csv,
            file_name=f"Matokeo_{info['school'].replace(' ', '_')}.csv",
            mime="text/csv"
        )
