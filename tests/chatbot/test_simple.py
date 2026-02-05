#!/usr/bin/env python3
"""간단한 연결 테스트"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_memory_agent_sdk import Agent

def main():
    api_key = os.getenv("AI_MEMORY_AGENT_API_KEY")
    if not api_key:
        print("AI_MEMORY_AGENT_API_KEY 환경 변수를 설정해주세요.")
        sys.exit(1)

    print("Agent 초기화 중...")
    agent = Agent(
        api_key=api_key,
        base_url=os.getenv("AI_MEMORY_AGENT_URL", "http://localhost:8000"),
        agent_id=os.getenv("AGENT_ID", "My Bot"),
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_url=os.getenv("LLM_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL"),
    )

    print("서버 헬스 체크...")
    if agent.health():
        print("✓ 서버 연결 성공")
    else:
        print("✗ 서버 연결 실패")

    print("\nLLM 테스트: '안녕하세요?'")
    try:
        response = agent.message("안녕하세요?")
        print(f"✓ 응답: {response}")
    except Exception as e:
        print(f"✗ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
