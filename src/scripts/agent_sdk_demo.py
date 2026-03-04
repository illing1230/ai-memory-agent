"""대화형 Agent SDK 데모 스크립트

AI Memory Agent SDK를 대화형으로 테스트할 수 있는 데모 스크립트입니다.
명령어 기반 상호작용과 AI 대화 모드를 지원합니다.

Usage:
    python -m src.scripts.agent_sdk_demo
    python -m src.scripts.agent_sdk_demo --api-key sk_xxxxx
    python -m src.scripts.agent_sdk_demo --base-url http://localhost:8000
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_api_key_from_db() -> tuple[str, str, str] | None:
    """DB에서 첫 번째 활성 Agent Instance의 API 키, ID, 이름을 조회"""
    db_path = Path("data/memory.db")
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT id, api_key, name FROM agent_instances WHERE status = 'active' ORDER BY created_at DESC LIMIT 1",
        )
        row = cursor.fetchone()
        if row:
            return row[0], row[1], row[2]
        return None
    finally:
        conn.close()


def print_help():
    """도움말 출력"""
    print("""
╔══════════════════════════════════════════════════╗
║            Agent SDK 대화형 데모                 ║
╠══════════════════════════════════════════════════╣
║  /health   - 서버 헬스 체크                      ║
║  /memory   - 메모리 저장 (내용 입력)             ║
║  /message  - 메시지 전송                         ║
║  /log      - 로그 전송                           ║
║  /data     - 에이전트 데이터 조회                ║
║  /sources  - 메모리 소스 조회                    ║
║  /search   - 메모리 검색 (쿼리 입력)             ║
║  /agent    - 에이전트 정보 조회                  ║
║  /clear    - 화면 지우기                         ║
║  /help     - 도움말                              ║
║  /exit     - 종료                                ║
║                                                  ║
║  그 외 입력 → AI 대화 모드 (ENABLE_AI_CHAT=true) ║
╚══════════════════════════════════════════════════╝
""")


def ai_chat(user_message: str, client=None, agent_name: str = "Agent") -> str | None:
    """AI 대화 모드: .env의 LLM 설정을 사용하여 AI와 대화"""
    enable_ai = os.getenv("ENABLE_AI_CHAT", "false").lower() == "true"
    if not enable_ai:
        print("  AI 대화 모드가 비활성화되어 있습니다. (.env에서 ENABLE_AI_CHAT=true로 설정)")
        return None

    llm_provider = os.getenv("LLM_PROVIDER", "ollama")

    if llm_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        try:
            import anthropic
            ac = anthropic.Anthropic(api_key=api_key)
            response = ac.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": user_message}],
            )
            ai_response = response.content[0].text
        except Exception as e:
            print(f"  Anthropic API 오류: {e}")
            return None
    elif llm_provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b")
        try:
            import httpx
            resp = httpx.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": user_message}],
                    "stream": False,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            ai_response = resp.json()["message"]["content"]
        except Exception as e:
            print(f"  Ollama API 오류: {e}")
            return None
    else:
        # OpenAI 호환 API (LLM_URL 사용)
        llm_url = os.getenv("LLM_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        llm_api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "no-key"))
        model = os.getenv("LLM_MODEL", os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b"))
        try:
            import httpx
            resp = httpx.post(
                f"{llm_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {llm_api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": user_message}],
                    "max_tokens": 1024,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            ai_response = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  LLM API 오류: {e}")
            return None

    print(f"\n  [AI] {ai_response}")

    # AI 응답 메모리 저장
    save_response = os.getenv("SAVE_AI_RESPONSE", "false").lower() == "true"
    if save_response and client:
        try:
            # 사용자 메시지 저장
            client.send_memory(
                content=f"[사용자] {user_message}",
                metadata={"source": "ai_chat", "role": "user"},
            )
            # AI 응답 저장
            client.send_memory(
                content=f"[AI] {ai_response}",
                metadata={"source": "ai_chat", "role": "assistant"},
            )
            print("  (사용자 메시지 + AI 응답 메모리 저장됨)")
        except Exception as e:
            print(f"  (메모리 저장 실패: {e})")

    return ai_response


def main():
    parser = argparse.ArgumentParser(description="Agent SDK 대화형 데모")
    parser.add_argument("--api-key", help="Agent Instance API Key")
    parser.add_argument("--base-url", default="http://localhost:8000", help="서버 URL")
    args = parser.parse_args()

    # SDK import
    try:
        from ai_memory_agent_sdk import SyncClient
    except ImportError:
        print("ai_memory_agent_sdk 패키지가 설치되어 있지 않습니다.")
        print("설치: pip install -e ai_memory_agent_sdk/")
        sys.exit(1)

    # API 키 확인: 명령줄 인자 > 환경변수 > 대화형 입력 > DB 첫 번째 활성 Agent
    api_key = args.api_key or os.getenv("AGENT_API_KEY")
    agent_id = ""
    agent_name = "Agent"

    if not api_key:
        user_input = input("API Key를 입력하세요 (Enter로 DB에서 자동 조회): ").strip()
        if user_input:
            api_key = user_input
        else:
            print("DB에서 API 키 조회 중...")
            result = get_api_key_from_db()
            if result:
                agent_id, api_key, agent_name = result
                print(f"  Agent: {agent_name} ({agent_id})")
                print(f"  API Key: {api_key}")
            else:
                print("DB에서 활성 Agent를 찾을 수 없습니다.")
                sys.exit(1)

    # 클라이언트 초기화
    client = SyncClient(
        api_key=api_key,
        base_url=args.base_url,
        agent_id=agent_id,
    )

    print(f"\n{'=' * 50}")
    print(f"  Agent SDK 대화형 데모")
    print(f"  서버: {args.base_url}")
    print(f"  Agent: {agent_name}")
    print(f"  AI 대화: {'활성' if os.getenv('ENABLE_AI_CHAT', 'false').lower() == 'true' else '비활성'}")
    print(f"{'=' * 50}")
    print_help()

    try:
        while True:
            try:
                user_input = input(f"\n[{agent_name}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n종료합니다.")
                break

            if not user_input:
                continue

            # 명령어 처리
            if user_input == "/exit":
                print("종료합니다.")
                break

            elif user_input == "/help":
                print_help()

            elif user_input == "/clear":
                os.system("clear" if os.name != "nt" else "cls")

            elif user_input == "/health":
                try:
                    health = client.health_check()
                    print(f"  {json.dumps(health, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"  오류: {e}")

            elif user_input.startswith("/memory"):
                parts = user_input.split(maxsplit=1)
                content = parts[1] if len(parts) > 1 else input("  메모리 내용: ").strip()
                if content:
                    try:
                        result = client.send_memory(
                            content=content,
                            metadata={"source": "interactive_demo"},
                        )
                        print(f"  저장 완료: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    except Exception as e:
                        print(f"  오류: {e}")

            elif user_input.startswith("/message"):
                parts = user_input.split(maxsplit=1)
                content = parts[1] if len(parts) > 1 else input("  메시지 내용: ").strip()
                if content:
                    try:
                        result = client.send_message(
                            content=content,
                            metadata={"source": "interactive_demo"},
                        )
                        print(f"  전송 완료: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    except Exception as e:
                        print(f"  오류: {e}")

            elif user_input.startswith("/log"):
                parts = user_input.split(maxsplit=1)
                content = parts[1] if len(parts) > 1 else input("  로그 내용: ").strip()
                if content:
                    try:
                        result = client.send_log(
                            content=content,
                            metadata={"source": "interactive_demo"},
                        )
                        print(f"  전송 완료: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    except Exception as e:
                        print(f"  오류: {e}")

            elif user_input == "/data":
                try:
                    data = client.get_agent_data(limit=10)
                    items = data.get("data", data.get("items", []))
                    print(f"  총 {len(items)}개 데이터:")
                    for item in items:
                        dtype = item.get("data_type", "?")
                        content = item.get("content", "")[:80]
                        print(f"    [{dtype}] {content}")
                except Exception as e:
                    print(f"  오류: {e}")

            elif user_input == "/sources":
                try:
                    sources = client.get_memory_sources()
                    print(f"  {json.dumps(sources, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"  오류: {e}")

            elif user_input.startswith("/search"):
                parts = user_input.split(maxsplit=1)
                query = parts[1] if len(parts) > 1 else input("  검색어: ").strip()
                if query:
                    try:
                        result = client.search_memories(query=query, limit=5)
                        results = result.get("results", [])
                        print(f"  {len(results)}개 결과:")
                        for r in results:
                            score = r.get("score", 0)
                            content = r.get("content", "")[:80]
                            print(f"    [{score:.3f}] {content}")
                    except Exception as e:
                        print(f"  오류: {e}")

            elif user_input == "/agent":
                print(f"  Agent Name: {agent_name}")
                print(f"  Agent ID: {agent_id}")
                print(f"  API Key: {api_key[:20]}...")
                print(f"  서버: {args.base_url}")

            else:
                # AI 대화 모드
                ai_chat(user_input, client=client, agent_name=agent_name)

    finally:
        client.close()


if __name__ == "__main__":
    main()
