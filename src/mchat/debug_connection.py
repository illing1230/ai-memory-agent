"""Mchat 연결 디버깅 스크립트"""

import asyncio
import httpx
import ssl

# 설정
MCHAT_URL = "https://mchat.samsung.com"  # 실제 URL 확인 필요
MCHAT_TOKEN = "sig14w8mj7naxnmdzghk4qa88w"

# SSL 검증 비활성화
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def test_connection():
    print("=" * 50)
    print("Mchat 연결 테스트")
    print("=" * 50)
    
    # 테스트할 인증 헤더 형식들
    auth_formats = [
        ("Bearer token", {"Authorization": f"Bearer {MCHAT_TOKEN}"}),
        ("Token only", {"Authorization": MCHAT_TOKEN}),
        ("Token header", {"Token": MCHAT_TOKEN}),
        ("X-Auth-Token", {"X-Auth-Token": MCHAT_TOKEN}),
    ]
    
    for name, headers in auth_formats:
        print(f"\n--- {name} ---")
        headers["Content-Type"] = "application/json"
        
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                # /api/v4/users/me 테스트
                response = await client.get(
                    f"{MCHAT_URL}/api/v4/users/me",
                    headers=headers,
                )
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text[:200] if response.text else '(empty)'}")
                
                if response.status_code == 200:
                    print(f"  ✅ 성공!")
                    return headers
                    
        except Exception as e:
            print(f"  ❌ 오류: {e}")
    
    # API v4가 아닌 경우 테스트
    print("\n--- API 버전 확인 ---")
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            # 루트 엔드포인트
            response = await client.get(f"{MCHAT_URL}/api/v4/system/ping")
            print(f"  /api/v4/system/ping: {response.status_code}")
            
            # 다른 버전?
            response = await client.get(f"{MCHAT_URL}/api/v3/users/me")
            print(f"  /api/v3/users/me: {response.status_code}")
            
    except Exception as e:
        print(f"  오류: {e}")
    
    return None


async def test_with_login():
    """이메일/비밀번호 로그인 테스트 (토큰이 아닌 경우)"""
    print("\n--- 세션 토큰 방식 테스트 ---")
    print("(토큰이 세션 토큰인 경우)")
    
    headers = {
        "Authorization": f"Bearer {MCHAT_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # 쿠키 기반 인증 테스트
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False, cookies={"MMAUTHTOKEN": MCHAT_TOKEN}) as client:
            response = await client.get(
                f"{MCHAT_URL}/api/v4/users/me",
                headers={"Content-Type": "application/json"},
            )
            print(f"  Cookie auth: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ 쿠키 인증 성공!")
                print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  오류: {e}")


async def main():
    working_headers = await test_connection()
    
    if not working_headers:
        await test_with_login()
        print("\n" + "=" * 50)
        print("확인 필요 사항:")
        print("=" * 50)
        print("1. MCHAT_URL이 정확한가요? (예: https://mchat.sec.samsung.net)")
        print("2. 토큰이 Personal Access Token인가요, Session Token인가요?")
        print("3. Mchat 관리자에게 API 접근 방법 문의 필요")
        print("4. 토큰에 필요한 권한이 있는지 확인")


if __name__ == "__main__":
    asyncio.run(main())
