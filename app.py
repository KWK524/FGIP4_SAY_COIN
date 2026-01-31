import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 설정: 페이지 기본 세팅 ---
st.set_page_config(page_title="FGIP4 S.A.Y COIN", page_icon="🪙")

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
        "passport_label": "HSE Passport No",
        "passport_check_label": "Passport No 확인 (재입력)",
        "coin_input_label": "코인 일련번호 입력 ({}/{}번째)",
        "cat_top": "상위 분류",
        "cat_bot": "하위 분류",
        "select_default": "- 선택하세요 -",
        "note_label": "비고 (선택사항)",
        "submit_btn": "지급 등록",
        "warning_fill": "모든 필수 항목을 입력해주세요.",
        "warning_pass_mismatch": "패스포트 번호가 서로 일치하지 않습니다.",
        "success_msg": "처리되었습니다!",
        "fail_msg": "처리에 실패했습니다.",
        "duplicate_msg": "이미 지급된 코인 번호가 포함되어 있습니다: {}",
        "ok_btn": "OK",
        "retry_btn": "재시도",
        "refresh_btn": "내역 새로고침",
        "no_data": "데이터가 없습니다.",
        "header_history": "나의 지급 내역",
        "redeem_search_label": "근로자 조회 (Passport No)",
        "redeem_search_btn": "조회",
        "redeem_info": "보유 코인: {} 개",
        "redeem_reason_label": "사용 사유",
        "redeem_btn": "선택한 코인 사용 처리",
        "redeem_warning": "사용할 코인을 선택해주세요.",
        "redeem_reason_warning": "사용 사유를 입력해주세요.",
        "table_cols": ["시간", "관리자ID", "이름", "패스포트", "코인번호", "상위분류", "하위분류", "비고"],
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
        "passport_label": "HSE Passport No",
        "passport_check_label": "Confirm Passport No",
        "coin_input_label": "Enter Coin Serial ({}/{})",
        "cat_top": "Category (Top)",
        "cat_bot": "Category (Bottom)",
        "select_default": "- Select -",
        "note_label": "Note (Optional)",
        "submit_btn": "Submit",
        "warning_fill": "Please fill in all required fields.",
        "warning_pass_mismatch": "Passport numbers do not match.",
        "success_msg": "Success!",
        "fail_msg": "Failed.",
        "duplicate_msg": "Coin already issued: {}",
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
        "table_cols": ["Time", "ManagerID", "Name", "Passport", "CoinNo", "Top", "Bottom", "Note"],
        "redeem_table_title": "▼ Select Coins (Checkbox)",
        "col_select": "Select",
        "col_coin_no": "Coin No",
        "col_timestamp": "Date",
        "col_reason": "Reason",
        "col_manager": "Manager",
        "api_wait": "High traffic, retrying... ({}/{})"
    }
}

conn = st.connection("gsheets", type=GSheetsConnection)

def get_text(key, *args):
    lang_code = st.session_state.get('language', 'KO')
    text = LANG[lang_code].get(key, key)
    if args:
        return text.format(*args)
    return text

# --- 재시도 로직 ---
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

# --- 데이터 성형 함수 ---
def clean_numeric_str(val, width=0):
    s = str(val).strip()
    if s == "nan" or s == "None": return ""
    s = s.replace(".0", "") 
    is_used = "*" in s
    clean_s = s.replace("*", "") 
    if clean_s.isdigit() and width > 0:
        clean_s = clean_s.zfill(width)
    return clean_s + ("*" if is_used else "")

# --- 카테고리 데이터 로드 (Categories 시트에서) ---
@st.cache_data(ttl=600)
def load_category_data():
    try:
        df = read_data_with_retry(worksheet="Categories", ttl=600)
        # E열(Quantity)이 없으면 기본값 1로 생성
        if 'Quantity' not in df.columns:
            df['Quantity'] = 1
        
        # Quantity 컬럼을 숫자로 변환 (에러 방지)
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1).astype(int)
        
        return df
    except Exception:
        return pd.DataFrame()

# --- 로그인 함수 ---
@st.cache_data(ttl=600) 
def load_users_data():
    return read_data_with_retry(worksheet="Users", ttl=600)

def login(username, password):
    try:
        users_df = load_users_data()
        users_df['ID'] = users_df['ID'].apply(lambda x: clean_numeric_str(x))
        users_df['PW'] = users_df['PW'].apply(lambda x: clean_numeric_str(x))
        
        if 'Role' not in users_df.columns:
            users_df['Role'] = ""
        else:
            users_df['Role'] = users_df['Role'].fillna("").astype(str)

        user = users_df[(users_df['ID'] == str(username).strip()) & (users_df['PW'] == str(password).strip())]
        
        if not user.empty:
            return user.iloc[0]['Name'], user.iloc[0]['Role']
        return None, None
    except Exception as e:
        return None, None

def clear_inputs():
    st.session_state['k_passport'] = ""
    st.session_state['k_pass_check'] = ""
    st.session_state['k_note'] = ""
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('k_coin_dynamic_')]
    for k in keys_to_remove:
        del st.session_state[k]
        
    default_val = get_text("select_default")
    st.session_state['k_top'] = default_val
    st.session_state['k_bot'] = default_val

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

        # [TAB 1] 코인 지급 (E열 수량 연동)
        with tabs[0]:
            st.subheader(get_text("header_reward"))
            
            # 카테고리 데이터 로드
            cat_df = load_category_data()
            if cat_df.empty:
                st.error("Categories 시트를 불러올 수 없습니다.")
                st.stop()

            # 언어에 따른 컬럼 선택
            lang_suffix = "_KO" if st.session_state['language'] == "KO" else "_EN"
            col_top = f"Top{lang_suffix}"
            col_bot = f"Bottom{lang_suffix}"
            
            # --- 1. 패스포트 입력 및 확인 ---
            col1, col2 = st.columns(2)
            passport_no = col1.text_input(get_text("passport_label"), max_chars=10, key="k_passport")
            passport_check = col2.text_input(get_text("passport_check_label"), max_chars=10, key="k_pass_check", type="password")

            # --- 2. 2단 분류 ---
            default_opt = get_text("select_default")
            
            top_cats = [default_opt] + sorted(cat_df[col_top].unique().tolist())
            selected_top = st.selectbox(get_text("cat_top"), top_cats, key="k_top")

            bot_cats = [default_opt]
            if selected_top != default_opt:
                filtered_df = cat_df[cat_df[col_top] == selected_top]
                bot_cats += sorted(filtered_df[col_bot].unique().tolist())
            
            selected_bot = st.selectbox(get_text("cat_bot"), bot_cats, disabled=(selected_top == default_opt), key="k_bot")

            # --- 3. E열(Quantity)에서 수량 가져오기 ---
            coin_count = 0
            if selected_bot != default_opt:
                # 선택된 항목의 행(Row) 찾기
                try:
                    target_row = cat_df[
                        (cat_df[col_top] == selected_top) & 
                        (cat_df[col_bot] == selected_bot)
                    ]
                    if not target_row.empty:
                        # E열 값 읽기
                        coin_count = int(target_row.iloc[0]['Quantity'])
                    else:
                        coin_count = 1
                except:
                    coin_count = 1
            
            # 코인 입력창 생성
            entered_coins = []
            
            if coin_count > 0:
                st.markdown(f"**ℹ️ {coin_count}개의 코인 번호를 입력하세요.** (4자리 숫자)")
                cols = st.columns(min(coin_count, 4))
                for i in range(coin_count):
                    with cols[i % 4]:
                        val = st.text_input(
                            get_text("coin_input_label", i+1, coin_count), 
                            max_chars=4, 
                            key=f"k_coin_dynamic_{i}"
                        )
                        entered_coins.append(val)

            note = st.text_area(get_text("note_label"), height=80, key="k_note")

            if st.button(get_text("submit_btn"), type="primary", use_container_width=True):
                # 유효성 검사
                if (not passport_no or not passport_check or 
                    selected_top == default_opt or selected_bot == default_opt or
                    any(c == "" for c in entered_coins)):
                    st.warning(get_text("warning_fill"))
                elif passport_no != passport_check:
                    st.warning(get_text("warning_pass_mismatch"))
                else:
                    # HSE 접두어 처리
                    final_passport = str(passport_no).strip()
                    if not final_passport.upper().startswith("HSE"):
                        final_passport = "HSE" + final_passport
                    
                    # 코인 번호 정제
                    final_coins = [clean_numeric_str(c, 4) for c in entered_coins]

                    try:
                        existing_data = read_data_with_retry(worksheet="Logs", ttl=0)
                        
                        # 중복 검사
                        if not existing_data.empty:
                            existing_coins = existing_data['Coin_No'].apply(lambda x: clean_numeric_str(x, 4)).tolist()
                            duplicates = [c for c in final_coins if c in existing_coins]
                            if duplicates:
                                raise Exception(get_text("duplicate_msg", ", ".join(duplicates)))

                        # 데이터 저장
                        new_rows = []
                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        for c_no in final_coins:
                            new_rows.append({
                                "Timestamp": now_ts,
                                "Manager_ID": st.session_state['user_id'],
                                "Manager_Name": st.session_state['user_name'],
                                "Passport_No": final_passport,
                                "Coin_No": c_no,
                                "Main_Cat": selected_top,  
                                "Sub_Cat": selected_bot,
                                "Detail_Cat": "", 
                                "Note": note
                            })
                        
                        new_df = pd.DataFrame(new_rows)
                        updated_data = pd.concat([existing_data, new_df], ignore_index=True)
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
                my_logs = all_logs[all_logs['Manager_ID'] == st.session_state['user_id']].copy()
                
                if not my_logs.empty:
                    display_df = my_logs[['Timestamp', 'Manager_ID', 'Manager_Name', 'Passport_No', 'Coin_No', 'Main_Cat', 'Sub_Cat', 'Note']].copy()
                    display_df.columns = LANG[st.session_state['language']]['table_cols']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(get_text("no_data"))
            except Exception:
                st.error(get_text("fail_msg"))

        # [TAB 3] 코인 사용
        if st.session_state['user_role'] == "Master":
            with tabs[2]:
                st.subheader(get_text("tab3"))
                col_s1, col_s2 = st.columns([3, 1])
                search_passport = col_s1.text_input(get_text("redeem_search_label"), max_chars=15)
                do_search = col_s2.button(get_text("redeem_search_btn"), use_container_width=True)

                if search_passport:
                    try:
                        all_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                        
                        input_key = str(search_passport).strip()
                        search_candidates = [input_key]
                        if not input_key.upper().startswith("HSE"):
                            search_candidates.append("HSE" + input_key)

                        all_logs['Coin_Clean'] = all_logs['Coin_No'].apply(lambda x: clean_numeric_str(x, 4))
                        valid_logs = all_logs[~all_logs['Coin_Clean'].str.contains(r'\*', regex=True)].copy()
                        target_logs = valid_logs[valid_logs['Passport_No'].isin(search_candidates)].copy()
                        
                        count = len(target_logs)
                        st.metric(label="Available Coins", value=f"{count} EA")

                        if count > 0:
                            display_df = target_logs[['Coin_No', 'Timestamp', 'Sub_Cat', 'Manager_Name']]
                            st.write(get_text("redeem_table_title"))
                            display_df.insert(0, "Select", False)
                            
                            edited_df = st.data_editor(
                                display_df,
                                column_config={
                                    "Select": st.column_config.CheckboxColumn(get_text("col_select"), default=False),
                                    "Coin_No": get_text("col_coin_no"),
                                    "Timestamp": get_text("col_timestamp"),
                                    "Sub_Cat": get_text("col_reason"),
                                    "Manager_Name": get_text("col_manager")
                                },
                                disabled=["Coin_No", "Timestamp", "Sub_Cat", "Manager_Name"],
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
                                        refresh_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                                        refresh_logs['Coin_Clean'] = refresh_logs['Coin_No'].apply(lambda x: clean_numeric_str(x, 4))

                                        usage_records = []
                                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        
                                        selected_clean = [clean_numeric_str(c, 4).replace("*","") for c in selected_coins]
                                        mask = (refresh_logs['Coin_Clean'].isin(selected_clean)) & \
                                               (refresh_logs['Passport_No'].isin(search_candidates))
                                        
                                        rows_to_update = refresh_logs[mask].index
                                        
                                        for idx in rows_to_update:
                                            old_val = str(refresh_logs.at[idx, 'Coin_No'])
                                            pass_val = str(refresh_logs.at[idx, 'Passport_No'])
                                            if "*" not in old_val:
                                                refresh_logs.at[idx, 'Coin_No'] = old_val + "*"
                                                usage_records.append({
                                                    "Timestamp": now_ts,
                                                    "Manager_ID": st.session_state['user_id'],
                                                    "Manager_Name": st.session_state['user_name'],
                                                    "Passport_No": pass_val,
                                                    "Coin_No": clean_numeric_str(old_val, 4),
                                                    "Reason": redeem_reason
                                                })
                                        
                                        refresh_logs = refresh_logs.drop(columns=['Coin_Clean'], errors='ignore')
                                        update_data_with_retry(worksheet="Logs", data=refresh_logs)
                                        
                                        if usage_records:
                                            new_usage_df = pd.DataFrame(usage_records).astype(str)
                                            try:
                                                existing_usage = read_data_with_retry(worksheet="Usage", ttl=0)
                                                updated_usage = pd.concat([existing_usage, new_usage_df], ignore_index=True)
                                            except Exception:
                                                updated_usage = new_usage_df
                                            
                                            update_data_with_retry(worksheet="Usage", data=updated_usage)

                                        st.success(f"{len(usage_records)} EA - {get_text('success_msg')}")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        else:
                            st.info(get_text("no_data"))
                    except Exception as e:
                        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
