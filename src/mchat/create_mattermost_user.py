"""Mattermost 서버에 사용자 생성 스크립트"""

import asyncio
import sys
from src.mchat.client import MchatClient
from src.config import get_settings


async def create_mattermost_user(
    email: str,
    username: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
):
    """Mattermost 서버에 사용자 생성"""
    
    settings = get_settings()
    
    if not settings.mchat_enabled or not settings.mchat_token:
        print("❌ Mchat이 비활성화되어 있거나 토큰이 없습니다.")
        print(f"   MCHAT_ENABLED={settings.mchat_enabled}")
        print(f"   MCHAT_URL={settings.mchat_url}")
        return False
    
    client = MchatClient()
    
    try:
        # 사용자가 이미 존재하는지 확인
        try:
            existing_user = await client.get_user_by_username(username)
            print(f"⚠️  사용자 '{username}'이 이미 존재합니다 (ID: {existing_user['id']})")
            return False
        except Exception:
            # 사용자가 존재하지 않음 - 계속 진행
            pass
        
        # 사용자 생성 API (관리자 토큰 필요)
        # Bot 토큰으로는 사용자 생성 불가능
        print(f"📝 사용자 생성 시도: {email}")
        print(f"   사용자명: {username}")
        print(f"   비밀번호: {password}")
        print(f"   이름: {first_name} {last_name}")
        print()
        print("⚠️  사용자 생성에는 Mattermost 관리자 토큰이 필요합니다.")
        print("   현재 MCHAT_TOKEN은 Bot 토큰일 가능성이 높습니다.")
        print()
        print("📋 수동 생성 방법:")
        print(f"   1. Mattermost 웹 접속: {settings.mchat_url}")
        print("   2. 관리자로 로그인")
        print("   3. System Console > Users > Add User")
        print(f"   4. Email: {email}")
        print(f"   5. Username: {username}")
        print(f"   6. Password: {password}")
        print(f"   7. First Name: {first_name}")
        print(f"   8. Last Name: {last_name}")
        
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


async def main():
    """메인 함수"""
    
    # 사용자 정보
    email = "local@test.com"
    username = "localtest"
    password = "test123"
    first_name = "Local"
    last_name = "Test"
    
    print("=" * 60)
    print("Mattermost 사용자 생성")
    print("=" * 60)
    print()
    
    await create_mattermost_user(email, username, password, first_name, last_name)
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
