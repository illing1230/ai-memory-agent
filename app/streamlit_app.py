"""AI Memory Agent - Streamlit 데모 UI"""

import streamlit as st
import httpx
import json

# API 설정
API_BASE_URL = "http://localhost:8000/api/v1"

# 페이지 설정
st.set_page_config(
    page_title="AI Memory Agent",
    page_icon="🧠",
    layout="wide",
)

# 세션 상태 초기화
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "users" not in st.session_state:
    st.session_state.users = []


def api_request(method: str, endpoint: str, data: dict = None, user_id: str = None):
    """API 요청 헬퍼"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if user_id:
        headers["X-User-ID"] = user_id
    
    try:
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API 오류: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        st.error(f"연결 오류: {str(e)}")
        return None


def load_users():
    """사용자 목록 로드"""
    result = api_request("GET", "/users")
    if result:
        st.session_state.users = result
    return st.session_state.users


# 사이드바 - 사용자 선택
with st.sidebar:
    st.title("🧠 AI Memory Agent")
    st.markdown("---")
    
    # 사용자 목록 로드
    users = load_users()
    
    if users:
        user_options = {f"{u['name']} ({u['email']})": u['id'] for u in users}
        selected_user = st.selectbox(
            "👤 사용자 선택",
            options=list(user_options.keys()),
            index=0 if user_options else None,
        )
        if selected_user:
            st.session_state.user_id = user_options[selected_user]
            st.success(f"선택됨: {selected_user}")
    else:
        st.warning("사용자가 없습니다. 먼저 사용자를 생성하세요.")
        
        with st.expander("➕ 새 사용자 생성"):
            new_name = st.text_input("이름")
            new_email = st.text_input("이메일")
            if st.button("생성"):
                if new_name and new_email:
                    result = api_request("POST", "/users", {
                        "name": new_name,
                        "email": new_email,
                    })
                    if result:
                        st.success("사용자 생성됨!")
                        st.rerun()
    
    st.markdown("---")
    st.caption("Made with ❤️ for Samsung Quality Team")


# 메인 컨텐츠
if not st.session_state.user_id:
    st.warning("👈 사이드바에서 사용자를 선택하세요.")
    st.stop()


# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 메모리 검색", 
    "💾 메모리 저장", 
    "📋 메모리 목록",
    "🤖 자동 추출"
])


# 탭 1: 메모리 검색
with tab1:
    st.header("🔍 메모리 시맨틱 검색")
    st.markdown("자연어로 검색하면 의미적으로 유사한 메모리를 찾습니다.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "검색어",
            placeholder="예: 코드 리뷰 시간, 회의 일정, 선호하는 도구...",
        )
    with col2:
        search_limit = st.number_input("결과 수", min_value=1, max_value=20, value=5)
    
    if st.button("🔍 검색", type="primary"):
        if search_query:
            with st.spinner("검색 중..."):
                result = api_request(
                    "POST",
                    "/memories/search",
                    {"query": search_query, "limit": search_limit},
                    st.session_state.user_id,
                )
            
            if result and result.get("results"):
                st.success(f"{len(result['results'])}개 결과 발견")
                
                for i, item in enumerate(result["results"]):
                    memory = item["memory"]
                    score = item["score"]
                    
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{memory['content']}**")
                            st.caption(
                                f"📁 {memory['scope']} | "
                                f"🏷️ {memory.get('category', '-')} | "
                                f"⭐ {memory.get('importance', '-')}"
                            )
                        with col2:
                            st.metric("유사도", f"{score:.2%}")
                        st.divider()
            else:
                st.info("검색 결과가 없습니다.")
        else:
            st.warning("검색어를 입력하세요.")


# 탭 2: 메모리 저장
with tab2:
    st.header("💾 새 메모리 저장")
    
    with st.form("memory_form"):
        content = st.text_area(
            "메모리 내용",
            placeholder="예: 김철수는 아침 회의를 선호한다",
            height=100,
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            scope = st.selectbox("범위", ["personal", "project", "department"])
        with col2:
            category = st.selectbox(
                "카테고리",
                ["preference", "fact", "decision", "relationship", "other"],
            )
        with col3:
            importance = st.selectbox("중요도", ["low", "medium", "high"])
        
        submitted = st.form_submit_button("💾 저장", type="primary")
        
        if submitted:
            if content:
                with st.spinner("저장 중..."):
                    result = api_request(
                        "POST",
                        "/memories",
                        {
                            "content": content,
                            "scope": scope,
                            "category": category,
                            "importance": importance,
                        },
                        st.session_state.user_id,
                    )
                
                if result:
                    st.success("✅ 메모리가 저장되었습니다!")
                    st.json(result)
            else:
                st.warning("내용을 입력하세요.")


# 탭 3: 메모리 목록
with tab3:
    st.header("📋 내 메모리 목록")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 새로고침"):
            st.rerun()
    
    with st.spinner("로딩 중..."):
        memories = api_request(
            "GET",
            "/memories",
            user_id=st.session_state.user_id,
        )
    
    if memories:
        st.success(f"총 {len(memories)}개 메모리")
        
        for memory in memories:
            with st.expander(f"📝 {memory['content'][:50]}...", expanded=False):
                st.markdown(f"**내용:** {memory['content']}")
                st.markdown(f"**범위:** {memory['scope']}")
                st.markdown(f"**카테고리:** {memory.get('category', '-')}")
                st.markdown(f"**중요도:** {memory.get('importance', '-')}")
                st.markdown(f"**생성일:** {memory['created_at']}")
                st.caption(f"ID: {memory['id']}")
    else:
        st.info("저장된 메모리가 없습니다.")


# 탭 4: 자동 추출
with tab4:
    st.header("🤖 대화에서 메모리 자동 추출")
    st.markdown("대화 내용을 입력하면 LLM이 중요한 정보를 자동으로 추출합니다.")
    
    conversation_input = st.text_area(
        "대화 내용",
        placeholder="""예시:
user: 나는 보통 아침 9시에 출근해
assistant: 네, 9시 출근이시군요.
user: 그리고 점심은 12시에 먹는 걸 좋아해
assistant: 12시 점심 선호하시는군요.""",
        height=200,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        extract_scope = st.selectbox("저장 범위", ["personal", "project", "department"], key="extract_scope")
    
    if st.button("🤖 메모리 추출", type="primary"):
        if conversation_input:
            # 대화 파싱
            lines = conversation_input.strip().split("\n")
            conversation = []
            for line in lines:
                if line.startswith("user:"):
                    conversation.append({"role": "user", "content": line[5:].strip()})
                elif line.startswith("assistant:"):
                    conversation.append({"role": "assistant", "content": line[10:].strip()})
                elif ":" in line:
                    role, content = line.split(":", 1)
                    conversation.append({"role": role.strip(), "content": content.strip()})
            
            if conversation:
                with st.spinner("LLM이 메모리를 추출하는 중..."):
                    result = api_request(
                        "POST",
                        "/memories/extract",
                        {
                            "conversation": conversation,
                            "scope": extract_scope,
                        },
                        st.session_state.user_id,
                    )
                
                if result:
                    st.success(f"✅ {len(result)}개 메모리가 추출되었습니다!")
                    for mem in result:
                        st.info(f"📝 {mem['content']}")
                else:
                    st.warning("추출된 메모리가 없습니다.")
            else:
                st.warning("대화 형식이 올바르지 않습니다.")
        else:
            st.warning("대화 내용을 입력하세요.")


# 푸터
st.markdown("---")
st.caption("AI Memory Agent v0.1.0 | 권한 기반 멀티채팅 메모리 관리 시스템")
