#!/usr/bin/env python3
"""
외부 LLM + AI Memory Agent SDK 테스트 챗봇
Agent 클래스 하나로 LLM 호출, 메시지 저장, 메모리 검색/추출을 모두 처리
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from ai_memory_agent_sdk import Agent
except ImportError:
    print("AI Memory Agent SDK가 설치되지 않았습니다.")
    print("설치: pip install -e ai_memory_agent_sdk")
    sys.exit(1)


def setup_context_sources(agent: Agent) -> None:
    """대화형 메모리 소스 설정"""
    try:
        sources = agent.sources()
    except Exception as e:
        print(f"  소스 조회 실패: {e}")
        return

    ctx: dict = {
        "include_personal": False,
        "include_agent": False,
        "include_document": False,
        "chat_rooms": [],
    }

    # Agent 메모리
    if "agent" in sources:
        print(f"  Agent 메모리: {sources['agent']['name']}")
        ans = input("  Agent 메모리 포함? (y/N): ").strip().lower()
        if ans == "y":
            ctx["include_agent"] = True

    # 문서 메모리
    if "document" in sources:
        print(f"  문서 메모리: {sources['document']['name']}")
        ans = input("  문서 메모리 포함? (y/N): ").strip().lower()
        if ans == "y":
            ctx["include_document"] = True

    # 개인 메모리
    ans = input("  개인 메모리 포함? (y/N): ").strip().lower()
    if ans == "y":
        ctx["include_personal"] = True

    # 채팅방
    if sources["chat_rooms"]:
        print(f"  채팅방 ({len(sources['chat_rooms'])}개):")
        for i, r in enumerate(sources["chat_rooms"]):
            print(f"    {i + 1}. {r['name']}")
        sel = input("  포함할 번호 (콤마 구분, 없으면 Enter): ").strip()
        if sel:
            for s in sel.split(","):
                idx = int(s.strip()) - 1
                if 0 <= idx < len(sources["chat_rooms"]):
                    ctx["chat_rooms"].append(sources["chat_rooms"][idx]["id"])

    agent.context_sources = ctx
    active = []
    if ctx["include_agent"]:
        active.append("Agent")
    if ctx["include_document"]:
        active.append("문서")
    if ctx["include_personal"]:
        active.append("개인")
    if ctx["chat_rooms"]:
        active.append(f"채팅방({len(ctx['chat_rooms'])})")
    print(f"  설정 완료: {', '.join(active) or '없음'}\n")


def main():
    api_key = os.getenv("AI_MEMORY_AGENT_API_KEY")
    if not api_key:
        print("AI_MEMORY_AGENT_API_KEY 환경 변수를 설정해주세요.")
        sys.exit(1)

    agent = Agent(
        api_key=api_key,
        base_url=os.getenv("AI_MEMORY_AGENT_URL", "http://localhost:8000"),
        agent_id=os.getenv("AGENT_ID", "My Bot"),
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_url=os.getenv("LLM_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL"),
    )

    print("=" * 60)
    print("External LLM Chatbot + AI Memory Agent")
    print("=" * 60)
    print("\n명령어: /exit /clear /memory /sources /search /data /setup /help\n")

    if agent.health():
        print("서버 연결 성공\n")
    else:
        print("서버 연결 실패 - 메모리 저장 없이 계속합니다.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd == "/exit":
                print("\n종료합니다.")
                break
            elif cmd == "/clear":
                agent.clear()
                print("대화 초기화 완료.\n")
            elif cmd == "/memory":
                mem = agent.memory()
                if mem:
                    print(f"\n추출된 메모리:\n{mem}\n")
                else:
                    print("대화가 부족합니다.\n")
            elif cmd == "/sources":
                sources = agent.sources()
                print(f"\n=== 메모리 소스 ===")
                
                if "agent" in sources:
                    print(f"  Agent: {sources['agent']['name']}")
                
                if "document" in sources:
                    print(f"  문서: {sources['document']['name']}")
                
                print(f"\n  채팅방 ({len(sources['chat_rooms'])}개):")
                for r in sources["chat_rooms"]:
                    print(f"    - {r['name']}")
                print()
            elif cmd.startswith("/search "):
                query = user_input[8:].strip()
                if query:
                    result = agent.search(query)
                    print(f"\n검색 결과: {result['total']}건")
                    for r in result["results"]:
                        print(f"  [{r['score']:.3f}] ({r['scope']}) {r['content'][:80]}...")
                    print()
            elif cmd == "/search":
                print("  사용법: /search <검색어>\n")
            elif cmd == "/data":
                result = agent.data(limit=20)
                print(f"\n에이전트 데이터 ({result['total']}건 중 최근 20건)")
                for d in result["data"]:
                    print(f"  [{d['data_type']}] {d['content'][:60]}...")
                print()
            elif cmd == "/setup":
                setup_context_sources(agent)
            elif cmd == "/help":
                print("\n  /exit    - 종료")
                print("  /clear   - 대화 초기화")
                print("  /memory  - 대화에서 메모리 추출/저장")
                print("  /sources - 접근 가능한 메모리 소스 목록")
                print("  /search  - 메모리 검색 (/search <검색어>)")
                print("  /data    - 에이전트 저장 데이터 조회")
                print("  /setup   - 메모리 소스 설정 (대화 시 자동 검색)")
                print("  /help    - 도움말\n")
            else:
                response = agent.message(user_input)
                print(f"\nAssistant: {response}\n")

        except KeyboardInterrupt:
            print("\n\n종료합니다.")
            break
        except Exception as e:
            import traceback
            print(f"\n오류: {e}")
            print(f"상세 정보:\n{traceback.format_exc()}\n")


if __name__ == "__main__":
    main()
