#!/usr/bin/env python3
"""테스트용 문서 업로드 스크립트"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx

async def upload_document():
    """문서 업로드"""
    api_key = os.getenv("AI_MEMORY_AGENT_API_KEY")
    base_url = os.getenv("AI_MEMORY_AGENT_URL", "http://localhost:8000")
    
    if not api_key:
        print("AI_MEMORY_AGENT_API_KEY 환경 변수를 설정해주세요.")
        sys.exit(1)
    
    # 테스트용 문서 파일
    doc_path = "/tmp/test_doc.txt"
    if not os.path.exists(doc_path):
        print(f"문서 파일이 없습니다: {doc_path}")
        sys.exit(1)
    
    with open(doc_path, 'rb') as f:
        files = {'file': ('test_doc.txt', f, 'text/plain')}
        headers = {'X-API-Key': api_key}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/documents",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"문서 업로드 성공!")
                print(f"  문서 ID: {result['id']}")
                print(f"  파일명: {result['name']}")
                print(f"  상태: {result['status']}")
                print(f"  청크 수: {result['chunk_count']}")
            else:
                print(f"문서 업로드 실패: {response.status_code}")
                print(f"  응답: {response.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(upload_document())
