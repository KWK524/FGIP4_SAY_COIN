import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import extra_streamlit_components as stx

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
        "tab4": "🤝 협력사 관리",
        "header_reward": "근로자 안전 행동 보상",
        "passport_label": "HSE Passport No", 
        "passport_check_label": "HSE Passport No (Confirm)",
        "coin_input_guide": "**ℹ️ {}개의 코인 번호를 입력하세요.** (4~5자리 숫자)", # 수정됨
        "coin_input_label": "코인 일련번호 입력 ({}/{}번째)",
        "cat_top": "상위 분류",
        "cat_bot": "하위 분류",
        "select_default": "- 선택하세요 -",
        "note_label": "비고 (선택사항)",
        "submit_btn": "지급 등록",
        "warning_fill": "모든 필수 항목을 입력해주세요.",
        "warning_pass_mismatch": "입력한 두 개의 패스포트 번호가 일치하지 않습니다.",
        "warning_coin_len": "코인 번호는 4자리 또는 5자리 숫자로 입력해야 합니다.", # 추가됨
        "warning_coin_self_dup": "입력한 코인 번호 중 중복된 번호가 있습니다.",
        "success_msg": "처리되었습니다!",
        "fail_msg": "처리에 실패했습니다.",
        "duplicate_msg": "이미 지급된 코인 번호가 포함되어 있습니다: {}",
        "ok_btn": "OK",
        "retry_btn": "재시도",
        "refresh_btn": "내역 새로고침",
        "no_data": "데이터가 없습니다.",
        "header_history": "나의 지급 내역",
        "redeem_search_label": "근로자 조회 (HSE Passport No)",
        "redeem_coin_search_label": "코인 조회 (일련번호 4~5자리)", # 수정됨
        "redeem_search_mode": "검색 방식 선택",
        "mode_worker": "근로자 검색 (보유 코인 목록)",
        "mode_coin": "코인 번호 검색 (단건 조회)",
        "coin_owner_info": "🔍 소유자 정보: Passport No **{}**",
        "coin_not_found": "⚠️ 해당 코인을 찾을 수 없거나 이미 사용되었습니다.",
        "redeem_search_btn": "조회",
        "redeem_info": "보유 코인: {} 개",
        "redeem_reason_label": "사용 사유",
        "redeem_btn": "선택한 코인 사용 처리",
        "redeem_single_btn": "해당 코인 사용 처리",
        "redeem_warning": "사용할 코인을 선택해주세요.",
        "redeem_reason_warning": "사용 사유를 입력해주세요.",
        "table_cols": ["시간", "관리자ID", "이름", "패스포트", "코인번호", "상위분류", "하위분류", "비고"],
        "redeem_table_title": "▼ 코인 선택 (체크박스)",
        "col_select": "선택",
        "col_coin_no": "코인 번호",
        "col_timestamp": "지급 일시",
        "col_reason": "사유",
        "col_manager": "지급자",
        "api_wait": "통신량이 많아 대기 중... ({}/{})",
        "subcon_select_label": "협력사(Subcontractor) 선택",
        "subcon_balance_fmt": "💰 현재 보유 수량: **{}** 개",
        "subcon_action_type": "작업 유형",
        "action_give": "지급 (Provision)",
        "action_use": "사용 (Redeem)",
        "subcon_qty_label": "수량 (개)",
        "subcon_reason_label": "사유 (필수)",
        "subcon_btn_give": "✅ 지급 처리",
        "subcon_btn_use": "🛑 사용 처리",
        "subcon_warn_qty": "수량은 1 이상의 정수여야 합니다.",
        "subcon_warn_reason": "사유를 입력해주세요.",
        "subcon_warn_balance": "보유 수량이 부족합니다.",
        "subcon_success_give": "협력사 지급 완료!",
        "subcon_success_use": "협력사 사용 완료!",
        "shortcut_caption": "바로가기 아이콘 만들기",
        "shortcut_title": "📲 홈 화면에 추가하는 법",
        "ios_guide": """**1.** Safari 브라우저 하단 **[공유]** 버튼(📤) 클릭\n**2.** 메뉴를 올려서 **[홈 화면에 추가]** 선택\n**3.** 우측 상단 **[추가]** 클릭""",
        "android_guide": """**1.** Chrome 브라우저 우측 상단 **[점 3개]** 메뉴 클릭\n**2.** **[홈 화면에 추가]** 또는 **[앱 설치]** 선택\n**3.** **[추가]** 버튼 클릭"""
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
        "tab4": "🤝 Subcontractor",
        "header_reward": "Safety Action Reward",
        "passport_label": "HSE Passport No",
        "passport_check_label": "HSE Passport No (Confirm)",
        "coin_input_guide": "**ℹ️ Enter {} coin serial numbers.** (4-5 digits)", # 수정됨
        "coin_input_label": "Enter Coin Serial ({}/{})",
        "cat_top": "Category (Top)",
        "cat_bot": "Category (Bottom)",
        "select_default": "- Select -",
        "note_label": "Note (Optional)",
        "submit_btn": "Submit",
        "warning_fill": "Please fill in all required fields.",
        "warning_pass_mismatch": "Passport numbers do not match.",
        "warning_coin_len": "Coin numbers must be 4 or 5 digits.", # 추가됨
        "warning_coin_self_dup": "Duplicate coin numbers entered.",
        "success_msg": "Success!",
        "fail_msg": "Failed.",
        "duplicate_msg": "Coin already issued: {}",
        "ok_btn": "OK",
        "retry_btn": "Retry",
        "refresh_btn": "Refresh",
        "no_data": "No data found.",
        "header_history": "My History",
        "redeem_search_label": "Search Worker (HSE Passport No)",
        "redeem_coin_search_label": "Search Coin (4-5 digit Serial)", # 수정됨
        "redeem_search_mode": "Search Mode",
        "mode_worker": "By Worker (List Coins)",
        "mode_coin": "By Coin No (Single)",
        "coin_owner_info": "🔍 Owner: Passport No **{}**",
        "coin_not_found": "⚠️ Coin not found or already used.",
        "redeem_search_btn": "Search",
        "redeem_info": "Owned Coins: {}",
        "redeem_reason_label": "Redeem Reason",
        "redeem_btn": "Redeem Selected Coins",
        "redeem_single_btn": "Redeem This Coin",
        "redeem_warning": "Select coins to redeem.",
        "redeem_reason_warning": "Please enter a reason.",
        "table_cols": ["Time", "ManagerID", "Name", "Passport", "CoinNo", "Top", "Bottom", "Note"],
        "redeem_table_title": "▼ Select Coins (Checkbox)",
        "col_select": "Select",
        "col_coin_no": "Coin No",
        "col_timestamp": "Date",
        "col_reason": "Reason",
        "col_manager": "Manager",
        "api_wait": "High traffic, retrying... ({}/{})",
        "subcon_select_label": "Select Subcontractor",
        "subcon_balance_fmt": "💰 Current Balance: **{}**",
        "subcon_action_type": "Action Type",
        "action_give": "Give (Provision)",
        "action_use": "Use (Redeem)",
        "subcon_qty_label": "Quantity",
        "subcon_reason_label": "Reason (Mandatory)",
        "subcon_btn_give": "✅ Submit (Give)",
        "subcon_btn_use": "🛑 Submit (Use)",
        "subcon_warn_qty": "Quantity must be > 0.",
        "subcon_warn_reason": "Please enter a reason.",
        "subcon_warn_balance": "Insufficient balance.",
        "subcon_success_give": "Provision Success!",
        "subcon_success_use": "Redemption Success!",
        "shortcut_caption": "Create App Shortcut",
        "shortcut_title": "📲 Add to Home Screen",
        "ios_guide": """**1.** Tap **[Share]** button (📤) in Safari\n**2.** Scroll down & select **[Add to Home Screen]**\n**3.** Tap **[Add]** (Top right)""",
        "android_guide": """**1.** Tap **[Menu]** (3 dots) in Chrome (Top right)\n**2.** Select **[Add to Home Screen]** or **[Install App]**\n**3.** Tap **[Add]**"""
    }
}

conn = st.connection("gsheets", type=GSheetsConnection)

def get_text(key, *args):
    lang_code = st.session_state.get('language', 'EN')
    text = LANG[lang_code].get(key, key)
    if args:
        return text.format(*args)
    return text

# --- gspread 원본 클라이언트를 이용한 Append 통신 ---
def get_gspread_worksheet(worksheet_name):
    sheet_info = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "http" in sheet_info:
        return conn.client.open_by_url(sheet_info).worksheet(worksheet_name)
    else:
        try:
            return conn.client.open_by_key(sheet_info).worksheet(worksheet_name)
        except:
            return conn.client.open(sheet_info).worksheet(worksheet_name)

def read_data_with_retry(worksheet, ttl=0, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            return conn.read(worksheet=worksheet, ttl=ttl)
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                retries += 1
                time.sleep(2 ** retries)
            else:
                raise e
    raise Exception("API Quota Exceeded. Please try again later.")

# --- 데이터 캐싱 함수 ---
def get_cached_logs(force_refresh=False):
    if 'cached_logs' not in st.session_state or force_refresh:
        st.session_state['cached_logs'] = read_data_with_retry(worksheet="Logs", ttl=0)
    return st.session_state['cached_logs']

def get_cached_subcon_logs(force_refresh=False):
    if 'cached_subcon_logs' not in st.session_state or force_refresh:
        try:
            st.session_state['cached_subcon_logs'] = read_data_with_retry(worksheet="Subcon_Logs", ttl=0)
        except:
            st.session_state['cached_subcon_logs'] = pd.DataFrame()
    return st.session_state['cached_subcon_logs']

# --- 데이터 성형 함수 ---
def clean_numeric_str(val, width=0):
    s = str(val).strip()
    if s == "nan" or s == "None": return ""
    s = s.replace(".0", "") 
    is_used = "*" in s
    clean_s = s.replace("*", "") 
    
    # 5자리 데이터는 원형 보존, 과거 누락된 데이터(4자리 미만)만 앞에 0을 채움
    if clean_s.isdigit() and width > 0:
        clean_s = clean_s.zfill(width)
        
    return clean_s + ("*" if is_used else "")

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
    except Exception:
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
    st.session_state['redeem_reason_input'] = ""
    st.session_state['redeem_search_key'] = ""
    st.session_state['redeem_coin_search_key'] = ""
    st.session_state['subcon_reason_input'] = ""
    st.session_state['subcon_qty_input'] = 1

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

def get_manager():
    return stx.CookieManager(key="auth_cookie_manager")

def main():
    cookie_manager = get_manager()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = ""
    
    if 'language' not in st.session_state:
        lang_cookie = cookie_manager.get("fgip4_lang")
        if lang_cookie in ["KO", "EN"]:
            st.session_state['language'] = lang_cookie
        else:
            st.session_state['language'] = "EN"

    if st.session_state.get('logout_pressed', False):
        st.session_state['logout_pressed'] = False
    else:
        cookie_val = cookie_manager.get("fgip4_auth")
        if not st.session_state['logged_in'] and cookie_val and str(cookie_val).strip() != "":
            try:
                if ":" in cookie_val:
                    c_id, c_pw = cookie_val.split(":", 1)
                    user_name, user_role = login(c_id, c_pw)
                    if user_name:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = user_name
                        st.session_state['user_id'] = c_id
                        st.session_state['user_role'] = user_role
                        st.rerun()
            except:
                pass

    with st.sidebar:
        st.header("Settings")
        lang_options = ["English", "Korean"]
        current_idx = 0 if st.session_state['language'] == "EN" else 1
        lang_choice = st.radio("Language", lang_options, index=current_idx)
        new_lang = "EN" if lang_choice == "English" else "KO"
        
        if st.session_state['language'] != new_lang:
            st.session_state['language'] = new_lang
            cookie_manager.set("fgip4_lang", new_lang, expires_at=datetime.now() + timedelta(days=30))
            time.sleep(0.2)
            st.rerun()
        
        if st.session_state['logged_in']:
            st.divider()
            role_display = "Admin" if st.session_state['user_role'] == "Master" else "User"
            st.info(get_text("welcome", st.session_state['user_name'], role_display))
            if st.button(get_text("logout_btn")):
                cookie_manager.set("fgip4_auth", "", expires_at=datetime.now())
                st.session_state['logged_in'] = False
                st.session_state['logout_pressed'] = True
                time.sleep(0.5) 
                st.rerun()

        st.divider()
        st.caption(get_text("shortcut_caption"))
        with st.expander(get_text("shortcut_title")):
            tab_ios, tab_android = st.tabs(["iPhone", "Android"])
            with tab_ios:
                st.markdown(get_text("ios_guide"), unsafe_allow_html=True)
            with tab_android:
                st.markdown(get_text("android_guide"))

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
                    cookie_val = f"{username}:{password}"
                    cookie_manager.set("fgip4_auth", cookie_val, expires_at=datetime.now() + timedelta(days=7))
                    st.rerun()
                else:
                    st.error(get_text("login_fail"))
    else:
        st.title(get_text("title"))
        tabs_list = [get_text("tab1"), get_text("tab2")]
        if st.session_state['user_role'] == "Master":
            tabs_list.append(get_text("tab3"))
            tabs_list.append(get_text("tab4"))
        tabs = st.tabs(tabs_list)

        # ==========================================
        # [TAB 1] 코인 지급
        # ==========================================
        with tabs[0]:
            st.subheader(get_text("header_reward"))
            
            cat_df = load_category_data()
            if cat_df.empty:
                st.error("Categories 시트를 불러올 수 없습니다.")
                st.stop()

            cat_df.columns = cat_df.columns.str.strip()
            if st.session_state['user_role'] != "Master":
                if 'Permission' in cat_df.columns:
                    mask = cat_df['Permission'].fillna("").astype(str).str.strip().str.upper() == "MASTER"
                    cat_df = cat_df[~mask]

            is_ko = (st.session_state['language'] == "KO")
            col_top_display = "Top_KO" if is_ko else "Top_EN"
            col_bot_display = "Bottom_KO" if is_ko else "Bottom_EN"
            
            col1, col2 = st.columns(2)
            passport_no = col1.text_input(get_text("passport_label"), max_chars=5, key="k_passport")
            passport_check = col2.text_input(get_text("passport_check_label"), max_chars=5, key="k_pass_check")

            default_opt = get_text("select_default")
            top_cats = [default_opt] + sorted(cat_df[col_top_display].unique().tolist())
            selected_top = st.selectbox(get_text("cat_top"), top_cats, key="k_top")

            bot_cats = [default_opt]
            if selected_top != default_opt:
                filtered_df = cat_df[cat_df[col_top_display] == selected_top]
                bot_cats += sorted(filtered_df[col_bot_display].unique().tolist())
            
            selected_bot = st.selectbox(get_text("cat_bot"), bot_cats, disabled=(selected_top == default_opt), key="k_bot")

            coin_count = 0
            selected_row = None
            if selected_bot != default_opt:
                try:
                    selected_row = cat_df[(cat_df[col_top_display] == selected_top) & (cat_df[col_bot_display] == selected_bot)].iloc[0]
                    coin_count = int(selected_row['Quantity'])
                except:
                    coin_count = 1
            
            with st.form("coin_issue_form"):
                entered_coins = []
                if coin_count > 0:
                    st.markdown(get_text("coin_input_guide", coin_count))
                    cols = st.columns(min(coin_count, 4))
                    for i in range(coin_count):
                        with cols[i % 4]:
                            # [수정] max_chars=5 로 늘림
                            val = st.text_input(get_text("coin_input_label", i+1, coin_count), max_chars=5, key=f"k_coin_dynamic_{i}")
                            entered_coins.append(val)

                note = st.text_area(get_text("note_label"), height=80, key="k_note")
                submitted = st.form_submit_button(get_text("submit_btn"), type="primary", use_container_width=True)

                if submitted:
                    if (not passport_no or not passport_check or selected_top == default_opt or selected_bot == default_opt or any(c == "" for c in entered_coins)):
                        st.warning(get_text("warning_fill"))
                    elif passport_no != passport_check:
                        st.warning(get_text("warning_pass_mismatch"))
                    # [추가] 코인 길이가 4 또는 5가 아니면 차단
                    elif any(len(str(c).strip()) not in [4, 5] for c in entered_coins):
                        st.warning(get_text("warning_coin_len"))
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

                            new_rows_values = []
                            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            for c_no in final_coins:
                                new_rows_values.append([
                                    now_ts,
                                    st.session_state['user_id'],
                                    st.session_state['user_name'],
                                    f"'{final_passport}",  
                                    f"'{c_no}",            
                                    selected_row['Top_KO'],
                                    selected_row['Bottom_KO'],
                                    selected_row['Top_EN'],
                                    selected_row['Bottom_EN'],
                                    note
                                ])
                            
                            logs_ws = get_gspread_worksheet("Logs")
                            logs_ws.append_rows(new_rows_values, value_input_option='USER_ENTERED')
                            
                            get_cached_logs(force_refresh=True)
                            show_result_popup(True, clear_on_ok=True)
                        except Exception as e:
                            show_result_popup(False, str(e))

        # ==========================================
        # [TAB 2] 지급 기록
        # ==========================================
        with tabs[1]:
            st.subheader(get_text("header_history"))
            if st.button(get_text("refresh_btn"), key="hist_refresh"):
                get_cached_logs(force_refresh=True)
                st.rerun()
            try:
                all_logs = get_cached_logs()
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

        # ==========================================
        # [TAB 3] 코인 사용
        # ==========================================
        if st.session_state['user_role'] == "Master":
            with tabs[2]:
                st.subheader(get_text("tab3"))
                search_mode = st.radio(
                    get_text("redeem_search_mode"),
                    options=["Worker", "Coin"],
                    format_func=lambda x: get_text("mode_worker") if x == "Worker" else get_text("mode_coin"),
                    horizontal=True
                )
                
                if st.button(get_text("refresh_btn"), key="redeem_refresh"):
                    get_cached_logs(force_refresh=True)
                    st.rerun()
                st.divider()

                if search_mode == "Worker":
                    col_s1, col_s2 = st.columns([3, 1])
                    search_passport = col_s1.text_input(get_text("redeem_search_label"), max_chars=5, key="redeem_search_key")
                    do_search = col_s2.button(get_text("redeem_search_btn"), use_container_width=True)

                    if search_passport:
                        try:
                            all_logs = get_cached_logs().copy()
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
                                    key="redeem_data_editor",
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

                                redeem_reason = st.text_input(get_text("redeem_reason_label"), key="redeem_reason_input")
                                
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
                                            mask = (refresh_logs['Coin_Clean'].isin(selected_clean)) & (refresh_logs['Passport_Clean'] == clean_search_key)
                                            rows_to_update = refresh_logs[mask].index
                                            
                                            logs_ws = get_gspread_worksheet("Logs")
                                            
                                            for idx in rows_to_update:
                                                old_val = str(refresh_logs.at[idx, 'Coin_No'])
                                                pass_val = str(refresh_logs.at[idx, 'Passport_No'])
                                                if "*" not in old_val:
                                                    logs_ws.update_cell(int(idx) + 2, 5, old_val + "*")
                                                    
                                                    usage_records.append([
                                                        now_ts,
                                                        st.session_state['user_id'],
                                                        st.session_state['user_name'],
                                                        f"'{clean_numeric_str(pass_val, 5)}",
                                                        f"'{clean_numeric_str(old_val, 4)}",
                                                        redeem_reason
                                                    ])
                                            
                                            if usage_records:
                                                usage_ws = get_gspread_worksheet("Usage")
                                                usage_ws.append_rows(usage_records, value_input_option='USER_ENTERED')

                                            get_cached_logs(force_refresh=True)
                                            show_result_popup(True, clear_on_ok=True)

                                        except Exception as e:
                                            show_result_popup(False, str(e))
                            else:
                                st.info(get_text("no_data"))
                        except Exception as e:
                            st.error(f"Error: {e}")

                # B. 코인 번호 검색 모드
                else: 
                    col_c1, col_c2 = st.columns([3, 1])
                    # [수정] max_chars=5 로 늘림
                    search_coin_no = col_c1.text_input(get_text("redeem_coin_search_label"), max_chars=5, key="redeem_coin_search_key")
                    do_search_coin = col_c2.button(get_text("redeem_search_btn"), use_container_width=True)

                    if search_coin_no:
                        try:
                            all_logs = get_cached_logs().copy()
                            clean_coin_key = clean_numeric_str(search_coin_no, 4)
                            all_logs['Coin_Clean'] = all_logs['Coin_No'].apply(lambda x: clean_numeric_str(x, 4))
                            target_row = all_logs[(all_logs['Coin_Clean'].str.replace("*","") == clean_coin_key) & (~all_logs['Coin_Clean'].str.contains(r'\*'))]

                            if not target_row.empty:
                                row_data = target_row.iloc[0]
                                owner_passport = clean_numeric_str(row_data['Passport_No'], 5)
                                st.info(get_text("coin_owner_info", owner_passport))
                                redeem_reason_coin = st.text_input(get_text("redeem_reason_label"), key="redeem_reason_input")
                                
                                if st.button(get_text("redeem_single_btn"), type="primary"):
                                    if not redeem_reason_coin:
                                        st.warning(get_text("redeem_reason_warning"))
                                    else:
                                        try:
                                            refresh_logs = read_data_with_retry(worksheet="Logs", ttl=0)
                                            refresh_logs['Coin_Clean'] = refresh_logs['Coin_No'].apply(lambda x: clean_numeric_str(x, 4))
                                            mask = (refresh_logs['Coin_Clean'] == clean_coin_key) & (~refresh_logs['Coin_No'].astype(str).str.contains(r'\*'))
                                            rows_to_update = refresh_logs[mask].index
                                            
                                            if len(rows_to_update) > 0:
                                                idx = rows_to_update[0]
                                                old_val = str(refresh_logs.at[idx, 'Coin_No'])
                                                pass_val = str(refresh_logs.at[idx, 'Passport_No'])
                                                
                                                logs_ws = get_gspread_worksheet("Logs")
                                                logs_ws.update_cell(int(idx) + 2, 5, old_val + "*")
                                                
                                                now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                usage_ws = get_gspread_worksheet("Usage")
                                                usage_ws.append_row([
                                                    now_ts,
                                                    st.session_state['user_id'],
                                                    st.session_state['user_name'],
                                                    f"'{clean_numeric_str(pass_val, 5)}",
                                                    f"'{clean_numeric_str(old_val, 4)}",
                                                    redeem_reason_coin
                                                ], value_input_option='USER_ENTERED')
                                                
                                                get_cached_logs(force_refresh=True)
                                                show_result_popup(True, clear_on_ok=True)
                                            else:
                                                show_result_popup(False, get_text("coin_not_found"))
                                        except Exception as e:
                                            show_result_popup(False, str(e))
                            else:
                                st.warning(get_text("coin_not_found"))
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ==========================================
        # [TAB 4] 협력사 관리
        # ==========================================
        if st.session_state['user_role'] == "Master":
            with tabs[3]:
                st.subheader(get_text("tab4"))
                try:
                    users_df = load_users_data()
                    subcon_list = users_df[users_df['Role'] == 'Subcon']['Name'].unique().tolist()
                    subcon_list.sort()
                except:
                    subcon_list = []
                
                if not subcon_list:
                    st.warning("No Subcontractors found in Users sheet.")
                    st.stop()

                selected_subcon = st.selectbox(get_text("subcon_select_label"), [get_text("select_default")] + subcon_list)
                
                if st.button(get_text("refresh_btn"), key="subcon_refresh"):
                    get_cached_subcon_logs(force_refresh=True)
                    st.rerun()

                if selected_subcon != get_text("select_default"):
                    current_balance = 0
                    try:
                        subcon_logs = get_cached_subcon_logs()
                        if not subcon_logs.empty and 'Subcon_Name' in subcon_logs.columns:
                            df_s = subcon_logs[subcon_logs['Subcon_Name'] == selected_subcon]
                            given = df_s[df_s['Type'] == 'Give']['Quantity'].astype(int).sum()
                            used = df_s[df_s['Type'] == 'Use']['Quantity'].astype(int).sum()
                            current_balance = given - used
                    except Exception:
                        pass
                    
                    st.info(get_text("subcon_balance_fmt", current_balance))
                    st.divider()
                    
                    action_type = st.radio(
                        get_text("subcon_action_type"), 
                        ["Give", "Use"],
                        format_func=lambda x: get_text("action_give") if x == "Give" else get_text("action_use"),
                        horizontal=True
                    )
                    
                    col_q, col_r = st.columns([1, 3])
                    if 'subcon_qty_input' not in st.session_state:
                        st.session_state['subcon_qty_input'] = 1
                    qty = col_q.number_input(get_text("subcon_qty_label"), min_value=1, step=1, format="%d", key="subcon_qty_input")
                    reason = col_r.text_input(get_text("subcon_reason_label"), key="subcon_reason_input")
                    
                    btn_label = get_text("subcon_btn_give") if action_type == "Give" else get_text("subcon_btn_use")
                    
                    if st.button(btn_label, type="primary", use_container_width=True):
                        if qty < 1:
                            st.warning(get_text("subcon_warn_qty"))
                        elif not reason:
                            st.warning(get_text("subcon_warn_reason"))
                        elif action_type == "Use" and qty > current_balance:
                            st.warning(get_text("subcon_warn_balance"))
                        else:
                            try:
                                now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                subcon_ws = get_gspread_worksheet("Subcon_Logs")
                                subcon_ws.append_row([
                                    now_ts,
                                    st.session_state['user_name'],
                                    selected_subcon,
                                    action_type,
                                    int(qty),
                                    reason
                                ], value_input_option='USER_ENTERED')
                                
                                get_cached_subcon_logs(force_refresh=True)
                                show_result_popup(True, clear_on_ok=True)
                            except Exception as e:
                                show_result_popup(False, str(e))

if __name__ == "__main__":
    main()
