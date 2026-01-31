import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 설정: 페이지 기본 세팅 ---
st.set_page_config(page_title="S.A.Y COIN 지급 시스템", page_icon="🪙")

# --- 데이터베이스 연결 (구글 시트) ---
# 캐시 유지 시간(ttl)을 0으로 해서 즉시 업데이트 반영
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 지급 사유 데이터 (나중에 구글 시트로 뺄 수도 있음) ---
REASON_DATA = {
    "개인 보호구": {
        "안전모": ["턱끈 체결 철저", "올바른 착용", "파손품 자진 신고", "직접 입력"],
        "안전벨트": ["고리 체결 철저", "올바른 착용", "직접 입력"],
        "안전화": ["뒤꿈치 꺾어 신지 않음", "직접 입력"],
        "직접 입력": ["직접 입력"]
    },
    "안전 행동": {
        "정리정돈": ["작업장 정리 우수", "통로 확보", "직접 입력"],
        "TBM 참여": ["적극적 의견 제시", "스트레칭 우수", "직접 입력"],
        "직접 입력": ["직접 입력"]
    },
    "직접 입력": {
        "직접 입력": ["직접 입력"]
    }
}

# --- 로그인 함수 ---
def login(username, password):
    try:
        # Users 시트 읽어오기
        users_df = conn.read(worksheet="Users", ttl=0)
        
        # [🔴 디버깅용 코드] 이 부분이 화면에 엑셀 내용을 보여줍니다.
        st.write("▼ 컴퓨터가 읽은 엑셀 데이터 (테스트 후 삭제하세요)")
        st.dataframe(users_df) 
        
        # 데이터 전처리 (강제 문자 변환)
        users_df['ID'] = users_df['ID'].astype(str).str.strip()
        users_df['PW'] = users_df['PW'].astype(str).str.strip()
        username = str(username).strip()
        password = str(password).strip()

        # 비교
        user = users_df[(users_df['ID'] == username) & (users_df['PW'] == password)]
        
        if not user.empty:
            return user.iloc[0]['Name']
        else:
            return None
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# --- 메인 화면 로직 ---
def main():
    # 세션 상태 초기화 (로그인 여부 확인)
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = ""
        st.session_state['user_id'] = ""

    # [화면 1] 로그인 페이지
    if not st.session_state['logged_in']:
        st.title("🏗️ S.A.Y COIN 로그인")
        
        with st.form("login_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            submit = st.form_submit_button("로그인")
            
            if submit:
                user_name = login(username, password)
                if user_name:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_name
                    st.session_state['user_id'] = username
                    st.rerun() # 화면 새로고침
                else:
                    st.error("아이디 또는 비밀번호가 잘못되었습니다. (마스터 파일 확인 필요)")

    # [화면 2] 메인 기능 페이지 (로그인 성공 시)
    else:
        st.sidebar.success(f"접속자: {st.session_state['user_name']} 님")
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.title("S.A.Y COIN 지급 시스템 🪙")
        
        # 탭 구성: 지급하기 vs 기록보기
        tab1, tab2 = st.tabs(["💰 코인 지급", "📋 지급 기록"])

        # --- 탭 1: 코인 지급 ---
        with tab1:
            st.subheader("근로자 안전 행동 보상")
            
            with st.form("coin_form", clear_on_submit=True):
                # 1. 기본 정보
                col1, col2 = st.columns(2)
                passport_no = col1.text_input("Passport No (5자리)", max_chars=5)
                coin_no = col2.text_input("Coin Serial (0001~3000)", max_chars=4)

                # 2. 사유 선택 (동적 드롭다운)
                # 대분류
                main_cat = st.selectbox("대분류", list(REASON_DATA.keys()))
                
                # 중분류 (대분류 선택에 따라 바뀜)
                sub_cat_options = list(REASON_DATA[main_cat].keys())
                sub_cat = st.selectbox("중분류", sub_cat_options)
                
                # 소분류 (중분류 선택에 따라 바뀜)
                detail_cat_options = REASON_DATA[main_cat][sub_cat]
                detail_cat = st.selectbox("소분류 (사유)", detail_cat_options)

                # 3. 직접 입력 로직
                final_reason = detail_cat # 기본값
                
                # 사용자가 '직접 입력'을 선택했는지 체크
                is_manual_input = (main_cat == "직접 입력") or (sub_cat == "직접 입력") or (detail_cat == "직접 입력")
                
                manual_text = ""
                if is_manual_input:
                    manual_text = st.text_input("📝 상세 사유를 직접 입력하세요")
                    if manual_text:
                        final_reason = manual_text

                note = st.text_area("비고 (선택사항)", height=80)

                # 제출 버튼
                submitted = st.form_submit_button("지급 등록")

                if submitted:
                    if len(passport_no) < 5 or len(coin_no) < 4:
                        st.warning("패스포트 번호와 코인 번호를 정확히 입력해주세요.")
                    elif is_manual_input and not manual_text:
                        st.warning("직접 입력 칸에 내용을 작성해주세요.")
                    else:
                        # 저장 로직
                        new_data = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Manager_ID": st.session_state['user_id'],
                            "Manager_Name": st.session_state['user_name'],
                            "Passport_No": passport_no,
                            "Coin_No": coin_no,
                            "Main_Cat": main_cat,
                            "Sub_Cat": sub_cat,
                            "Detail_Cat": final_reason,
                            "Note": note
                        }])
                        
                        try:
                            # 기존 데이터 읽기 -> 합치기 -> 다시 쓰기
                            # (대규모 동시성 처리 시에는 append 모드가 좋지만 gsheets connection 기본은 전체 갱신임)
                            existing_data = conn.read(worksheet="Logs", ttl=0)
                            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
                            conn.update(worksheet="Logs", data=updated_data)
                            
                            st.success(f"{passport_no}번 근로자에게 코인 지급 완료!")
                        except Exception as e:
                            st.error(f"저장 실패 (잠시 후 다시 시도해주세요): {e}")

        # --- 탭 2: 지급 기록 ---
        with tab2:
            st.subheader("나의 지급 내역")
            if st.button("내역 새로고침"):
                st.rerun()
                
            try:
                # 전체 데이터 가져와서 내 ID로 필터링
                all_logs = conn.read(worksheet="Logs", ttl=0)
                my_logs = all_logs[all_logs['Manager_ID'] == st.session_state['user_id']]
                
                # 최신순 정렬
                if not my_logs.empty:
                    my_logs = my_logs.sort_values(by="Timestamp", ascending=False)
                    st.dataframe(my_logs, use_container_width=True)
                else:
                    st.info("아직 지급한 기록이 없습니다.")
                    
            except Exception as e:
                st.error("데이터를 불러오는 중 오류가 발생했습니다.")

if __name__ == "__main__":

    main()
