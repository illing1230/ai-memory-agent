"""
Mchat 연결 디버깅 스크립트

로컬 Mattermost 또는 Samsung Mchat 서버 연결 테스트.
.env 설정을 자동으로 사용합니다.

실행:
    python -m src.mchat.debug_connection
"""

import asyncio

from src.config import get_settings
from src.mchat.client import MchatClient


async def test_connection():
    settings = get_settings()

    print("=" * 50)
    print("Mchat 연결 테스트")
    print("=" * 50)
    print(f"URL: {settings.mchat_url}")
    print(f"Token: {'***' + settings.mchat_token[-4:] if settings.mchat_token else '(not set)'}")
    print(f"SSL Verify: {settings.mchat_ssl_verify}")
    print()

    if not settings.mchat_token:
        print("MCHAT_TOKEN이 설정되지 않았습니다.")
        print(".env 파일에 MCHAT_TOKEN을 설정하세요.")
        return

    client = MchatClient()

    # 1. Ping 테스트
    print("--- 1. Server Ping ---")
    try:
        ok = await client.ping()
        print(f"  Ping: {'OK' if ok else 'FAIL'}")
    except Exception as e:
        print(f"  Ping error: {e}")

    # 2. Bot 정보 조회
    print("\n--- 2. Bot Info (GET /api/v4/users/me) ---")
    try:
        me = await client.get_me()
        print(f"  ID: {me['id']}")
        print(f"  Username: {me['username']}")
        print(f"  Email: {me.get('email', '-')}")
        print(f"  Roles: {me.get('roles', '-')}")
        print(f"  Is Bot: {me.get('is_bot', False)}")
    except Exception as e:
        print(f"  Error: {e}")
        print("\n  가능한 원인:")
        print("  - 토큰이 올바르지 않음")
        print("  - Bot Account가 생성되지 않음")
        print("  - Personal Access Token이 활성화되지 않음")
        return

    # 3. 팀 목록
    print("\n--- 3. Teams ---")
    try:
        teams = await client.get_teams()
        for t in teams:
            print(f"  - {t['display_name']} (id: {t['id'][:8]})")
    except Exception as e:
        print(f"  Error: {e}")

    # 4. 채널 목록
    print("\n--- 4. Channels ---")
    try:
        teams = await client.get_teams()
        for team in teams:
            channels = await client.get_channels_for_team(team["id"])
            print(f"  Team: {team['display_name']}")
            for ch in channels[:10]:
                ch_type = ch.get("type", "?")
                name = ch.get("display_name") or ch.get("name", "?")
                print(f"    - [{ch_type}] {name} (id: {ch['id'][:8]})")
            if len(channels) > 10:
                print(f"    ... +{len(channels) - 10} more")
    except Exception as e:
        print(f"  Error: {e}")

    # 5. 메시지 전송 테스트
    print("\n--- 5. Post Test ---")
    try:
        teams = await client.get_teams()
        if teams:
            channels = await client.get_channels_for_team(teams[0]["id"])
            # Town Square 채널 찾기
            town_square = next(
                (ch for ch in channels if ch.get("name") == "town-square"),
                channels[0] if channels else None
            )
            if town_square:
                post = await client.create_post(
                    channel_id=town_square["id"],
                    message="AI Memory Bot 연결 테스트입니다.",
                )
                print(f"  Message posted! ID: {post['id'][:8]}")
                # 테스트 메시지 삭제
                await client.delete_post(post["id"])
                print(f"  Test message deleted.")
            else:
                print("  No channels found to test posting.")
    except Exception as e:
        print(f"  Post error: {e}")

    print("\n" + "=" * 50)
    print("연결 테스트 완료!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_connection())
