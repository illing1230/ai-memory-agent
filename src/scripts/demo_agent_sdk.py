"""Agent SDK 데모 스크립트

서버가 실행 중인 상태에서 SDK를 통해 Agent 기능을 시연합니다.
seed_demo가 먼저 실행되어 있어야 합니다.

Usage:
    # 서버 실행 중인 상태에서
    python -m src.scripts.demo_agent_sdk

    # API 키를 직접 지정하는 경우
    python -m src.scripts.demo_agent_sdk --api-key sk_xxxxx

    # 서버 주소 변경
    python -m src.scripts.demo_agent_sdk --base-url http://localhost:8000
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path


def get_api_key_from_db() -> tuple[str, str] | None:
    """DB에서 '품질 모니터링 봇'의 API 키와 ID를 조회"""
    db_path = Path("data/sqlite/memory.db")
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT id, api_key FROM agent_instances WHERE name = ? AND status = 'active' LIMIT 1",
            ("품질 모니터링 봇",),
        )
        row = cursor.fetchone()
        if row:
            return row[0], row[1]
        return None
    finally:
        conn.close()


def print_section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(label: str, data):
    print(f"\n  [{label}]")
    if isinstance(data, dict):
        print(f"  {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"  {data}")


def main():
    parser = argparse.ArgumentParser(description="Agent SDK 데모")
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

    # API 키 조회
    api_key = args.api_key
    agent_id = ""

    if not api_key:
        print("DB에서 API 키 조회 중...")
        result = get_api_key_from_db()
        if result:
            agent_id, api_key = result
            print(f"  Agent ID: {agent_id}")
            print(f"  API Key: {api_key}")
        else:
            print("DB에서 API 키를 찾을 수 없습니다.")
            print("seed_demo를 먼저 실행하거나 --api-key 옵션을 사용하세요.")
            sys.exit(1)

    print_section("Agent SDK 데모 시작")
    print(f"  서버: {args.base_url}")
    print(f"  Agent ID: {agent_id}")
    print(f"  API Key: {api_key[:20]}...")

    # 클라이언트 초기화
    client = SyncClient(
        api_key=api_key,
        base_url=args.base_url,
        agent_id=agent_id,
    )

    try:
        # ---- 1. 헬스 체크 ----
        print_section("1. 서버 헬스 체크")
        try:
            health = client.health_check()
            print_result("응답", health)
            print("  -> 서버 정상 동작 확인")
        except Exception as e:
            print(f"  서버 연결 실패: {e}")
            print(f"  서버가 실행 중인지 확인하세요: {args.base_url}")
            sys.exit(1)

        # ---- 2. 메모리 저장 ----
        print_section("2. 메모리 저장 (send_memory)")

        memory1 = client.send_memory(
            content="A라인 실시간 불량률 3.1%, 전일 대비 0.8% 상승",
            metadata={"source": "quality_system", "line": "A", "timestamp": "2026-02-23T10:00:00+09:00"},
        )
        print_result("메모리 1", memory1)

        time.sleep(0.5)

        memory2 = client.send_memory(
            content="B라인 CPK 지수 1.42 (기준: 1.33 이상)",
            metadata={"source": "quality_system", "line": "B", "timestamp": "2026-02-23T10:05:00+09:00"},
        )
        print_result("메모리 2", memory2)
        print("  -> 2개 메모리 저장 완료")

        # ---- 3. 메모리 검색 ----
        print_section("3. 메모리 검색 (search_memories)")

        time.sleep(1)  # 벡터 인덱싱 대기

        search_result = client.search_memories(
            query="불량률",
            limit=5,
        )
        print_result("검색 결과 (불량률)", search_result)

        memories = search_result.get("memories", search_result.get("results", []))
        if memories:
            print(f"  -> {len(memories)}개 메모리 검색됨")
        else:
            print("  -> 검색 결과 없음 (벡터 인덱싱 지연 가능)")

        # ---- 4. 메시지 전송 ----
        print_section("4. 메시지 전송 (send_message)")

        message = client.send_message(
            content="[품질 모니터링 봇] A라인 불량률 경고: 3.1% (기준 초과). 즉시 점검 바랍니다.",
            metadata={"alert_level": "warning", "timestamp": "2026-02-23T10:10:00+09:00"},
        )
        print_result("메시지 전송", message)
        print("  -> 작업 로그 전송 완료")

        # ---- 5. 로그 전송 ----
        print_section("5. 로그 전송 (send_log)")

        log = client.send_log(
            content="품질 데이터 수집 작업 완료: A라인 120건, B라인 98건 처리",
            metadata={"job_id": "QC-2026-0223-001", "timestamp": "2026-02-23T10:15:00+09:00"},
        )
        print_result("로그 전송", log)
        print("  -> 로그 전송 완료")

        # ---- 6. 에이전트 데이터 조회 ----
        print_section("6. 에이전트 데이터 조회 (get_agent_data)")

        agent_data = client.get_agent_data(limit=10)
        print_result("저장된 데이터", agent_data)

        items = agent_data.get("data", agent_data.get("items", []))
        if items:
            print(f"  -> 총 {len(items)}개 데이터 조회됨")
            for item in items[:3]:
                content = item.get("content", "")
                dtype = item.get("data_type", "")
                print(f"     [{dtype}] {content[:60]}...")
        else:
            print("  -> 데이터 없음")

        # ---- 7. 메모리 소스 조회 ----
        print_section("7. 메모리 소스 조회 (get_memory_sources)")

        sources = client.get_memory_sources()
        print_result("접근 가능한 소스", sources)

        source_list = sources.get("sources", sources.get("chat_rooms", []))
        if source_list:
            print(f"  -> {len(source_list)}개 소스 접근 가능")
        else:
            print("  -> 소스 정보 없음")

        # ---- 완료 ----
        print_section("데모 완료!")
        print("  모든 SDK 기능이 정상 동작합니다.")
        print()
        print("  시연한 기능:")
        print("    1. health_check()     - 서버 상태 확인")
        print("    2. send_memory()      - 메모리 데이터 저장")
        print("    3. search_memories()  - 메모리 검색")
        print("    4. send_message()     - 메시지 전송")
        print("    5. send_log()         - 로그 전송")
        print("    6. get_agent_data()   - 저장된 데이터 조회")
        print("    7. get_memory_sources() - 접근 가능한 소스 조회")
        print()

    except Exception as e:
        print(f"\n  오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
