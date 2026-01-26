"""
Mchat Integration 사용 예시

실행:
    python -m src.mchat.example
"""

import asyncio
from src.mchat.client import MchatClient
from src.config import get_settings


async def main():
    settings = get_settings()
    
    # 디버그 출력
    print(f"MCHAT_URL: {settings.mchat_url}")
    print(f"MCHAT_TOKEN: {settings.mchat_token[:10] if settings.mchat_token else 'None'}...")
    print(f"MCHAT_ENABLED: {settings.mchat_enabled}")
    
    if not settings.mchat_enabled:
        print("Mchat is disabled. Set MCHAT_ENABLED=true in .env")
        return
    
    if not settings.mchat_token:
        print("MCHAT_TOKEN is not set in .env")
        return
    
    # 클라이언트 생성
    client = MchatClient()
    
    # 1. 연결 테스트 - 내 정보 조회
    print("\n=== 1. Bot 정보 조회 ===")
    try:
        me = await client.get_me()
        print(f"Bot ID: {me['id']}")
        print(f"Username: {me['username']}")
        print(f"Nickname: {me.get('nickname', '-')}")
    except Exception as e:
        print(f"연결 실패: {e}")
        return
    
    # 2. 팀 목록 조회
    print("\n=== 2. 팀 목록 ===")
    teams = await client.get_teams()
    for team in teams:
        print(f"  - {team['display_name']} ({team['name']})")
    
    # 3. 첫 번째 팀의 채널 목록
    if teams:
        print(f"\n=== 3. '{teams[0]['display_name']}' 팀 채널 ===")
        channels = await client.get_channels_for_team(teams[0]["id"])
        for ch in channels[:10]:  # 상위 10개만
            ch_type = {"O": "공개", "P": "비공개", "D": "DM", "G": "그룹DM"}.get(ch["type"], ch["type"])
            print(f"  - [{ch_type}] {ch['display_name'] or ch['name']}")
    
    # 4. 이벤트 핸들러 등록
    @client.on("posted")
    async def handle_message(event):
        """새 메시지 수신 시"""
        data = event.get("data", {})
        post = data.get("post", {})
        
        message = post.get("message", "")
        channel_id = post.get("channel_id", "")
        user_id = post.get("user_id", "")
        post_id = post.get("id", "")
        
        # AI 응답 메시지는 무시 (무한루프 방지)
        if message.startswith("🤖"):
            return
        
        print(f"\n[새 메시지] user={user_id}, msg={message[:50]}...")
        
        # 1. 모든 메시지 저장 (내 메시지 포함)
        # TODO: DB에 메시지 저장
        print(f"  [저장] channel={channel_id}, user={user_id}")
        
        # 2. @ai 멘션 또는 /remember 커맨드 처리 (내 메시지도 포함 - 테스트용)
        if "@ai" in message.lower() or message.startswith("/remember"):
            response = f"🤖 메시지를 받았습니다: {message[:30]}..."
            
            await client.create_post(
                channel_id=channel_id,
                message=response,
                # root_id 제거 - DM에서는 Thread 지원 안 될 수 있음
            )
            print(f"  [응답 전송] {response}")
    
    @client.on("typing")
    async def handle_typing(event):
        """타이핑 중 이벤트"""
        data = event.get("data", {})
        user_id = data.get("user_id", "")
        if user_id != me["id"]:
            print(f"[타이핑 중] user={user_id}")
    
    # 5. WebSocket 연결 시작
    print("\n=== 4. WebSocket 연결 (Ctrl+C로 종료) ===")
    print("메시지를 기다리는 중...")
    
    try:
        await client.connect_websocket()
    except KeyboardInterrupt:
        print("\n종료 중...")
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
