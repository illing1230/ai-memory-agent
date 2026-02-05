#!/usr/bin/env python3
"""테스트용 문서 업로드 스크립트 (사용자 인증)"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx

async def login_and_upload():
    """로그인 후 문서 업로드"""
    base_url = os.getenv("AI_MEMORY_AGENT_URL", "http://localhost:8000")
    
    # 1. 로그인
    print("1. 로그인 중...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        login_response = await client.post(
            f"{base_url}/auth/login",
            json={
                "email": "dev@test.local",
                "password": "test123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"로그인 실패: {login_response.status_code}")
            print(f"  응답: {login_response.text}")
            sys.exit(1)
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        print(f"로그인 성공! 토큰: {access_token[:20]}...")
        
        # 2. 문서 업로드
        print("\n2. 문서 업로드 중...")
        doc_path = "/tmp/test_doc.txt"
        if not os.path.exists(doc_path):
            print(f"문서 파일이 없습니다: {doc_path}")
            sys.exit(1)
        
        with open(doc_path, 'rb') as f:
            files = {'file': ('test_doc.txt', f, 'text/plain')}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            upload_response = await client.post(
                f"{base_url}/documents/upload",
                files=files,
                headers=headers
            )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                print(f"문서 업로드 성공!")
                print(f"  문서 ID: {result['id']}")
                print(f"  파일명: {result['name']}")
                print(f"  상태: {result['status']}")
                print(f"  청크 수: {result['chunk_count']}")
            else:
                print(f"문서 업로드 실패: {upload_response.status_code}")
                print(f"  응답: {upload_response.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(login_and_upload())
