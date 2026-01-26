"""AI Memory Agent - Streamlit 데모 UI"""

import streamlit as st
import httpx
import json
import time

# API 설정
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://10.244.14.73:8000/api/v1")

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
if "current_room" not in st.session_state:
    st.session_state.current_room = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_toast" not in st.session_state:
    st.session_state.memory_toast = None


def api_request(method: str, endpoint: str, data: dict = None, user_id: str = None):
    """API 요청 헬퍼"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if user_id:
        headers["X-User-ID"] = user_id
    
    try:
        with httpx.Client(timeout=60.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = client.put(url, headers=headers, json=data)
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


def load_projects():
    """프로젝트 목록 로드"""
    return api_request("GET", "/users/projects") or []


def load_departments():
    """부서 목록 로드"""
    return api_request("GET", "/users/departments") or []


def load_chat_rooms():
    """채팅방 목록 로드 (모든 채팅방)"""
    return api_request("GET", "/chat-rooms", user_id=st.session_state.user_id) or []


def load_messages(room_id: str):
    """채팅방 메시지 로드"""
    return api_request("GET", f"/chat-rooms/{room_id}/messages", user_id=st.session_state.user_id) or []


def show_memory_toast():
    """메모리 저장 토스트 표시"""
    if st.session_state.memory_toast:
        memories = st.session_state.memory_toast
        
        # 토스트 스타일 컨테이너
        toast_html = f"""
        <div style="
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 350px;
            animation: slideIn 0.3s ease-out;
        ">
            <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px;">
                🧠 메모리 자동 저장됨 ({len(memories)}개)
            </div>
        """
        
        for mem in memories[:3]:  # 최대 3개만 표시
            content = mem.get('content', '')[:50]
            if len(mem.get('content', '')) > 50:
                content += '...'
            toast_html += f"""
            <div style="
                background: rgba(255,255,255,0.2);
                padding: 8px 12px;
                border-radius: 6px;
                margin-top: 6px;
                font-size: 13px;
            ">
                📝 {content}
            </div>
            """
        
        if len(memories) > 3:
            toast_html += f"""
            <div style="font-size: 12px; margin-top: 8px; opacity: 0.8;">
                +{len(memories) - 3}개 더...
            </div>
            """
        
        toast_html += """
        </div>
        <style>
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        </style>
        """
        
        st.markdown(toast_html, unsafe_allow_html=True)
        
        # 토스트 클리어 (다음 리로드에서 사라지도록)
        st.session_state.memory_toast = None


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
    else:
        st.warning("사용자가 없습니다.")
        
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
    
    # 슬래시 커맨드 도움말
    with st.expander("📖 커맨드 도움말"):
        st.markdown("""
        **메모리 관리**
        - `/remember <내용>` - 저장
        - `/forget <검색어>` - 삭제
        - `/search <검색어>` - 검색
        
        **채팅방 관리**
        - `/members` - 멤버 목록
        - `/invite <이메일>` - 멤버 초대
        
        **AI 호출**
        - `@ai <질문>` - AI에게 질문
        
        **기타**
        - `/help` - 도움말
        """)
    
    st.caption("Made with ❤️ for Samsung Quality Team")


# 메모리 토스트 표시
show_memory_toast()


# 메인 컨텐츠
if not st.session_state.user_id:
    st.warning("👈 사이드바에서 사용자를 선택하세요.")
    st.stop()


# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 채팅",
    "🔍 메모리 검색", 
    "💾 메모리 저장", 
    "📋 메모리 목록",
    "🤖 자동 추출"
])


# 탭 1: 채팅
with tab1:
    st.header("💬 채팅")
    
    col1, col2 = st.columns([1, 3])
    
    # 왼쪽: 채팅방 목록
    with col1:
        st.subheader("채팅방")
        
        # 새 채팅방 생성
        with st.expander("➕ 새 채팅방"):
            room_name = st.text_input("채팅방 이름", key="new_room_name")
            room_type = st.selectbox("타입", ["personal", "project", "department"], key="new_room_type")
            
            # 메모리 소스 선택
            st.markdown("**📦 메모리 소스**")
            use_personal = st.checkbox("내 개인 메모리", value=True, key="use_personal")
            
            # 프로젝트 선택
            projects = load_projects()
            selected_projects = []
            if projects:
                st.markdown("프로젝트:")
                for proj in projects:
                    if st.checkbox(proj["name"], key=f"proj_{proj['id']}"):
                        selected_projects.append(proj["id"])
            
            # 부서 선택
            departments = load_departments()
            selected_depts = []
            if departments:
                st.markdown("부서:")
                for dept in departments:
                    if st.checkbox(dept["name"], key=f"dept_{dept['id']}"):
                        selected_depts.append(dept["id"])
            
            if st.button("채팅방 생성", type="primary"):
                if room_name:
                    context_sources = {
                        "memory": {
                            "personal": use_personal,
                            "projects": selected_projects,
                            "departments": selected_depts,
                        },
                        "rag": {"collections": [], "filters": {}}
                    }
                    result = api_request("POST", "/chat-rooms", {
                        "name": room_name,
                        "room_type": room_type,
                        "context_sources": context_sources,
                    }, st.session_state.user_id)
                    if result:
                        st.success("채팅방 생성됨!")
                        st.rerun()
        
        st.markdown("---")
        
        # 채팅방 목록
        rooms = load_chat_rooms()
        for room in rooms:
            room_label = f"{'🏠' if room['room_type']=='personal' else '📋' if room['room_type']=='project' else '🏢'} {room['name']}"
            if st.button(room_label, key=f"room_{room['id']}", use_container_width=True):
                st.session_state.current_room = room
                st.session_state.messages = load_messages(room["id"])
                st.rerun()
    
    # 오른쪽: 채팅 화면
    with col2:
        if st.session_state.current_room:
            room = st.session_state.current_room
            st.subheader(f"{room['name']}")
            
            # 메모리 소스 표시
            context = room.get("context_sources", {})
            memory_config = context.get("memory", {})
            sources = []
            if memory_config.get("personal"):
                sources.append("개인")
            if memory_config.get("projects"):
                sources.append(f"프로젝트({len(memory_config['projects'])})")
            if memory_config.get("departments"):
                sources.append(f"부서({len(memory_config['departments'])})")
            st.caption(f"📦 메모리 소스: {', '.join(sources) if sources else '없음'}")
            
            st.markdown("---")
            
            # 메시지 표시
            chat_container = st.container(height=400)
            with chat_container:
                for msg in st.session_state.messages:
                    if msg["role"] == "assistant":
                        with st.chat_message("assistant"):
                            st.markdown(msg["content"])
                    else:
                        with st.chat_message("user"):
                            user_name = msg.get("user_name", "Unknown")
                            st.markdown(f"**{user_name}**: {msg['content']}")
            
            # 메시지 입력
            st.markdown("---")
            st.caption("💡 `@ai` AI 호출 | `/remember` 메모리 저장 | `/help` 도움말")
            
            user_input = st.chat_input("메시지를 입력하세요...")
            
            if user_input:
                with st.spinner("전송 중..."):
                    result = api_request("POST", f"/chat-rooms/{room['id']}/messages", {
                        "content": user_input,
                    }, st.session_state.user_id)
                
                if result:
                    # 메시지 목록 새로고침
                    st.session_state.messages = load_messages(room["id"])
                    
                    # 추출된 메모리가 있으면 토스트로 표시
                    if result.get("extracted_memories"):
                        st.session_state.memory_toast = result["extracted_memories"]
                    
                    st.rerun()
        else:
            st.info("👈 왼쪽에서 채팅방을 선택하거나 새로 만드세요.")


# 탭 2: 메모리 검색
with tab2:
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
    
    if st.button("🔍 검색", type="primary", key="search_btn"):
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


# 탭 3: 메모리 저장
with tab3:
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


# 탭 4: 메모리 목록
with tab4:
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
            content_preview = memory['content'][:50] + ('...' if len(memory['content']) > 50 else '')
            with st.expander(f"📝 {content_preview}", expanded=False):
                st.markdown(f"**내용:** {memory['content']}")
                st.markdown(f"**범위:** {memory['scope']}")
                st.markdown(f"**카테고리:** {memory.get('category', '-')}")
                st.markdown(f"**중요도:** {memory.get('importance', '-')}")
                st.markdown(f"**생성일:** {memory['created_at']}")
                st.caption(f"ID: {memory['id']}")
    else:
        st.info("저장된 메모리가 없습니다.")


# 탭 5: 자동 추출
with tab5:
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
