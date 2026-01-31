import streamlit as st
import pandas as pd
import time
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
        "duplicate_msg": "이미 지급된 코인 번호입니다 (아직 사용 안 됨).",
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
        "redeem_table_title": "▼ 코인 선택 (체크박스)",
        "col_select": "선택",
        "col_coin_no": "코인 번호",
        "col_timestamp": "지급 일시",
        "col_reason": "사유",
        "col_manager": "지급자",
        "api_wait": "통신량이 많아 대기 중... ({}/{})"
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
        "duplicate_msg": "This coin is already issued and active.",
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
        "redeem_table_title": "▼ Select Coins (Checkbox)",
        "col_select": "Select",
        "col_coin_no": "Coin No",
        "col_timestamp": "Date",
        "col_reason": "Reason",
        "col_manager": "Manager",
        "api_wait": "High traffic, retrying... ({}/{})"
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

def get_text(key, *args):
    lang_code = st.session_state.get('language', 'KO')
    text = LANG[lang_code].get(key, key)
    if args:
        return text.format(*args)
    return text

# --- [핵심] 강력한 데이터 정제 함수 (1.0 -> 0001 복원) ---
def sanitize_code(value, length=4):
    """
    1.0 -> 1 -> 0001 로 변환
    1234* -> 1234* (유지)
    nan -> ""
    """
    s = str(value).strip()
    if s.lower() == "nan" or s.lower() == "none" or s == "":
        return ""
    
    # 1.0 같은 실수형 문자열 처리
    if s.endswith(".0"):
        s = s[:-2]
        
    # 별표(*)가 있으면 분리해서 숫자 부분만 패딩
    has_star = "*" in s
    clean_s = s.replace("*", "")
    
    # 숫자만 있다면 지정된 길이만큼 0 채우기 (패스포트5, 코인4)
    if clean_s.isdigit():
        clean_s = clean_s.zfill(length)
        
    return clean_s + ("*" if has_star else "")

# --- 재시도 로직 함수 ---
def read_data_with_retry(worksheet, ttl=0, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            return conn.read(worksheet=worksheet, ttl=ttl)
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                retries += 1
                wait_time = 2 ** retries
                st.toast(get_text("api_wait", retries, max_retries), icon="⏳")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("API Quota Exceeded. Please try again later.")

def update_data_with_retry(worksheet, data, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            conn.update(worksheet=worksheet, data=data)
            return True
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                retries += 1
                wait_time = 2 ** retries
                st.toast(get_text("api_wait", retries, max_retries), icon="⏳")
                time.sleep(wait_time)
            else:
                raise e
    return False

# --- 로그인 함수 ---
@st.cache_data(ttl=600) 
def load_users_data():
    return read_data_with_retry(worksheet="Users", ttl=600)

def login(username, password):
    try:
        users_df = load_users_data()
        # 데이터 정제 적용
        users_df['ID'] = users_df['ID'].apply(lambda x: sanitize_code(x, 0)) # ID는 패딩 안함
        users_df['PW'] = users_df['PW'].apply(lambda x: sanitize_code(x, 0))
        
        if 'Role' not in users_df.columns:
            users_df['Role'] = ""
        else:
            users_df['Role'] = users_df['Role'].fillna("").astype(str)

        user = users_df[(users_df['ID'] == str(username).strip()) & (users_df['PW'] == str(password).strip())]
        
        if not user.empty:
            return user.iloc[0]['Name'], user.iloc[0]['Role']
        return None, None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None, None

def clear_inputs():
    st.session_state['k_passport'] = ""
    st.session_state['k_coin'] = ""
    st.session_state['k_note'] = ""
    default_val = get_text("select_default")
    st.session_state['k_main'] = default_val
    st.session_state['k_sub'] = default_val
    st.session_state['k_detail'] = default_val

@st.dialog("알림")
def show_result_popup(is_success, error_msg=None, clear_on_ok=False):
    if is_success:
        st.success(get_text("success_msg"))
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
            st.info(get_text("welcome", st.session_state['user_name'], role_display))
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
                load_users_data.clear()
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
        
        tabs_list = [get_text("tab1"), get_text("tab2")]
        if st.session_state['user_role'] == "Master":
            tabs_list.append(get_text("tab3"))
            
        tabs = st.tabs(tabs_list)

        # [TAB 1] 코인 지급
        with tabs[0]:
            st.subheader(get_text("header_reward"))
            current_data = SAFETY_DATA[st.session_state['language']]
            default_opt = get_text("select_default")

            col1, col2 = st.columns(2)
            passport_no = col1.text_input(get_text("passport_label"), max_chars=5, key="k_passport")
            coin_no = col2.text_input(get_text("coin_label"), max_chars=4, key="k_coin")

            main_cats = [default_opt] + list(current_data.keys())
            selected_main = st.selectbox(get_text("cat_main"), main_cats, key="k_main")

            sub_cats = [default_opt]
            if selected_main != default_opt:
                sub_cats += list(current_data[selected_main].keys())
            selected_sub = st.selectbox(get_text("cat_sub"), sub_cats, disabled=(selected_main == default_opt), key="k_sub")

            detail_cats = [default_opt]
            if selected_sub != default_opt and selected_main != default_opt:
                detail_cats += current_data[selected_main][selected_sub]
            selected_detail = st.selectbox(get_text("cat_detail"), detail_cats, disabled=(selected_sub == default_opt), key="k_detail")

            note = st.text_area(get_text("note_label"), height=80, key="k_note")

            if st.button(get_text("submit_btn"), type="primary", use_container_width=True):
                if (not passport_no or not coin_no or 
                    selected_main == default_opt or selected_sub == default_opt):
                    st.warning(get_text("warning_fill"))
                else:
                    # [핵심] 저장할 때 ' (아포스트로피)를 붙여서 텍스트로 강제 인식시킴
                    safe_passport = f"'{passport_no.zfill(5)}"
                    safe_coin = f"'{coin_no.zfill(4)}"
                    
                    new_data = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Manager_ID": st.session_state['user_id'],
                        "Manager_Name": st.session_state['user_name'],
                        "Passport_No": safe_passport,
                        "Coin_No": safe_coin,
                        "Main_Cat": selected_main,
                        "Sub_Cat": selected_sub,
                        "Detail_Cat": selected_detail,
                        "Note": note
                    }])
                    
                    try:
                        existing_data = read_data_with_retry(worksheet="Logs", ttl=0)
                        
                        if not existing_data.empty:
                            # 읽어온 데이터 정제 후 비교
                            check_series = existing_data['Coin_No'].apply(lambda x: sanitize_code(x, 4))
                            input_coin = coin_no.zfill(4) # 입력값도 4자리로 맞춰서 비교
                            
                            if input_coin in check_series.values:
                                raise Exception(get_text("duplicate_msg"))

                        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
                        update_data_with_retry(worksheet="Logs", data=updated_data)
                        show_result_popup(True, clear_on_ok=True)
                        
                    except Exception as e:
                        show_result_popup(False, str(e))

        # [TAB 2] 지급 기록
        with tabs[1]:
            st.subheader(get_text("header_history"))
            if st.button(get_text("refresh_btn"), key="hist_refresh"):
                st.rerun()
                
            try:
                all_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                
                # 데이터 정제 (보여주기용)
                all_logs['Passport_No'] = all_logs['Passport_No'].apply(lambda x: sanitize_code(x, 5))
                all_logs['Coin_No'] = all_logs['Coin_No'].apply(lambda x: sanitize_code(x, 4))
                
                my_logs = all_logs[all_logs['Manager_ID'] == st.session_state['user_id']]
                
                if not my_logs.empty:
                    my_logs = my_logs.sort_values(by="Timestamp", ascending=False)
                    st.dataframe(my_logs, use_container_width=True, hide_index=True)
                else:
                    st.info(get_text("no_data"))
            except Exception:
                st.error(get_text("fail_msg"))

        # [TAB 3] 코인 사용 (Master Only)
        if st.session_state['user_role'] == "Master":
            with tabs[2]:
                st.subheader(get_text("tab3"))
                
                col_s1, col_s2 = st.columns([3, 1])
                search_passport = col_s1.text_input(get_text("redeem_search_label"), max_chars=5)
                do_search = col_s2.button(get_text("redeem_search_btn"), use_container_width=True)

                if search_passport:
                    try:
                        all_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                        
                        # [핵심] 읽어온 데이터 싹 정제 (1.0 -> 0001)
                        all_logs['Passport_No'] = all_logs['Passport_No'].apply(lambda x: sanitize_code(x, 5))
                        all_logs['Coin_No'] = all_logs['Coin_No'].apply(lambda x: sanitize_code(x, 4))
                        
                        clean_search_key = search_passport.strip().zfill(5)
                        
                        target_logs = all_logs[
                            (all_logs['Passport_No'] == clean_search_key) & 
                            (~all_logs['Coin_No'].str.contains(r'\*', regex=True))
                        ].copy()

                        count = len(target_logs)
                        st.metric(label="Available Coins", value=f"{count} EA")

                        if count > 0:
                            display_df = target_logs[['Coin_No', 'Timestamp', 'Detail_Cat', 'Manager_Name']]
                            
                            st.write(get_text("redeem_table_title"))
                            display_df.insert(0, "Select", False)
                            
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
                                        # 1. Logs 시트 업데이트
                                        refresh_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                                        
                                        # 매칭을 위해 다시 정제
                                        refresh_logs['Passport_No'] = refresh_logs['Passport_No'].apply(lambda x: sanitize_code(x, 5))
                                        refresh_logs['Coin_No'] = refresh_logs['Coin_No'].apply(lambda x: sanitize_code(x, 4))

                                        usage_records = []
                                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                        for c_no in selected_coins:
                                            idx = refresh_logs[
                                                (refresh_logs['Coin_No'] == c_no) & 
                                                (refresh_logs['Passport_No'] == clean_search_key)
                                            ].index
                                            
                                            if not idx.empty:
                                                target_idx = idx[0]
                                                # 별표 붙일 때 아포스트로피 붙여서 저장
                                                refresh_logs.at[target_idx, 'Coin_No'] = f"'{c_no}*"
                                                
                                                usage_records.append({
                                                    "Timestamp": now_ts,
                                                    "Manager_ID": st.session_state['user_id'],
                                                    "Manager_Name": st.session_state['user_name'],
                                                    "Passport_No": f"'{clean_search_key}", # 아포스트로피 추가
                                                    "Coin_No": f"'{c_no}",                 # 아포스트로피 추가
                                                    "Reason": redeem_reason
                                                })

                                        # 2. Logs 저장
                                        update_data_with_retry(worksheet="Logs", data=refresh_logs)
                                        
                                        # 3. Usage 시트 저장
                                        if usage_records:
                                            new_usage_df = pd.DataFrame(usage_records)
                                            try:
                                                existing_usage = read_data_with_retry(worksheet="Usage", ttl=0)
                                                updated_usage = pd.concat([existing_usage, new_usage_df], ignore_index=True)
                                            except Exception:
                                                updated_usage = new_usage_df
                                            
                                            update_data_with_retry(worksheet="Usage", data=updated_usage)

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
