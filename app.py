import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 설정: 페이지 기본 세팅 ---
st.set_page_config(page_title="S.A.Y COIN System", page_icon="🪙")

# --- 다국어 텍스트 사전 (Language Dictionary) ---
LANG = {
    "KO": {
        "title": "S.A.Y COIN 지급 시스템",
        "login_title": "🏗️ S.A.Y COIN 로그인",
        "id_label": "아이디",
        "pw_label": "비밀번호",
        "login_btn": "로그인",
        "login_fail": "아이디 또는 비밀번호가 잘못되었습니다.",
        "logout_btn": "로그아웃",
        "welcome": "접속자: {} 님",
        "tab1": "💰 코인 지급",
        "tab2": "📋 지급 기록",
        "header_reward": "근로자 안전 행동 보상",
        "passport_label": "Passport No (5자리)",
        "coin_label": "Coin Serial (0001~3000)",
        "cat_main": "대분류",
        "cat_sub": "중분류",
        "cat_detail": "소분류 (상세 사유)",
        "select_default": "- 선택하세요 -",
        "note_label": "비고 (선택사항)",
        "submit_btn": "지급 등록",
        "warning_fill": "모든 필수 항목(번호, 분류)을 선택해주세요.",
        "success_msg": "저장되었습니다!",
        "fail_msg": "저장에 실패했습니다.",
        "home_btn": "홈 화면으로",
        "retry_btn": "재시도",
        "refresh_btn": "내역 새로고침",
        "no_data": "아직 지급한 기록이 없습니다.",
        "header_history": "나의 지급 내역",
        "table_cols": ["시간", "관리자ID", "이름", "패스포트", "코인번호", "대분류", "중분류", "소분류", "비고"]
    },
    "EN": {
        "title": "S.A.Y COIN System",
        "login_title": "🏗️ Login",
        "id_label": "ID",
        "pw_label": "Password",
        "login_btn": "Login",
        "login_fail": "Invalid ID or Password.",
        "logout_btn": "Logout",
        "welcome": "User: {}",
        "tab1": "💰 Reward Coin",
        "tab2": "📋 History",
        "header_reward": "Safety Action Reward",
        "passport_label": "Passport No (5 digits)",
        "coin_label": "Coin Serial (0001~3000)",
        "cat_main": "Category (Main)",
        "cat_sub": "Activity (Sub)",
        "cat_detail": "Detail",
        "select_default": "- Select -",
        "note_label": "Note (Optional)",
        "submit_btn": "Submit",
        "warning_fill": "Please fill in all required fields.",
        "success_msg": "Saved Successfully!",
        "fail_msg": "Save Failed.",
        "home_btn": "Return Home",
        "retry_btn": "Retry",
        "refresh_btn": "Refresh",
        "no_data": "No records found.",
        "header_history": "My History",
        "table_cols": ["Time", "ManagerID", "Name", "Passport", "CoinNo", "Main", "Sub", "Detail", "Note"]
    }
}

# --- 안전 데이터 (KO/EN) ---
# 구조: 대분류 -> 중분류 -> 소분류 리스트
SAFETY_DATA = {
    "KO": {
        "개인 보호구 (PPE)": {
            "안전모": ["턱끈 체결 철저", "올바른 착용 상태", "파손품 자진 교체 요청"],
            "안전벨트": ["고소작업 시 체결 철저", "이중 안전고리 사용", "올바른 착용"],
            "안전화": ["뒤꿈치 꺾어 신지 않음", "끈 조임 상태 양호"],
            "보안경/마스크": ["분진 발생 작업 시 착용", "용접 보안면 착용"]
        },
        "안전 행동 (Behavior)": {
            "정리정돈": ["작업장 통로 확보", "자재 적재 상태 양호", "작업 후 청소 상태 우수"],
            "TBM/교육": ["TBM 적극적 참여", "동료에게 위험 전파", "스트레칭 우수"],
            "장비 유도": ["신호수 위치 준수", "장비 반경 내 접근 금지 준수"]
        },
        "위험 발굴 (Risk)": {
            "아차사고": ["아차사고 신고 및 공유", "불안전한 상태 개선 건의"],
            "작업 중지": ["위험 상황 인지 후 작업 중지권 행사"]
        }
    },
    "EN": {
        "Personal Protective Equipment (PPE)": {
            "Safety Helmet": ["Chin strap secured", "Properly worn", "Request replacement for damage"],
            "Safety Harness": ["Hook secured at height", "Double lanyard usage", "Properly worn"],
            "Safety Shoes": ["Heels not folded", "Laces tied properly"],
            "Goggles/Mask": ["Worn during dusty work", "Welding shield used"]
        },
        "Safe Behavior": {
            "Housekeeping": ["Walkways clear", "Material stacking safe", "Clean after work"],
            "TBM/Training": ["Active participation in TBM", "Warning others of risks", "Excellent stretching"],
            "Equipment Signaling": ["Signaler position maintained", "Stayed out of radius"]
        },
        "Risk Identification": {
            "Near Miss": ["Reported near miss", "Suggested safety improvement"],
            "Stop Work": ["Exercised Stop Work Authority"]
        }
    }
}

# --- 데이터베이스 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 헬퍼 함수 ---
def get_text(key):
    """현재 언어 설정에 맞는 텍스트 반환"""
    lang_code = st.session_state.get('language', 'KO')
    return LANG[lang_code][key]

def login(username, password):
    try:
        users_df = conn.read(worksheet="Users", ttl=0)
        # 숫자/문자 호환 처리
        users_df['ID'] = users_df['ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        users_df['PW'] = users_df['PW'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        username = str(username).strip()
        password = str(password).strip()

        user = users_df[(users_df['ID'] == username) & (users_df['PW'] == password)]
        if not user.empty:
            return user.iloc[0]['Name']
        return None
    except Exception:
        return None

# --- 팝업(Dialog) 함수 (Streamlit 1.34+ 권장) ---
@st.dialog("Result")
def show_result_popup(is_success, error_msg=None):
    if is_success:
        st.success(get_text("success_msg"))
        if st.button(get_text("home_btn"), key="popup_home"):
            st.rerun()
    else:
        st.error(f"{get_text('fail_msg')}\n({error_msg})")
        if st.button(get_text("retry_btn"), key="popup_retry"):
            st.rerun()

# --- 메인 로직 ---
def main():
    # 1. 세션 초기화
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'language' not in st.session_state:
        st.session_state['language'] = "KO"

    # 2. 사이드바 (언어 설정 및 정보)
    with st.sidebar:
        st.header("Settings")
        # 언어 전환 토글
        lang_choice = st.radio("Language", ["Korean", "English"], 
                               index=0 if st.session_state['language'] == "KO" else 1)
        st.session_state['language'] = "KO" if lang_choice == "Korean" else "EN"
        
        if st.session_state['logged_in']:
            st.divider()
            st.info(get_text("welcome").format(st.session_state['user_name']))
            if st.button(get_text("logout_btn")):
                st.session_state['logged_in'] = False
                st.rerun()

    # 3. 로그인 화면
    if not st.session_state['logged_in']:
        st.title(get_text("login_title"))
        with st.form("login_form"):
            username = st.text_input(get_text("id_label"))
            password = st.text_input(get_text("pw_label"), type="password")
            submit = st.form_submit_button(get_text("login_btn"))
            
            if submit:
                user_name = login(username, password)
                if user_name:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_name
                    st.session_state['user_id'] = username
                    st.rerun()
                else:
                    st.error(get_text("login_fail"))

    # 4. 메인 앱 화면
    else:
        st.title(get_text("title"))
        tab1, tab2 = st.tabs([get_text("tab1"), get_text("tab2")])

        # --- TAB 1: 코인 지급 ---
        with tab1:
            st.subheader(get_text("header_reward"))
            
            # 드롭다운 데이터 로드 (언어에 맞게)
            current_data = SAFETY_DATA[st.session_state['language']]
            default_opt = get_text("select_default")

            # Form 시작
            # 주의: Streamlit Form 안에서는 동적 상호작용(값 변경 시 리로드)이 제한적임.
            # 따라서 3단 드롭다운의 실시간 갱신을 위해 Form을 쓰지 않거나, 
            # selectbox를 form 밖에 두고 마지막 제출만 버튼으로 처리하는 방식을 씀.
            # 여기서는 UX를 위해 Form 없이 구성하고 마지막에 버튼으로 처리함.

            col1, col2 = st.columns(2)
            passport_no = col1.text_input(get_text("passport_label"), max_chars=5)
            coin_no = col2.text_input(get_text("coin_label"), max_chars=4)

            # [1] 대분류
            main_cats = [default_opt] + list(current_data.keys())
            selected_main = st.selectbox(get_text("cat_main"), main_cats)

            # [2] 중분류 (대분류 선택 시 활성화)
            sub_cats = [default_opt]
            is_sub_disabled = True
            if selected_main != default_opt:
                is_sub_disabled = False
                sub_cats += list(current_data[selected_main].keys())
            
            selected_sub = st.selectbox(get_text("cat_sub"), sub_cats, disabled=is_sub_disabled)

            # [3] 소분류 (중분류 선택 시 활성화)
            detail_cats = [default_opt]
            is_detail_disabled = True
            if selected_sub != default_opt:
                is_detail_disabled = False
                detail_cats += current_data[selected_main][selected_sub]

            selected_detail = st.selectbox(get_text("cat_detail"), detail_cats, disabled=is_detail_disabled)

            # 비고
            note = st.text_area(get_text("note_label"), height=80)

            # 제출 버튼
            if st.button(get_text("submit_btn"), type="primary", use_container_width=True):
                # 유효성 검사
                if (not passport_no or not coin_no or 
                    selected_main == default_opt or 
                    selected_sub == default_opt or 
                    selected_detail == default_opt):
                    st.warning(get_text("warning_fill"))
                else:
                    # 저장 로직
                    new_data = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Manager_ID": st.session_state['user_id'],
                        "Manager_Name": st.session_state['user_name'],
                        "Passport_No": passport_no,
                        "Coin_No": coin_no,
                        "Main_Cat": selected_main,
                        "Sub_Cat": selected_sub,
                        "Detail_Cat": selected_detail,
                        "Note": note
                    }])
                    
                    try:
                        existing_data = conn.read(worksheet="Logs", ttl=0)
                        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
                        conn.update(worksheet="Logs", data=updated_data)
                        
                        # 성공 팝업
                        show_result_popup(True)
                        
                    except Exception as e:
                        # 실패 팝업
                        show_result_popup(False, str(e))

        # --- TAB 2: 지급 기록 ---
        with tab2:
            st.subheader(get_text("header_history"))
            if st.button(get_text("refresh_btn")):
                st.rerun()
                
            try:
                all_logs = conn.read(worksheet="Logs", ttl=0)
                my_logs = all_logs[all_logs['Manager_ID'] == st.session_state['user_id']]
                
                if not my_logs.empty:
                    my_logs = my_logs.sort_values(by="Timestamp", ascending=False)
                    # 테이블 컬럼명 번역 적용 (보여주기용)
                    display_df = my_logs.copy()
                    # (주의: 실제 컬럼 갯수와 table_cols 갯수가 맞지 않으면 에러날 수 있으니 단순 표시)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(get_text("no_data"))
            except Exception:
                st.error(get_text("fail_msg"))

if __name__ == "__main__":
    main()
