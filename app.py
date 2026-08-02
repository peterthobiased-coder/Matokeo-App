import streamlit as st
import pandas as pd
import numpy as np

# 1. Caching kwa ajili ya usalama na kasi ya mfumo
@st.cache_data
def calculate_grade_and_points(score):
    if pd.isna(score) or score == '':
        return None, None
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
    if selected_subjects_count < 7:
        return 'I-VII (Masomo Chini ya 7)'
    if total_points >= 7 and total_points <= 17: return 'I'
    elif total_points <= 21: return 'II'
    elif total_points <= 25: return 'III'
    elif total_points <= 33: return 'IV'
    else: return '0'

# 2. Muundo wa Ukurasa
st.set_page_config(page_title="Mfumo wa Matokeo O-Level", layout="wide")

st.title("Mfumo wa Kuchakata Matokeo ya Mtihani (O-Level)")
st.write("Weka taarifa za shule, sajili masomo, na weka alama kupata ripoti kamili na summary ya masomo chini.")

# 3. Sehemu ya Taarifa za Shule / Mtihani
st.sidebar.header("Taarifa za Shule & Mtihani")
mkoa = st.sidebar.text_input("Mkoa", "MWANZA")
wilaya = st.sidebar.text_input("Wilaya/Halmashauri", "BUCHOSA DISTRICT COUNCIL")
shule = st.sidebar.text_input("Jina la Shule", "CHEMA SECONDARY SCHOOL")
namba_shule = st.sidebar.text_input("Namba ya Kituo (Centre No)", "S7647")
aina_mtihani = st.sidebar.text_input("Aina ya Mtihani", "FORM FOUR LAKE ZONE MOCK EXAMINATION")
mwaka = st.sidebar.text_input("Mwaka/Mwezi", "MAY 2026")

# 4. Usajili wa Masomo yanayofundishwa
st.sidebar.header("Usajili wa Masomo")
masomo_yote = ['CIVICS', 'HISTORY', 'GEOGRAPHY', 'KISWAHILI', 'ENGLISH LANGUAGE', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'BASIC MATHEMATICS', 'LITERATURE IN ENGLISH']
masomo_yaliyosajiliwa = st.sidebar.multiselect("Chagua masomo yanayochakatwa shuleni", masomo_yote, default=masomo_yote)

# 5. Kuingiza Alama za Wanafunzi
st.header("Ingiza Alama za Wanafunzi")
if 'data_wanafunzi' not in st.session_state:
    st.session_state.data_wanafunzi = pd.DataFrame(columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])

col_add1, col_add2 = st.columns([3, 1])
with col_add1:
    idadi = st.number_input("Idadi ya wanafunzi unaotaka kuwaongeza kwa mkupuo:", min_value=1, value=5, step=1)
with col_add2:
    if st.button("Tengeneza Nafasi za Wanafunzi"):
        nyongeza = pd.DataFrame(index=range(idadi), columns=['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili'])
        # Weka mpangilio wa Namba za Usajili kiotomatiki
        kuanzia = len(st.session_state.data_wanafunzi) + 1
        nyongeza['Namba ya Usajili'] = [f"{namba_shule}/{str(i).zfill(4)}" for i in range(kuanzia, kuanzia + idadi)]
        nyongeza['Jinsia (M/F)'] = 'F' # Default gender
        st.session_state.data_wanafunzi = pd.concat([st.session_state.data_wanafunzi, nyongeza], ignore_index=True)

# Tengeneza nguzo (columns) za alama za masomo yaliyochaguliwa (Majaribio 30% na Mtihani 70%)
safu_za_kuhariri = ['Jina la Mwanafunzi', 'Jinsia (M/F)', 'Namba ya Usajili']
for somo in masomo_yaliyosajiliwa:
    safu_za_kuhariri.append(f"{somo} (30%)")
    safu_za_kuhariri.append(f"{somo} (70%)")

# Hakikisha dataframe ina nguzo zote zinazohitajika
for col in safu_za_kuhariri:
    if col not in st.session_state.data_wanafunzi.columns:
        st.session_state.data_wanafunzi[col] = np.nan

# Jedwali la kuingizia alama (Data Editor)
df_inayohaririwa = st.data_editor(
    st.session_state.data_wanafunzi[safu_za_kuhariri],
    num_rows="dynamic",
    use_container_width=True
)

if st.button("Hifadhi na Uchakate Matokeo kwa Ujumla"):
    st.session_state.data_wanafunzi = df_inayohaririwa.copy()
    
    df_matokeo = df_inayohaririwa.copy()
    
    # Kufuta safu zisizo na majina kabla ya kuchakata
    df_matokeo = df_matokeo.dropna(subset=['Jina la Mwanafunzi'])
    
    if not df_matokeo.empty:
        orodha_ya_ripoti = []
        
        # Kamusi (dictionary) kwa ajili ya kukusanya summary ya kila somo
        summary_masomo = {somo: {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0, 'Jumla_Alama': 0.0, 'Wanafunzi_Wanaosoma': 0} for somo in masomo_yaliyosajiliwa}
        
        # Uchakataji wa mwanafunzi mmoja mmoja
        for idx, mwanafunzi in df_matokeo.iterrows():
            taarifa_mwanafunzi = {
                'S/N': idx + 1,
                'NAME OF CANDIDATE': mwanafunzi['Jina la Mwanafunzi'],
                'SEX': mwanafunzi['Jinsia (M/F)'],
                'INDEX NO': mwanafunzi['Namba ya Usajili']
            }
            
            pointi_za_masomo = []
            jumla_ya_alama_zote = 0.0
            masomo_yaliyofanywa_hesabu = 0
            
            for somo in masomo_yaliyosajiliwa:
                try:
                    cwt = float(mwanafunzi.get(f"{somo} (30%)", 0)) if not pd.isna(mwanafunzi.get(f"{somo} (30%)")) else 0.0
                    eet = float(mwanafunzi.get(f"{somo} (70%)", 0)) if not pd.isna(mwanafunzi.get(f"{somo} (70%)")) else 0.0
                    
                    # Kama nguzo zote mbili zipo tupu, mwanafunzi hasomi somo hili
                    if pd.isna(mwanafunzi.get(f"{somo} (30%)")) and pd.isna(mwanafunzi.get(f"{somo} (70%)")):
                        taarifa_mwanafunzi[f"{somo} MK"] = "-"
                        taarifa_mwanafunzi[f"{somo} GR"] = "-"
                        continue
                        
                    wastani_somo = round(cwt + eet, 1)
                    daraja, pointi = calculate_grade_and_points(wastani_somo)
                    
                    taarifa_mwanafunzi[f"{somo} MK"] = wastani_somo
                    taarifa_mwanafunzi[f"{somo} GR"] = daraja
                    
                    if daraja:
                        pointi_za_masomo.append(pointi)
                        jumla_ya_alama_zote += wastani_somo
                        masomo_yaliyofanywa_hesabu += 1
                        
                        # Ongeza kwenye takwimu za summary ya masomo
                        summary_masomo[somo][daraja] += 1
                        summary_masomo[somo]['Jumla_Alama'] += wastani_somo
                        summary_masomo[somo]['Wanafunzi_Wanaosoma'] += 1
                        
                except Exception:
                    taarifa_mwanafunzi[f"{somo} MK"] = "-"
                    taarifa_mwanafunzi[f"{somo} GR"] = "-"
            
            # Hesabu ya Pointi, Wastani wa Mwanafunzi, Division na GPA yake
            if len(pointi_za_masomo) >= 7:
                pointi_za_masomo.sort()
                pointi_saba_bora = sum(pointi_za_masomo[:7])
                gpa_mwanafunzi = round(sum(pointi_za_masomo) / len(pointi_za_masomo), 4)
                div = calculate_division(pointi_saba_bora, len(pointi_za_masomo))
            else:
                pointi_saba_bora = sum(pointi_za_masomo) if pointi_za_masomo else 0
                gpa_mwanafunzi = round(sum(pointi_za_masomo) / len(pointi_za_masomo), 4) if pointi_za_masomo else 5.0
                div = 'IV' if len(pointi_za_masomo) > 0 else '0'
                
            taarifa_mwanafunzi['TOTAL MARKS'] = round(jumla_ya_alama_zote, 2)
            taarifa_mwanafunzi['AVG'] = round(jumla_ya_alama_zote / masomo_yaliyofanywa_hesabu, 1) if masomo_yaliyofanywa_hesabu > 0 else 0
            taarifa_mwanafunzi['POINTS'] = pointi_saba_bora
            taarifa_mwanafunzi['DIV'] = div
            taarifa_mwanafunzi['GPA'] = gpa_mwanafunzi
            
            orodha_ya_ripoti.append(taarifa_mwanafunzi)
            
        df_ripoti_kamili = pd.DataFrame(orodha_ya_ripoti)
        
        # Panga wanafunzi kulingana na ufaulu wao (kwanza kwa Division, kisha kwa pointi ndogo, na mwisho kwa wastani mkubwa)
        if 'POINTS' in df_ripoti_kamili.columns:
            df_ripoti_kamili = df_ripoti_kamili.sort_values(by=['DIV', 'POINTS', 'AVG'], ascending=[True, True, False]).reset_drop_index(drop=True)
            df_ripoti_kamili['POSITION'] = df_ripoti_kamili.index + 1
            
        # --- SEHEMU YA KUCHAPA RIPOTI ---
        st.markdown(f"<h3 style='text-align: center;'>{wilaya}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{shule} - kituo NO: {namba_shule}</h4>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{aina_mtihani}, {mwaka}</h4>", unsafe_allow_html=True)
        
        st.subheader("JEDWALI LA MATOKEO YA WANAFUNZI")
        st.dataframe(df_ripoti_kamili, use_container_width=True)
        
        # --- KIPENGELE KIPYA: SUMMARY YA MASOMO (SUBJECT PERFORMANCE SUMMARY) ---
        st.write("---")
        st.subheader("SUMMARY YA UFAULU WA MASOMO (SUBJECT PERFORMANCE SUMMARY)")
        
        rows_summary = []
        sn_somo = 1
        for somo, takwimu in summary_masomo.items():
            wanafunzi_waliopo = takwimu['Wanafunzi_Wanaosoma']
            if wanafunzi_waliopo > 0:
                wastani_wa_somo = round(takwimu['Jumla_Alama'] / wanafunzi_waliopo, 1)
                
                # Uhesabuji wa GPA ya Somo (Jumla ya pointi za madaraja / idadi ya wanafunzi)
                jumla_ya_pointi_za_somo = (takwimu['A']*1) + (takwimu['B']*2) + (takwimu['C']*3) + (takwimu['D']*4) + (takwimu['F']*5)
                gpa_somo = round(jumla_ya_pointi_za_somo / wanafunzi_waliopo, 4)
                
                # Kutafuta Daraja la Somo kutokana na GPA
                if gpa_somo >= 1.0 and gpa_somo < 2.0: daraja_somo = 'A'
                elif gpa_somo < 3.0: daraja_somo = 'B'
                elif gpa_somo < 4.0: daraja_somo = 'C'
                elif gpa_somo < 4.8: daraja_somo = 'D'
                else: daraja_somo = 'F'
                
                kufaulu = takwimu['A'] + takwimu['B'] + takwimu['C'] + takwimu['D']
                kufeli = takwimu['F']
                
                rows_summary.append({
                    'S/N': sn_somo,
                    'SUBJECT NAME': somo,
                    'A': takwimu['A'],
                    'B': takwimu['B'],
                    'C': takwimu['C'],
                    'D': takwimu['D'],
                    'F': takwimu['F'],
                    'TOTAL REG': wanafunzi_waliopo,
                    'AVG MARKS': wastani_wa_somo,
                    'GRADE': daraja_somo,
                    'GPA': gpa_somo,
                    'PASS': kufaulu,
                    'FAIL': kufeli
                })
                sn_somo += 1
                
        df_summary_masomo = pd.DataFrame(rows_summary)
        
        # Kupanga masomo kwa nafasi (Rank) kulingana na ufaulu wa GPA yao (ndogo ndio ya kwanza)
        if not df_summary_masomo.empty:
            df_summary_masomo = df_summary_masomo.sort_values(by='GPA', ascending=True).reset_index(drop=True)
            df_summary_masomo['RANK'] = df_summary_masomo.index + 1
            # Kupanga upya nguzo ili S/N zifuate mtiririko sahihi wa nafasi zao
            df_summary_masomo['S/N'] = df_summary_masomo.index + 1
            
            st.dataframe(df_summary_masomo, use_container_width=True)
        else:
            st.info("Hakuna data ya kutosha kuzalisha summary ya masomo.")
            
        # 6. Vifungo vya kupakua ripoti (Download Buttons)
        st.write("---")
        csv_kamili = df_ripoti_kamili.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Pakua Ripoti Kamili (Excel / CSV)",
            data=csv_kamili,
            file_name=f"Matokeo_{shule}_{mwaka}.csv",
            mime="text/csv"
                )
