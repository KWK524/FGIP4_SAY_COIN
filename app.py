import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 설정: 페이지 기본 세팅 ---
st.set_page_config(page_title="S.A.Y COIN System", page_icon="🪙")

# --- 다국어 텍스트 사전 ---
LANG = {
    "KO": {
        "title": "FGIP4 S.A.Y COIN",
        "login_title": "🏗️ FGIP4 로그인",
        "id_label": "아이디",
        "pw_label": "비밀번호",
        "login_btn": "로그인",
        "login_fail": "아이디/비번 확인 또는 권한 문의 필요.",
        "logout_btn": "로그아웃",
        "welcome": "접속자: {} 님 ({})",
        "tab1": "💰 코인 지급",
        "tab2": "📋 지급 기록",
        "tab3": "🏪 코인 사용(상품교환)",
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
        "success_msg": "처리되었습니다!",
        "fail_msg": "처리에 실패했습니다.",
        "ok_btn": "OK",
        "retry_btn": "재시도",
        "refresh_btn": "내역 새로고침",
        "no_data": "데이터가 없습니다.",
        "header_history": "나의 지급 내역",
        "redeem_search_label": "근로자 조회 (Passport No)",
        "redeem_search_btn": "조회",
        "redeem_info": "보유 코인: {} 개",
        "redeem_reason_label": "사용 사유 (예: 커피 교환)",
        "redeem_btn": "선택한 코인 사용 처리",
        "redeem_warning": "사용할 코인을 선택해주세요.",
        "redeem_reason_warning": "사용 사유를 입력해주세요.",
        "table_cols": ["시간", "관리자ID", "이름", "패스포트", "코인번호", "대분류", "중분류", "소분류", "비고"],
        # [추가된 부분: 코인 선택 테이블]
        "redeem_table_title": "▼ 코인 선택 (체크박스)",
        "col_select": "선택",
        "col_coin_no": "코인 번호",
        "col_timestamp": "지급 일시",
        "col_reason": "사유",
        "col_manager": "지급자"
    },
    "EN": {
        "title": "FGIP4 S.A.Y COIN",
        "login_title": "🏗️ FGIP4 Login",
        "id_label": "ID",
        "pw_label": "Password",
        "login_btn": "Login",
        "login_fail": "Check ID/PW or Permission.",
        "logout_btn": "Logout",
        "welcome": "User: {} ({})",
        "tab1": "💰 Reward Coin",
        "tab2": "📋 History",
        "tab3": "🏪 Redeem Coin",
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
        "success_msg": "Success!",
        "fail_msg": "Failed.",
        "ok_btn": "OK",
        "retry_btn": "Retry",
        "refresh_btn": "Refresh",
        "no_data": "No data found.",
        "header_history": "My History",
        "redeem_search_label": "Search Worker (Passport No)",
        "redeem_search_btn": "Search",
        "redeem_info": "Owned Coins: {}",
        "redeem_reason_label": "Redeem Reason",
        "redeem_btn": "Redeem Selected Coins",
        "redeem_warning": "Select coins to redeem.",
        "redeem_reason_warning": "Please enter a reason.",
        "table_cols": ["Time", "ManagerID", "Name", "Passport", "CoinNo", "Main", "Sub", "Detail", "Note"],
        # [Added: Redeem Table]
        "redeem_table_title": "▼ Select Coins (Checkbox)",
        "col_select": "Select",
        "col_coin_no": "Coin No",
        "col_timestamp": "Date",
        "col_reason": "Reason",
        "col_manager": "Manager"
    }
}

SAFETY_DATA = {
    "KO": {
        "개인 보호구": {
            "안전모": ["턱끈 체결 철저", "올바른 착용 상태", "파손품 자진 교체 요청"],
            "안전벨트": ["고소작업 시 체결 철저", "이중 안전고리 사용", "올바른 착용"],
            "안전화": ["뒤꿈치 꺾어 신지 않음", "끈 조임 상태 양호"],
            "보안경/마스크": ["분진 발생 작업 시 착용", "용접 보안면 착용"]
        },
        "안전 행동": {
            "정리정돈": ["작업장 통로 확보", "자재 적재 상태 양호", "작업 후 청소 상태 우수"],
            "TBM/교육": ["TBM 적극적 참여", "동료에게 위험 전파", "스트레칭 우수"],
            "장비 유도": ["신호수 위치 준수", "장비 반경 내 접근 금지 준수"]
        },
        "위험 발굴": {
            "아차사고": ["아차사고 신고 및 공유", "불안전한 상태 개선 건의"],
            "작업 중지": ["위험 상황 인지 후 작업 중지권 행사"]
        }
    },
    "EN": {
        "PPE": {
            "Helmet": ["Chin strap secured", "Properly worn"],
            "Harness": ["Hook secured", "Double lanyard usage"],
            "Shoes": ["Heels not folded", "Laces tied"]
        },
        "Safe Behavior": {
            "Housekeeping": ["Walkways clear", "Material stacking safe"],
            "TBM": ["Active participation", "Warning others"]
        },
        "Risk ID": {
            "Near Miss": ["Reported near miss"],
            "Stop Work": ["Stop Work Authority"]
        }
    }
}

conn = st.connection("gsheets", type=GSheetsConnection)

def get_text(key):
    lang_code = st.session_state.get('language', 'KO')
    return LANG[lang_code][key]

# --- 로그인 함수 (Role 추가) ---
def login(username, password):
    try:
        users_df = conn.read(worksheet="Users", ttl=0)
        users_df['ID'] = users_df['ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        users_df['PW'] = users_df['PW'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # Role 컬럼이 없으면 빈 문자열로 처리
        if 'Role' not in users_df.columns:
            users_df['Role'] = ""
        else:
            users_df['Role'] = users_df['Role'].fillna("").astype(str)

        user = users_df[(users_df['ID'] == str(username).strip()) & (users_df['PW'] == str(password).strip())]
        
        if not user.empty:
            return user.iloc[0]['Name'], user.iloc[0]['Role']
        return None, None
    except Exception as e:
        print(e)
        return None, None

# --- 입력 필드 초기화 함수 ---
def clear_inputs():
    # Session State의 키값을 초기화
    st.session_state['k_passport'] = ""
    st.session_state['k_coin'] = ""
    st.session_state['k_note'] = ""
    # 드롭다운 초기화를 위해 index 변경 등의 로직이 필요할 수 있으나,
    # 여기서는 input box 위주로 초기화. 드롭다운은 기본값으로 돌아감.

# --- 팝업(Dialog) 함수 ---
@st.dialog("알림")
def show_result_popup(is_success, error_msg=None, clear_on_ok=False):
    if is_success:
        st.success(get_text("success_msg"))
        # OK 버튼 누르면 입력창 비우고 닫기
        if st.button(get_text("ok_btn")):
            if clear_on_ok:
                clear_inputs()
            st.rerun()
    else:
        st.error(f"{get_text('fail_msg')}\n({error_msg})")
        if st.button(get_text("retry_btn")):
            st.rerun()

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = ""

    if 'language' not in st.session_state:
        st.session_state['language'] = "KO"

    with st.sidebar:
        st.header("Settings")
        lang_choice = st.radio("Language", ["Korean", "English"], 
                               index=0 if st.session_state['language'] == "KO" else 1)
        st.session_state['language'] = "KO" if lang_choice == "Korean" else "EN"
        
        if st.session_state['logged_in']:
            st.divider()
            role_display = "Admin" if st.session_state['user_role'] == "Master" else "User"
            st.info(get_text("welcome").format(st.session_state['user_name'], role_display))
            if st.button(get_text("logout_btn")):
                st.session_state['logged_in'] = False
                st.session_state['user_role'] = ""
                st.rerun()

    # --- 로그인 화면 ---
    if not st.session_state['logged_in']:
        st.title(get_text("login_title"))
        with st.form("login_form"):
            username = st.text_input(get_text("id_label"))
            password = st.text_input(get_text("pw_label"), type="password")
            submit = st.form_submit_button(get_text("login_btn"))
            
            if submit:
                user_name, user_role = login(username, password)
                if user_name:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_name
                    st.session_state['user_id'] = username
                    st.session_state['user_role'] = user_role
                    st.rerun()
                else:
                    st.error(get_text("login_fail"))

    # --- 메인 앱 화면 ---
    else:
        st.title(get_text("title"))
        
        # 탭 구성: 권한에 따라 다르게 표시
        tabs_list = [get_text("tab1"), get_text("tab2")]
        if st.session_state['user_role'] == "Master":
            tabs_list.append(get_text("tab3"))
            
        tabs = st.tabs(tabs_list)

        # ---------------------------------------------------------
        # [TAB 1] 코인 지급
        # ---------------------------------------------------------
        with tabs[0]:
            st.subheader(get_text("header_reward"))
            current_data = SAFETY_DATA[st.session_state['language']]
            default_opt = get_text("select_default")

            # Session State key를 사용하여 값 초기화 제어
            col1, col2 = st.columns(2)
            passport_no = col1.text_input(get_text("passport_label"), max_chars=5, key="k_passport")
            coin_no = col2.text_input(get_text("coin_label"), max_chars=4, key="k_coin")

            # 3단 드롭다운 (초기화 편의를 위해 간단하게 구성)
            main_cats = [default_opt] + list(current_data.keys())
            selected_main = st.selectbox(get_text("cat_main"), main_cats)

            sub_cats = [default_opt]
            if selected_main != default_opt:
                sub_cats += list(current_data[selected_main].keys())
            selected_sub = st.selectbox(get_text("cat_sub"), sub_cats, disabled=(selected_main == default_opt))

            detail_cats = [default_opt]
            if selected_sub != default_opt and selected_main != default_opt:
                detail_cats += current_data[selected_main][selected_sub]
            selected_detail = st.selectbox(get_text("cat_detail"), detail_cats, disabled=(selected_sub == default_opt))

            note = st.text_area(get_text("note_label"), height=80, key="k_note")

            if st.button(get_text("submit_btn"), type="primary", use_container_width=True):
                if (not passport_no or not coin_no or 
                    selected_main == default_opt or selected_sub == default_opt):
                    st.warning(get_text("warning_fill"))
                else:
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
                        show_result_popup(True, clear_on_ok=True) # 성공 시 입력창 초기화 트리거
                    except Exception as e:
                        show_result_popup(False, str(e))

        # ---------------------------------------------------------
        # [TAB 2] 지급 기록
        # ---------------------------------------------------------
        with tabs[1]:
            st.subheader(get_text("header_history"))
            if st.button(get_text("refresh_btn"), key="hist_refresh"):
                st.rerun()
                
            try:
                all_logs = conn.read(worksheet="Logs", ttl=0)
                # Manager_ID 기준으로 필터
                my_logs = all_logs[all_logs['Manager_ID'] == st.session_state['user_id']]
                
                if not my_logs.empty:
                    my_logs = my_logs.sort_values(by="Timestamp", ascending=False)
                    st.dataframe(my_logs, use_container_width=True, hide_index=True)
                else:
                    st.info(get_text("no_data"))
            except Exception:
                st.error(get_text("fail_msg"))

        # ---------------------------------------------------------
        # [TAB 3] 코인 사용 (Master Only) - 번역 적용 버전
        # ---------------------------------------------------------
        if st.session_state['user_role'] == "Master":
            with tabs[2]:
                st.subheader(get_text("tab3"))
                
                col_s1, col_s2 = st.columns([3, 1])
                search_passport = col_s1.text_input(get_text("redeem_search_label"), max_chars=5)
                do_search = col_s2.button(get_text("redeem_search_btn"), use_container_width=True)

                if search_passport:
                    try:
                        all_logs = conn.read(worksheet="Logs", ttl=0)
                        
                        # 전처리
                        all_logs['Passport_No'] = all_logs['Passport_No'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        all_logs['Coin_No'] = all_logs['Coin_No'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        clean_search_key = str(search_passport).strip()
                        
                        target_logs = all_logs[
                            (all_logs['Passport_No'] == clean_search_key) & 
                            (~all_logs['Coin_No'].str.contains(r'\*', regex=True))
                        ].copy()

                        count = len(target_logs)
                        st.metric(label="Available Coins", value=f"{count} EA")

                        if count > 0:
                            display_df = target_logs[['Coin_No', 'Timestamp', 'Detail_Cat', 'Manager_Name']]
                            
                            # [수정됨] 제목 번역 적용
                            st.write(get_text("redeem_table_title"))
                            display_df.insert(0, "Select", False)
                            
                            # [수정됨] 컬럼 헤더 번역 적용
                            edited_df = st.data_editor(
                                display_df,
                                column_config={
                                    "Select": st.column_config.CheckboxColumn(get_text("col_select"), default=False),
                                    "Coin_No": get_text("col_coin_no"),
                                    "Timestamp": get_text("col_timestamp"),
                                    "Detail_Cat": get_text("col_reason"),
                                    "Manager_Name": get_text("col_manager")
                                },
                                disabled=["Coin_No", "Timestamp", "Detail_Cat", "Manager_Name"],
                                hide_index=True,
                                use_container_width=True
                            )

                            redeem_reason = st.text_input(get_text("redeem_reason_label"))
                            
                            if st.button(get_text("redeem_btn"), type="primary"):
                                selected_coins = edited_df[edited_df["Select"] == True]["Coin_No"].tolist()
                                
                                if not selected_coins:
                                    st.warning(get_text("redeem_warning"))
                                elif not redeem_reason:
                                    st.warning(get_text("redeem_reason_warning"))
                                else:
                                    try:
                                        refresh_logs = conn.read(worksheet="Logs", ttl=0)
                                        refresh_logs['Passport_No'] = refresh_logs['Passport_No'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                                        refresh_logs['Coin_No'] = refresh_logs['Coin_No'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

                                        for c_no in selected_coins:
                                            idx = refresh_logs[
                                                (refresh_logs['Coin_No'] == c_no) & 
                                                (refresh_logs['Passport_No'] == clean_search_key)
                                            ].index
                                            
                                            if not idx.empty:
                                                target_idx = idx[0]
                                                refresh_logs.at[target_idx, 'Coin_No'] = f"{c_no}*"
                                                current_note = str(refresh_logs.at[target_idx, 'Note'])
                                                if current_note == "nan": current_note = ""
                                                refresh_logs.at[target_idx, 'Note'] = f"{current_note} [Used: {redeem_reason}]"

                                        conn.update(worksheet="Logs", data=refresh_logs)
                                        st.success(f"{len(selected_coins)} EA - {get_text('success_msg')}")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        else:
                            st.info(get_text("no_data"))

                    except Exception as e:
                        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()


