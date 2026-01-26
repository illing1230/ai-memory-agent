"""AI Memory Agent - Streamlit 데모 UI (개선판)"""

import streamlit as st
import httpx
import json

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
if "page" not in st.session_state:
    st.session_state.page = "chat"


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
    """내가 속한 채팅방 목록"""
    return api_request("GET", "/chat-rooms", user_id=st.session_state.user_id) or []


def load_messages(room_id: str):
    """채팅방 메시지 로드"""
    return api_request("GET", f"/chat-rooms/{room_id}/messages", user_id=st.session_state.user_id) or []


def show_memory_toast():
    """메모리 저장 토스트 표시"""
    if st.session_state.memory_toast:
        memories = st.session_state.memory_toast
        
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
        
        for mem in memories[:3]:
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
        st.session_state.memory_toast = None


# ==================== 사이드바 ====================
with st.sidebar:
    st.title("🧠 AI Memory Agent")
    st.markdown("---")
    
    # 사용자 선택
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
                    result = api_request("POST", "/users", {"name": new_name, "email": new_email})
                    if result:
                        st.success("사용자 생성됨!")
                        st.rerun()
    
    st.markdown("---")
    
    # 페이지 네비게이션
    st.subheader("📌 메뉴")
    if st.button("💬 채팅", use_container_width=True, type="primary" if st.session_state.page == "chat" else "secondary"):
        st.session_state.page = "chat"
        st.rerun()
    if st.button("🔍 메모리 검색", use_container_width=True, type="primary" if st.session_state.page == "search" else "secondary"):
        st.session_state.page = "search"
        st.rerun()
    if st.button("📋 메모리 목록", use_container_width=True, type="primary" if st.session_state.page == "list" else "secondary"):
        st.session_state.page = "list"
        st.rerun()
    
    st.markdown("---")
    
    # 채팅방 목록 (채팅 페이지일 때만)
    if st.session_state.page == "chat" and st.session_state.user_id:
        st.subheader("💬 채팅방")
        
        # 새 채팅방 생성
        with st.expander("➕ 새 채팅방"):
            room_name = st.text_input("채팅방 이름", key="new_room_name")
            
            st.markdown("**📦 메모리 소스**")
            st.caption("이 채팅방 메모리는 기본 포함됩니다")
            
            # 내가 속한 다른 채팅방
            my_rooms = load_chat_rooms()
            other_rooms = []
            if my_rooms:
                st.markdown("다른 채팅방:")
                for r in my_rooms:
                    if st.checkbox(r["name"], key=f"other_room_{r['id']}"):
                        other_rooms.append(r["id"])
            
            # 내 개인 메모리 전체
            include_personal = st.checkbox("⚠️ 내 개인 메모리 전체", value=False, key="include_personal")
            if include_personal:
                st.warning("주의: 모든 개인 메모리가 공유됩니다")
            
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
            
            if st.button("채팅방 생성", type="primary"):
                if room_name:
                    context_sources = {
                        "memory": {
                            "include_this_room": True,
                            "other_chat_rooms": other_rooms,
                            "include_personal": include_personal,
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
                        st.success("채팅방 생성됨!")
                        st.session_state.current_room = result
                        st.rerun()
        
        st.markdown("---")
        
        # 채팅방 목록
        rooms = load_chat_rooms()
        if rooms:
            for room in rooms:
                role = room.get("member_role", "member")
                role_emoji = {"owner": "👑", "admin": "⭐", "member": ""}.get(role, "")
                room_emoji = {'personal': '🏠', 'project': '📋', 'department': '🏢'}.get(room['room_type'], '💬')
                
                is_current = st.session_state.current_room and st.session_state.current_room.get("id") == room["id"]
                btn_type = "primary" if is_current else "secondary"
                
                if st.button(f"{room_emoji} {room['name']} {role_emoji}", key=f"room_{room['id']}", use_container_width=True, type=btn_type):
                    st.session_state.current_room = room
                    st.session_state.messages = load_messages(room["id"])
                    st.rerun()
        else:
            st.info("채팅방이 없습니다")
    
    st.markdown("---")
    
    # 커맨드 도움말
    with st.expander("📖 커맨드 도움말"):
        st.markdown("""
        **메모리**
        - `/remember <내용>` - 저장
        - `/search <검색어>` - 검색
        - `/forget <검색어>` - 삭제
        
        **채팅방**
        - `/members` - 멤버 목록
        - `/invite <이메일>` - 초대
        
        **AI**
        - `@ai <질문>` - AI 호출
        """)
    
    st.caption("Made with ❤️ for Samsung")


# ==================== 메인 콘텐츠 ====================
show_memory_toast()

if not st.session_state.user_id:
    st.warning("👈 사이드바에서 사용자를 선택하세요.")
    st.stop()


# 채팅 페이지
if st.session_state.page == "chat":
    if st.session_state.current_room:
        room = st.session_state.current_room
        
        # 헤더
        col1, col2 = st.columns([4, 1])
        with col1:
            st.header(f"💬 {room['name']}")
        with col2:
            if st.button("🔄 새로고침"):
                st.session_state.messages = load_messages(room["id"])
                st.rerun()
        
        # 메모리 소스 표시
        context = room.get("context_sources", {})
        memory_config = context.get("memory", {})
        sources = ["이 채팅방"]
        if memory_config.get("other_chat_rooms"):
            sources.append(f"다른방({len(memory_config['other_chat_rooms'])})")
        if memory_config.get("include_personal"):
            sources.append("개인전체⚠️")
        if memory_config.get("projects"):
            sources.append(f"프로젝트({len(memory_config['projects'])})")
        if memory_config.get("departments"):
            sources.append(f"부서({len(memory_config['departments'])})")
        st.caption(f"📦 메모리 소스: {', '.join(sources)}")
        
        st.markdown("---")
        
        # 메시지 표시
        chat_container = st.container(height=500)
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
        st.caption("💡 `@ai` AI 호출 | `/remember` 저장 | `/help` 도움말")
        
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
        st.info("👈 사이드바에서 채팅방을 선택하거나 새로 만드세요.")


# 메모리 검색 페이지
elif st.session_state.page == "search":
    st.header("🔍 메모리 시맨틱 검색")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("검색어", placeholder="예: 회의 일정, 선호하는 도구...")
    with col2:
        search_limit = st.number_input("결과 수", min_value=1, max_value=20, value=5)
    
    if st.button("🔍 검색", type="primary"):
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
                        scope_label = "채팅방" if memory['scope'] == 'chatroom' else memory['scope']
                        st.caption(f"📁 {scope_label} | 🏷️ {memory.get('category', '-')}")
                    with col2:
                        st.metric("유사도", f"{score:.0%}")
                    st.divider()
            else:
                st.info("검색 결과가 없습니다.")
        else:
            st.warning("검색어를 입력하세요.")


# 메모리 목록 페이지
elif st.session_state.page == "list":
    st.header("📋 내 메모리 목록")
    
    if st.button("🔄 새로고침"):
        st.rerun()
    
    with st.spinner("로딩 중..."):
        memories = api_request("GET", "/memories", user_id=st.session_state.user_id)
    
    if memories:
        st.success(f"총 {len(memories)}개 메모리")
        
        for memory in memories:
            content_preview = memory['content'][:50] + ('...' if len(memory['content']) > 50 else '')
            scope_label = "채팅방" if memory['scope'] == 'chatroom' else memory['scope']
            
            with st.expander(f"📝 {content_preview}"):
                st.markdown(f"**내용:** {memory['content']}")
                st.markdown(f"**범위:** {scope_label}")
                st.markdown(f"**카테고리:** {memory.get('category', '-')}")
                st.markdown(f"**중요도:** {memory.get('importance', '-')}")
                st.markdown(f"**생성일:** {memory['created_at']}")
    else:
        st.info("저장된 메모리가 없습니다.")


# 푸터
st.markdown("---")
st.caption("AI Memory Agent v0.2.0 | 채팅방 기반 메모리 관리")
