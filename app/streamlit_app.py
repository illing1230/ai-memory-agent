"""AI Memory Agent - Streamlit 데모 UI (Frontend UI 스타일 적용)"""
import os
import httpx
import streamlit as st

# API 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://10.244.14.73:8000/api/v1")

# 페이지 설정
st.set_page_config(
    page_title="AI Memory Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS (Streamlit 기본 테마 사용)
st.markdown("""
<style>
/* 내 메시지 우측 정렬 */
div[data-testid="stChatMessage"]:has(.my-msg-marker) {
    flex-direction: row-reverse;
}

div[data-testid="stChatMessage"]:has(.my-msg-marker) [data-testid="stMarkdownContainer"] {
    text-align: right;
}

.my-msg-marker {
    display: none;
}
</style>
""", unsafe_allow_html=True)

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
if "page" not in st.session_state:
    st.session_state.page = "chat"


def api_request(method: str, endpoint: str, data: dict = None, user_id: str = None):
    """API 요청 헬퍼"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if user_id:
        headers["X-User-ID"] = user_id
    
    try:
        # 프록시 비활성화 (내부망 직접 접속)
        with httpx.Client(timeout=60.0, proxy=None) as client:
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


def load_my_projects():
    """내가 속한 프로젝트 목록"""
    if not st.session_state.user_id:
        return []
    return api_request("GET", f"/users/{st.session_state.user_id}/projects") or []


def load_my_department():
    """내 부서 조회"""
    if not st.session_state.user_id:
        return None
    return api_request("GET", f"/users/{st.session_state.user_id}/department")


def load_chat_rooms():
    """내가 속한 대화방 목록"""
    return api_request("GET", "/chat-rooms", user_id=st.session_state.user_id) or []


def load_messages(room_id: str):
    """대화방 메시지 로드"""
    return api_request("GET", f"/chat-rooms/{room_id}/messages", user_id=st.session_state.user_id) or []


def render_chat_messages(messages: list, current_user_id: str):
    """Streamlit 기본 컴포넌트로 메시지 렌더링"""
    for msg in messages:
        user_id = msg.get("user_id", "")
        user_name = msg.get("user_name", "Unknown")
        content = msg.get("content", "")
        role = msg.get("role", "user")
        created_at = msg.get("created_at", "")[:16].replace("T", " ")
        
        if role == "assistant":
            # AI 메시지 (왼쪽)
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**AI Assistant** · {created_at}")
                st.markdown(content)
        elif user_id == current_user_id:
            # 내 메시지 (오른쪽)
            with st.chat_message("user", avatar="🧑"):
                st.markdown('<span class="my-msg-marker"></span>', unsafe_allow_html=True)
                st.markdown(f"**나** · {created_at}")
                st.markdown(content)
        else:
            # 다른 사람 메시지 (왼쪽)
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{user_name}** · {created_at}")
                st.markdown(content)


def show_memory_toast():
    """메모리 저장 토스트 표시"""
    if st.session_state.memory_toast:
        memories = st.session_state.memory_toast
        
        with st.container():
            st.success(f"🧠 메모리 자동 저장됨 ({len(memories)}개)")
            for mem in memories[:3]:
                content = mem.get('content', '')[:50]
                if len(mem.get('content', '')) > 50:
                    content += '...'
                st.info(f"📝 {content}")
            if len(memories) > 3:
                st.caption(f"+{len(memories) - 3}개 더...")
            st.session_state.memory_toast = None


# ==================== 사이드바 ====================
with st.sidebar:
    # 헤더
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #3b82f6;">
            <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08V3a2.5 2.5 0 0 1 5.42-1z"/>
            <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08V3a2.5 2.5 0 0 0-5.42-1z"/>
        </svg>
        <span style="font-weight: 600; font-size: 1rem;">Memory Agent</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 빠른 검색
    if st.button("메모리 검색", key="quick_search", use_container_width=True, icon="🔍"):
        st.session_state.page = "search"
        st.rerun()
    
    st.markdown("---")
    
    # 사용자 선택
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
        </svg>
        <span style="font-weight: 600; font-size: 0.875rem;">사용자</span>
    </div>
    """, unsafe_allow_html=True)
    
    users = load_users()
    
    if users:
        user_options = {f"{u['name']} ({u['email']})": u['id'] for u in users}
        selected_user = st.selectbox(
            "",
            options=list(user_options.keys()),
            index=0 if user_options else None,
            label_visibility="collapsed",
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
                    result = api_request("POST", "/users", {"name": new_name, "email": new_email})
                    if result:
                        st.success("사용자 생성됨!")
                        st.rerun()
    
    st.markdown("---")
    
    # 대화방 섹션
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span style="font-weight: 600; font-size: 0.875rem;">대화방</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.page == "chat" and st.session_state.user_id:
        # 새 대화방 생성
        with st.expander("새 대화방"):
            room_name = st.text_input("대화방 이름", key="new_room_name")
            
            st.markdown("**메모리 소스**")
            st.caption("이 대화방 메모리는 기본 포함됩니다")
            
            # 내가 속한 다른 대화방
            my_rooms = load_chat_rooms()
            other_rooms = []
            if my_rooms:
                st.markdown("다른 대화방:")
                for r in my_rooms:
                    if st.checkbox(r["name"], key=f"other_room_{r['id']}"):
                        other_rooms.append(r["id"])
            
            # 내가 속한 프로젝트
            my_projects = load_my_projects()
            selected_projects = []
            if my_projects:
                st.markdown("내 프로젝트:")
                for proj in my_projects:
                    if st.checkbox(proj["name"], key=f"proj_{proj['id']}"):
                        selected_projects.append(proj["id"])
            
            # 내 부서
            my_dept = load_my_department()
            selected_depts = []
            if my_dept:
                st.markdown("내 부서:")
                if st.checkbox(my_dept["name"], key=f"dept_{my_dept['id']}"):
                    selected_depts.append(my_dept["id"])
            
            if st.button("대화방 생성", type="primary"):
                if room_name:
                    context_sources = {
                        "memory": {
                            "include_this_room": True,
                            "other_chat_rooms": other_rooms,
                            "projects": selected_projects,
                            "departments": selected_depts,
                        },
                        "rag": {"collections": [], "filters": {}}
                    }
                    result = api_request("POST", "/chat-rooms", {
                        "name": room_name,
                        "room_type": "personal",
                        "context_sources": context_sources,
                    }, st.session_state.user_id)
                    if result:
                        st.success("대화방 생성됨!")
                        st.session_state.current_room = result
                        st.rerun()
        
        # 대화방 목록
        rooms = load_chat_rooms()
        if rooms:
            for room in rooms:
                role = room.get("member_role", "member")
                room_type = room.get("room_type", "personal")
                room_id = room["id"]
                
                # 룸 타입 아이콘
                if room_type == "personal":
                    type_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 7 7"/></svg>'
                elif room_type == "project":
                    type_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>'
                elif room_type == "department":
                    type_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h1v4"/><path d="M15 6h1v4"/></svg>'
                else:
                    type_icon = ''
                
                # 역할 아이콘
                if role == "owner":
                    role_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #f59e0b;"><path d="m12 3-1.912 5.813a2 2 0 0 0-1.278 1.278L4.5 12l4.31 4.31a2 2 0 0 0 1.278 1.278L12 21l1.912-5.813a2 2 0 0 0 1.278-1.278L19.5 12l-4.31-4.31a2 2 0 0 0-1.278-1.278z"/></svg>'
                elif role == "admin":
                    role_icon = '<svg xmlns="http://www.w33.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #f59e0b;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 6.86 14.14 2 9.27 8.91 8.26 12 2z"/></svg>'
                else:
                    role_icon = ''
                
                is_current = st.session_state.current_room and st.session_state.current_room.get("id") == room["id"]
                                
                # 룸 타입 이모지
                if room_type == "personal":
                    type_emoji = "🏠"
                elif room_type == "project":
                    type_emoji = "📋"
                elif room_type == "department":
                    type_emoji = "🏢"
                else:
                    type_emoji = "💬"
                                
                # 역할 이모지
                if role == "owner":
                    role_emoji = "💎"
                elif role == "admin":
                    role_emoji = "⭐"
                else:
                    role_emoji = ""
                                
                # Streamlit 네이티브 버튼 사용
                button_label = f"{type_emoji} {room['name']} {role_emoji}"
                if st.button(button_label, key=f"room_{room_id}", use_container_width=True, type="primary" if is_current else "secondary"):
                    st.session_state.current_room = room
                    st.session_state.messages = load_messages(room["id"])
                    st.rerun()
        else:
            st.info("대화방이 없습니다")
    
    st.markdown("---")
    
    # 메모리 섹션
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #3b82f6;">
            <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08V3a2.5 2.5 0 0 1 5.42-1z"/>
            <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08V3a2.5 2.5 0 0 0-5.42-1z"/>
        </svg>
        <span style="font-weight: 600; font-size: 0.875rem;">메모리</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("검색", use_container_width=True, type="primary" if st.session_state.page == "search" else "secondary"):
        st.session_state.page = "search"
        st.rerun()
    
    if st.button("목록", use_container_width=True, type="primary" if st.session_state.page == "list" else "secondary"):
        st.session_state.page = "list"
        st.rerun()
    
    st.markdown("---")
    
    # 프로젝트 섹션
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>
            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
        </svg>
        <span style="font-weight: 600; font-size: 0.875rem;">프로젝트</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("프로젝트 관리", use_container_width=True, type="primary" if st.session_state.page == "project" else "secondary"):
        st.session_state.page = "project"
        st.rerun()
    
    st.markdown("---")
    
    # 사용자 정보
    if st.session_state.user_id:
        users = load_users()
        current_user = next((u for u in users if u['id'] == st.session_state.user_id), None)
        if current_user:
            st.info(f"**{current_user['name']}**\n{current_user['email']}")
    
    # 커맨드 도움말
    with st.expander("커맨드 도움말"):
        st.markdown("""
        **메모리**
        - `/remember <내용>` - 저장
        - `/search <검색어>` - 검색
        - `/forget <검색어>` - 삭제
        
        **대화방**
        - `/members` - 멤버 목록
        - `/invite <이메일>` - 초대
        
        **AI**
        - `@ai <질문>` - AI 호출
        """)
    
    st.caption("Made by Automation Innovation Group")


# ==================== 메인 콘텐츠 ====================
show_memory_toast()

if not st.session_state.user_id:
    st.warning("👈 사이드바에서 사용자를 선택하세요.")
    st.stop()

# ==================== 채팅 페이지 ====================
if st.session_state.page == "chat":
    if st.session_state.current_room:
        room = st.session_state.current_room
        
        # 헤더
        st.markdown(f"""
        <div class="main-header">
            <h2 style="margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                {room['name']}
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 메모리 소스 표시
        context = room.get("context_sources", {})
        memory_config = context.get("memory", {})
        sources = ["이 대화방"]
        if memory_config.get("other_chat_rooms"):
            sources.append(f"다른방({len(memory_config['other_chat_rooms'])})")
        if memory_config.get("projects"):
            sources.append(f"프로젝트({len(memory_config['projects'])})")
        if memory_config.get("departments"):
            sources.append(f"부서({len(memory_config['departments'])})")
        
        st.markdown("메모리 소스: " + " ".join([f'<span class="memory-source-tag">{s}</span>' for s in sources]), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Streamlit 기본 chat_message로 메시지 표시
        render_chat_messages(st.session_state.messages, st.session_state.user_id)
        
        # 메시지 입력
        st.markdown("---")
        st.caption("`@ai` AI 호출 | `/remember` 저장 | `/help` 도움말")
        
        user_input = st.chat_input("메시지를 입력하세요...")
        
        if user_input:
            with st.spinner("전송 중..."):
                result = api_request("POST", f"/chat-rooms/{room['id']}/messages", {
                    "content": user_input,
                }, st.session_state.user_id)
                
                if result:
                    st.session_state.messages = load_messages(room["id"])
                    if result.get("extracted_memories"):
                        st.session_state.memory_toast = result["extracted_memories"]
                    st.rerun()
    else:
        st.info("사이드바에서 대화방을 선택하거나 새로 만드세요.")

# ==================== 프로젝트 페이지 ====================
elif st.session_state.page == "project":
    st.markdown("""
    <div class="main-header">
        <h2 style="margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
            </svg>
            프로젝트 관리
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    # 왼쪽: 프로젝트 목록
    with col1:
        st.subheader("내 프로젝트")
        
        # 새 프로젝트 생성
        with st.expander("새 프로젝트"):
            proj_name = st.text_input("프로젝트 이름", key="new_proj_name")
            proj_desc = st.text_area("설명", key="new_proj_desc", height=100)
            
            if st.button("프로젝트 생성", type="primary", key="create_proj"):
                if proj_name:
                    result = api_request("POST", "/users/projects", {
                        "name": proj_name,
                        "description": proj_desc,
                    }, st.session_state.user_id)
                    if result:
                        st.success("프로젝트 생성됨!")
                        st.rerun()
        
        st.markdown("---")
        
        # 내 프로젝트 목록
        my_projects = load_my_projects()
        if my_projects:
            for proj in my_projects:
                role = proj.get("member_role", "member")
                
                # 역할 아이콘
                if role == "owner":
                    role_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #f59e0b;"><path d="m12 3-1.912 5.813a2 2 0 0 0-1.278 1.278L4.5 12l4.31 4.31a2 2 0 0 0 1.278 1.278L12 21l1.912-5.813a2 2 0 0 0 1.278-1.278L19.5 12l-4.31-4.31a2 2 0 0 0-1.278-1.278z"/></svg>'
                elif role == "admin":
                    role_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #f59e0b;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 6.86 14.14 2 9.27 8.91 8.26 12 2z"/></svg>'
                else:
                    role_icon = ''
                
                if st.button(f"{proj['name']} {role_icon}", key=f"proj_select_{proj['id']}", use_container_width=True):
                    st.session_state.selected_project = proj
                    st.rerun()
        else:
            st.info("프로젝트가 없습니다")
    
    # 오른쪽: 프로젝트 상세
    with col2:
        if "selected_project" in st.session_state and st.session_state.selected_project:
            proj = st.session_state.selected_project
            my_role = proj.get("member_role", "member")
            
            st.subheader(f"📋 {proj['name']}")
            st.caption(f"내 역할: {my_role}")
            
            if proj.get("description"):
                st.markdown(f"**설명:** {proj['description']}")
            
            st.markdown("---")
            
            # 멤버 목록
            st.markdown("### 멤버")
            members = api_request("GET", f"/users/projects/{proj['id']}/members")
            
            if members:
                for m in members:
                    role = m.get("role", "member")
                    if role == "owner":
                        role_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #f59e0b;"><path d="m12 3-1.912 5.813a2 2 0 0 0-1.278 1.278L4.5 12l4.31 4.31a2 2 0 0 0 1.278 1.278L12 21l1.912-5.813a2 2 0 0 0 1.278-1.278L19.5 12l-4.31-4.31a2 2 0 0 0-1.278-1.278z"/></svg>'
                    elif role == "admin":
                        role_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #f59e0b;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 6.86 14.14 2 9.27 8.91 8.26 12 2z"/></svg>'
                    else:
                        role_icon = ''
                    st.markdown(f"{role_icon} **{m.get('user_name', 'Unknown')}** - {m.get('user_email', '')}")
            
            # 멤버 추가 (owner/admin만)
            if my_role in ["owner", "admin"]:
                st.markdown("---")
                st.markdown("### 멤버 초대")
                
                # 전체 사용자 목록에서 선택
                all_users = load_users()
                member_ids = [m["user_id"] for m in members] if members else []
                available_users = [u for u in all_users if u["id"] not in member_ids]
                
                if available_users:
                    user_options = {f"{u['name']} ({u['email']})": u['id'] for u in available_users}
                    selected_user_to_add = st.selectbox("사용자 선택", options=list(user_options.keys()), key="add_member_select")
                    member_role = st.selectbox("역할", ["member", "admin"], key="add_member_role")
                    
                    if st.button("멤버 추가", type="primary", key="add_member_btn"):
                        if selected_user_to_add:
                            target_user_id = user_options[selected_user_to_add]
                            result = api_request("POST", f"/users/projects/{proj['id']}/members", {
                                "user_id": target_user_id,
                                "role": member_role,
                            }, st.session_state.user_id)
                            if result:
                                st.success("멤버 추가됨!")
                                st.rerun()
                else:
                    st.info("추가할 수 있는 사용자가 없습니다")
            
            # 프로젝트 삭제 (owner만)
            if my_role == "owner":
                st.markdown("---")
                with st.expander("위험 영역"):
                    st.warning("프로젝트를 삭제하면 복구할 수 없습니다.")
                    if st.button("프로젝트 삭제", type="primary", key="delete_proj"):
                        result = api_request("DELETE", f"/users/projects/{proj['id']}", user_id=st.session_state.user_id)
                        if result:
                            st.success("프로젝트 삭제됨!")
                            st.session_state.selected_project = None
                            st.rerun()
        else:
            pass

# ==================== 메모리 검색 페이지 ====================
elif st.session_state.page == "search":
    st.markdown("""
    <div class="main-header">
        <h2 style="margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
            </svg>
            메모리 시맨틱 검색
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("검색어", placeholder="예: 회의 일정, 선호하는 도구...")
    with col2:
        search_limit = st.number_input("결과 수", min_value=1, max_value=20, value=5)
    
    if st.button("검색", type="primary"):
        if search_query:
            with st.spinner("검색 중..."):
                result = api_request("POST", "/memories/search", 
                    {"query": search_query, "limit": search_limit},
                    st.session_state.user_id)
                
                if result and result.get("results"):
                    st.success(f"{len(result['results'])}개 결과 발견")
                    
                    for item in result["results"]:
                        memory = item["memory"]
                        score = item["score"]
                        
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{memory['content']}**")
                            scope_label = "대화방" if memory['scope'] == 'chatroom' else memory['scope']
                            st.caption(f"{scope_label} | {memory.get('category', '-')}")
                        with col2:
                            st.metric("유사도", f"{score:.0%}")
                        st.divider()
                else:
                    st.info("검색 결과가 없습니다.")
        else:
            st.warning("검색어를 입력하세요.")

# ==================== 메모리 목록 페이지 ====================
elif st.session_state.page == "list":
    st.markdown("""
    <div class="main-header">
        <h2 style="margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/>
                <polyline points="16 6 20 10 10 4 6"/>
            </svg>
            내 메모리 목록
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("새로고침"):
        st.rerun()
    
    with st.spinner("로딩 중..."):
        memories = api_request("GET", "/memories", user_id=st.session_state.user_id)
        
        if memories:
            st.success(f"총 {len(memories)}개 메모리")
            
            for memory in memories:
                content_preview = memory['content'][:50] + ('...' if len(memory['content']) > 50 else '')
                scope_label = "대화방" if memory['scope'] == 'chatroom' else memory['scope']
                
                with st.expander(f"{content_preview}"):
                    st.markdown(f"**내용:** {memory['content']}")
                    st.markdown(f"**범위:** {scope_label}")
                    st.markdown(f"**카테고리:** {memory.get('category', '-')}")
                    st.markdown(f"**중요도:** {memory.get('importance', '-')}")
                    st.markdown(f"**생성일:** {memory['created_at']}")
        else:
            st.info("저장된 메모리가 없습니다.")

# 푸터
st.markdown("---")
st.caption("AI Memory Agent v0.2.0 | 대화방 + 프로젝트 기반 메모리 관리")
