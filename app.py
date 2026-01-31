import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 설정: 페이지 기본 세팅 ---
st.set_page_config(page_title="FGIP4 S.A.Y COIN", page_icon="🪙", layout="wide")

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
        "passport_check_label": "HSE Passport No (Confirm)",
        "coin_input_guide": "**ℹ️ {}개의 코인 번호를 입력하세요.** (4자리 숫자)",
        "coin_input_label": "코인 일련번호 입력 ({}/{}번째)",
        "cat_top": "상위 분류",
        "cat_bot": "하위 분류",
        "select_default": "- 선택하세요 -",
        "note_label": "비고 (선택사항)",
        "submit_btn": "지급 등록",
        "warning_fill": "모든 필수 항목을 입력해주세요.",
        "warning_pass_mismatch": "입력한 두 개의 패스포트 번호가 일치하지 않습니다.",
        "warning_coin_self_dup": "입력한 코인 번호 중 중복된 번호가 있습니다.",
        "success_msg": "처리되었습니다! (통계 업데이트 완료)",
        "fail_msg": "처리에 실패했습니다.",
        "duplicate_msg": "이미 지급된 코인 번호가 포함되어 있습니다: {}",
        "ok_btn": "OK",
        "retry_btn": "재시도",
        "refresh_btn": "내역 새로고침",
        "no_data": "데이터가 없습니다.",
        "header_history": "나의 지급 내역",
        "redeem_search_label": "근로자 조회 (HSE Passport No)",
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
        "passport_check_label": "HSE Passport No (Confirm)",
        "coin_input_guide": "**ℹ️ Enter {} coin serial numbers.** (4 digits)",
        "coin_input_label": "Enter Coin Serial ({}/{})",
        "cat_top": "Category (Top)",
        "cat_bot": "Category (Bottom)",
        "select_default": "- Select -",
        "note_label": "Note (Optional)",
        "submit_btn": "Submit",
        "warning_fill": "Please fill in all required fields.",
        "warning_pass_mismatch": "Passport numbers do not match.",
        "warning_coin_self_dup": "Duplicate coin numbers entered.",
        "success_msg": "Success! (Stats Updated)",
        "fail_msg": "Failed.",
        "duplicate_msg": "Coin already issued: {}",
        "ok_btn": "OK",
        "retry_btn": "Retry",
        "refresh_btn": "Refresh",
        "no_data": "No data found.",
        "header_history": "My History",
        "redeem_search_label": "Search Worker (HSE Passport No)",
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

# --- [수정됨] 월별 통계 자동 계산 및 업데이트 ---
def calculate_and_update_stats():
    try:
        logs_df = read_data_with_retry("Logs", ttl=0)
        users_df = read_data_with_retry("Users", ttl=0)
        cats_df = read_data_with_retry("Categories", ttl=0)
        
        if logs_df.empty: return

        # [핵심 변경 1] 날짜 포맷 변경 (2026-01 -> 26년 01월)
        # 이렇게 한글을 섞어야 구글 시트가 숫자로 오해하지 않습니다.
        logs_df['Month'] = pd.to_datetime(logs_df['Timestamp']).dt.strftime('%y년 %m월')
        
        # -----------------------------------------------------
        # [A] Users 시트 통계
        # -----------------------------------------------------
        user_stats = logs_df.pivot_table(index='Manager_ID', columns='Month', values='Coin_No', aggfunc='count', fill_value=0)
        
        users_df['ID'] = users_df['ID'].apply(lambda x: clean_numeric_str(x))
        user_stats.index = user_stats.index.astype(str)
        
        # [핵심 변경 2] 통계 컬럼 찾는 패턴 변경 (26년 01월 패턴)
        # 기존 Users 데이터에서 통계 컬럼을 제외한 기본 정보만 남김
        current_cols = users_df.columns.tolist()
        keep_cols = [c for c in current_cols if not re.match(r'\d{2}년 \d{2}월', c)]
        
        users_base = users_df[keep_cols].copy()
        
        users_final = pd.merge(users_base, user_stats, left_on='ID', right_index=True, how='left')
        users_final = users_final.fillna(0)
        
        # 숫자 컬럼들(통계) 정수 변환
        for col in users_final.columns:
            if re.match(r'\d{2}년 \d{2}월', col):
                users_final[col] = users_final[col].astype(int)
                
        update_data_with_retry("Users", users_final)
        
        # -----------------------------------------------------
        # [B] Categories 시트 통계
        # -----------------------------------------------------
        cat_stats = logs_df.pivot_table(index=['Top_KO', 'Bottom_KO'], columns='Month', values='Coin_No', aggfunc='count', fill_value=0)
        
        # Categories 원본 정리
        keep_cat_cols = [c for c in cats_df.columns.tolist() if not re.match(r'\d{2}년 \d{2}월', c)]
        cats_base = cats_df[keep_cat_cols].copy()
        
        cats_final = pd.merge(cats_base, cat_stats, on=['Top_KO', 'Bottom_KO'], how='left')
        cats_final = cats_final.fillna(0)
        
        for col in cats_final.columns:
            if re.match(r'\d{2}년 \d{2}월', col):
                cats_final[col] = cats_final[col].astype(int)
                
        update_data_with_retry("Categories", cats_final)
        
    except Exception as e:
        st.error(f"통계 업데이트 중 오류 발생: {e}")

# --- 카테고리 데이터 로드 ---
@st.cache_data(ttl=600)
def load_category_data():
    try:
        df = read_data_with_retry(worksheet="Categories", ttl=600)
        if 'Quantity' not in df.columns:
            df['Quantity'] = 1
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

        # [TAB 1] 코인 지급
        with tabs[0]:
            st.subheader(get_text("header_reward"))
            
            cat_df = load_category_data()
            if cat_df.empty:
                st.error("Categories 시트를 불러올 수 없습니다.")
                st.stop()

            is_ko = (st.session_state['language'] == "KO")
            col_top_display = "Top_KO" if is_ko else "Top_EN"
            col_bot_display = "Bottom_KO" if is_ko else "Bottom_EN"
            
            # 1. 입력
            col1, col2 = st.columns(2)
            passport_no = col1.text_input(get_text("passport_label"), max_chars=5, key="k_passport")
            passport_check = col2.text_input(get_text("passport_check_label"), max_chars=5, key="k_pass_check")

            # 2. 분류
            default_opt = get_text("select_default")
            top_cats = [default_opt] + sorted(cat_df[col_top_display].unique().tolist())
            selected_top = st.selectbox(get_text("cat_top"), top_cats, key="k_top")

            bot_cats = [default_opt]
            if selected_top != default_opt:
                filtered_df = cat_df[cat_df[col_top_display] == selected_top]
                bot_cats += sorted(filtered_df[col_bot_display].unique().tolist())
            
            selected_bot = st.selectbox(get_text("cat_bot"), bot_cats, disabled=(selected_top == default_opt), key="k_bot")

            # 3. 수량
            coin_count = 0
            selected_row = None

            if selected_bot != default_opt:
                try:
                    selected_row = cat_df[
                        (cat_df[col_top_display] == selected_top) & 
                        (cat_df[col_bot_display] == selected_bot)
                    ].iloc[0]
                    coin_count = int(selected_row['Quantity'])
                except:
                    coin_count = 1
            
            entered_coins = []
            if coin_count > 0:
                st.markdown(get_text("coin_input_guide", coin_count))
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
                if (not passport_no or not passport_check or 
                    selected_top == default_opt or selected_bot == default_opt or
                    any(c == "" for c in entered_coins)):
                    st.warning(get_text("warning_fill"))
                elif passport_no != passport_check:
                    st.warning(get_text("warning_pass_mismatch"))
                elif len(entered_coins) != len(set(entered_coins)):
                    st.warning(get_text("warning_coin_self_dup"))
                else:
                    final_passport = clean_numeric_str(passport_no, 5)
                    final_coins = [clean_numeric_str(c, 4) for c in entered_coins]

                    try:
                        existing_data = read_data_with_retry(worksheet="Logs", ttl=0)
                        
                        if not existing_data.empty:
                            existing_coins = existing_data['Coin_No'].apply(lambda x: clean_numeric_str(x, 4)).tolist()
                            duplicates = [c for c in final_coins if c in existing_coins]
                            if duplicates:
                                raise Exception(get_text("duplicate_msg", ", ".join(duplicates)))

                        new_rows = []
                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        val_top_ko = selected_row['Top_KO']
                        val_bot_ko = selected_row['Bottom_KO']
                        val_top_en = selected_row['Top_EN']
                        val_bot_en = selected_row['Bottom_EN']

                        for c_no in final_coins:
                            new_rows.append({
                                "Timestamp": now_ts,
                                "Manager_ID": st.session_state['user_id'],
                                "Manager_Name": st.session_state['user_name'],
                                "Passport_No": final_passport,
                                "Coin_No": c_no,
                                "Top_KO": val_top_ko,
                                "Bottom_KO": val_bot_ko,
                                "Top_EN": val_top_en,
                                "Bottom_EN": val_bot_en,
                                "Note": note
                            })
                        
                        new_df = pd.DataFrame(new_rows)
                        updated_data = pd.concat([existing_data, new_df], ignore_index=True)
                        update_data_with_retry(worksheet="Logs", data=updated_data)
                        
                        # 통계 업데이트
                        calculate_and_update_stats()
                        
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
                    my_logs['Passport_No'] = my_logs['Passport_No'].apply(lambda x: clean_numeric_str(x, 5))
                    my_logs['Coin_No'] = my_logs['Coin_No'].apply(lambda x: clean_numeric_str(x, 4))
                    
                    is_ko = (st.session_state['language'] == "KO")
                    show_top = "Top_KO" if is_ko else "Top_EN"
                    show_bot = "Bottom_KO" if is_ko else "Bottom_EN"

                    display_df = my_logs[['Timestamp', 'Manager_ID', 'Manager_Name', 'Passport_No', 'Coin_No', show_top, show_bot, 'Note']].copy()
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
                search_passport = col_s1.text_input(get_text("redeem_search_label"), max_chars=5)
                do_search = col_s2.button(get_text("redeem_search_btn"), use_container_width=True)

                if search_passport:
                    try:
                        all_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                        clean_search_key = clean_numeric_str(search_passport, 5)

                        all_logs['Coin_Clean'] = all_logs['Coin_No'].apply(lambda x: clean_numeric_str(x, 4))
                        all_logs['Passport_Clean'] = all_logs['Passport_No'].apply(lambda x: clean_numeric_str(x, 5))
                        
                        valid_logs = all_logs[~all_logs['Coin_Clean'].str.contains(r'\*', regex=True)].copy()
                        target_logs = valid_logs[valid_logs['Passport_Clean'] == clean_search_key].copy()
                        
                        count = len(target_logs)
                        st.metric(label="Available Coins", value=f"{count} EA")

                        if count > 0:
                            is_ko = (st.session_state['language'] == "KO")
                            show_bot = "Bottom_KO" if is_ko else "Bottom_EN"

                            target_logs['Coin_No'] = target_logs['Coin_Clean']
                            display_df = target_logs[['Coin_No', 'Timestamp', show_bot, 'Manager_Name']]
                            
                            st.write(get_text("redeem_table_title"))
                            display_df.insert(0, "Select", False)
                            
                            edited_df = st.data_editor(
                                display_df,
                                column_config={
                                    "Select": st.column_config.CheckboxColumn(get_text("col_select"), default=False),
                                    "Coin_No": get_text("col_coin_no"),
                                    "Timestamp": get_text("col_timestamp"),
                                    show_bot: get_text("col_reason"),
                                    "Manager_Name": get_text("col_manager")
                                },
                                disabled=["Coin_No", "Timestamp", show_bot, "Manager_Name"],
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
                                        refresh_logs['Passport_Clean'] = refresh_logs['Passport_No'].apply(lambda x: clean_numeric_str(x, 5))

                                        usage_records = []
                                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        
                                        selected_clean = [clean_numeric_str(c, 4).replace("*","") for c in selected_coins]
                                        mask = (refresh_logs['Coin_Clean'].isin(selected_clean)) & \
                                               (refresh_logs['Passport_Clean'] == clean_search_key)
                                        
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
                                        
                                        refresh_logs = refresh_logs.drop(columns=['Coin_Clean', 'Passport_Clean'], errors='ignore')
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
