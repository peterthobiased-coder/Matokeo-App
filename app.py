import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="School Results & Report System", layout="wide")

# Mfumo wa Grading wa NECTA (O-Level)
def calculate_grade(score):
    if pd.isna(score) or score == "": return "-"
    try:
        score = float(score)
    except:
        return "-"
    if score >= 75: return "A"
    elif score >= 65: return "B"
    elif score >= 45: return "C"
    elif score >= 30: return "D"
    else: return "F"

def grade_points(grade):
    points = {"A": 1, "B": 2, "C": 3, "D": 4, "F": 5}
    return points.get(grade, 0)

def calculate_division(total_points, subjects_counted):
    if subjects_counted < 7:
        return "N/A (Masomo < 7)"
    if total_points >= 7 and total_points <= 17: return "I"
    elif total_points <= 21: return "II"
    elif total_points <= 25: return "III"
    elif total_points <= 29: return "IV"
    else: return "0"

# Hifadhi ya Data ya Muda (Session State)
if 'students' not in st.session_state:
    st.session_state.students = pd.DataFrame(columns=['S/N', 'NAME', 'SEX'])
if 'marks' not in st.session_state:
    st.session_state.marks = pd.DataFrame()

st.title("🏫 Mfumo wa Kuchakata Matokeo ya Mitihani (O-Level)")
st.sidebar.header("MENU KUU")
page = st.sidebar.radio("Chagua Sehemu:", ["Nyumbani", "Jaza Majina", "Jaza Mitihani", "Ripoti ya Matokeo"])

# --- NYUMBANI ---
if page == "Nyumbani":
    st.subheader("Karibu kwenye Mfumo wa Ripoti za Shule")
    st.write("Mfumo huu umerahisishwa kutoka kwenye Excel yako ili kusaidia uingizaji wa data na usalama wa matokeo ya wanafunzi.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumla ya Wanafunzi", len(st.session_state.students))
    
# --- JAZA MAJINA ---
elif page == "Jaza Majina":
    st.subheader("Sajili Majina ya Wanafunzi")
    
    with st.form("student_form", clear_on_submit=True):
        sn = st.text_input("Namba ya Mwanafunzi (S/N) mfano: S3060-0001")
        name = st.text_input("Majina Kamili (NAME)")
        sex = st.selectbox("Jinsia (SEX)", ["M", "F"])
        submitted = st.form_submit_button("Sajili")
        
        if submitted and sn and name:
            new_student = pd.DataFrame([[sn, name.upper(), sex]], columns=['S/N', 'NAME', 'SEX'])
            st.session_state.students = pd.concat([st.session_state.students, new_student], ignore_index=True)
            st.success(f"{name} amesajiliwa kikamilifu!")

    st.write("### Orodha ya Wanafunzi Waliosajiliwa")
    st.dataframe(st.session_state.students, use_container_width=True)

# --- JAZA MITIHANI ---
elif page == "Jaza Mitihani":
    st.subheader("Ingiza Alama za Mitihani")
    
    if st.session_state.students.empty:
        st.warning("Tafadhali sajili wanafunzi kwanza kwenye sehemu ya 'Jaza Majina'.")
    else:
        subjects = ["CIVICS", "HISTORY", "GEOGRAPHY", "KISWAHILI", "ENGLISH", "PHYSICS", "CHEMISTRY", "BIOLOGY", "BASIC MATH"]
        
        if st.session_state.marks.empty or len(st.session_state.marks) != len(st.session_state.students):
            st.session_state.marks = st.session_state.students[['S/N', 'NAME', 'SEX']].copy()
            for sub in subjects:
                if sub not in st.session_state.marks.columns:
                    st.session_state.marks[sub] = np.nan
        
        st.write("Hariri alama moja kwa moja kwenye jedwali hapa chini:")
        edited_df = st.data_editor(st.session_state.marks, use_container_width=True)
        
        if st.button("Hifadhi Alama"):
            st.session_state.marks = edited_df
            st.success("Alama zimehifadhiwa kikamilifu!")

# --- RIPOTI YA MATOKEO ---
elif page == "Ripoti ya Matokeo":
    st.subheader("Matokeo ya Jumla na Ripoti ya NECTA")
    
    if st.session_state.marks.empty:
        st.warning("Hakuna alama zilizopatikana. Tafadhali jaza alama kwanza.")
    else:
        results_df = st.session_state.marks.copy()
        subjects = ["CIVICS", "HISTORY", "GEOGRAPHY", "KISWAHILI", "ENGLISH", "PHYSICS", "CHEMISTRY", "BIOLOGY", "BASIC MATH"]
        
        total_points_list = []
        division_list = []
        
        for index, row in results_df.iterrows():
            student_points = []
            for sub in subjects:
                grade = calculate_grade(row[sub])
                results_df.at[index, f"{sub}_GD"] = grade
                pts = grade_points(grade)
                if pts > 0:
                    student_points.append(pts)
            
            student_points.sort()
            top_7_points = sum(student_points[:7])
            subjects_counted = len(student_points)
            
            total_points_list.append(top_7_points if subjects_counted >= 7 else np.nan)
            division_list.append(calculate_division(top_7_points, subjects_counted))
            
        results_df['TOTAL POINTS'] = total_points_list
        results_df['DIVISION'] = division_list
        
        st.dataframe(results_df, use_container_width=True)
        
        st.subheader("Pakua Matokeo")
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Pakua kama CSV (Excel)",
            data=csv,
            file_name="Matokeo_O_Level.csv",
            mime="text/csv",
        )
