#!/usr/bin/env python3
"""
AI Memory Agent SDK 인터랙티브 데모

Phase 3 적응형 청킹을 포함한 전체 메모리 시스템을 데모하는 인터랙티브 스크립트.
입력 기반으로 실제 메모리 저장/검색/질문 기능을 테스트할 수 있다.

Usage:
    # 서버 실행 후
    python -m src.scripts.interactive_demo
    
    # API 키 직접 지정
    python -m src.scripts.interactive_demo --api-key sk_xxxxx
"""

import argparse
import json
import os
import sys
import time
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any


def get_api_key_from_db() -> Optional[tuple[str, str]]:
    """DB에서 활성 Agent Instance API 키 조회"""
    db_path = Path("data/memory.db")
    if not db_path.exists():
        return None
    
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT id, api_key, name FROM agent_instances WHERE status = 'active' LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return row[0], row[1], row[2]
        return None
    finally:
        conn.close()


def print_header():
    """헤더 출력"""
    print("=" * 70)
    print("🔥 AI Memory Agent SDK 인터랙티브 데모 (Phase 3)")
    print("=" * 70)
    print("  ✨ Phase 1: 지능형 청킹")
    print("  ✨ Phase 2: 계층적 메모리 (요약 + 청크)")  
    print("  ✨ Phase 3: 적응형 청킹 (코드/문서/대화/데이터별)")
    print("=" * 70)


def print_commands():
    """사용 가능한 명령어 출력"""
    print("\n🎯 사용 가능한 명령어:")
    print("  📝 /save <내용>     - 메모리 저장 (긴 내용은 적응형 청킹)")
    print("  🔍 /search <질문>   - 메모리 검색 (계층적 검색)")
    print("  📊 /memory          - 저장된 메모리 목록")
    print("  💬 /ask <질문>      - LLM + 메모리 활용 질문")
    print("  🧪 /test            - Phase 3 적응형 청킹 테스트")
    print("  📋 /sources         - 접근 가능한 메모리 소스")
    print("  🗑️  /clear          - 세션 초기화")
    print("  ❓ /help            - 도움말")
    print("  🚪 /exit            - 종료")
    print()


def print_phase3_demo():
    """Phase 3 적응형 청킹 데모 예시"""
    print("\n🌟 Phase 3 적응형 청킹 데모 예시:")
    print()
    print("1️⃣ 코드 저장:")
    print("   /save ```python")
    print("   def hello_world():")
    print("       print('Hello World')")
    print("   ```")
    print("   → 함수 단위로 보존 청킹")
    print()
    print("2️⃣ 긴 문서 저장:")  
    print("   /save # 프로젝트 개요")
    print("   이 프로젝트는...")
    print("   ## 상세 계획")
    print("   세부사항은...")
    print("   → 섹션 단위로 구조 보존")
    print()
    print("3️⃣ 대화 저장:")
    print("   /save 호영: 프로젝트 어때?")
    print("   데비: 잘 진행되고 있어!")
    print("   → 화자별 완전 보존")
    print()
    print("4️⃣ 테이블 데이터:")
    print("   /save | 이름 | 점수 |")
    print("   |------|------|")
    print("   | Alice | 95 |")
    print("   → 구조 완전 보존")
    print()


def test_adaptive_chunking(client):
    """적응형 청킹 테스트"""
    print("\n🧪 Phase 3 적응형 청킹 테스트 시작")
    print("-" * 50)
    
    # 1. 코드 테스트
    print("1️⃣ 코드 청킹 테스트...")
    code_content = '''```python
def fibonacci(n):
    """피보나치 수열 생성"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    """간단한 계산기"""
    def __init__(self):
        self.result = 0
        
    def add(self, x, y):
        """덧셈"""
        self.result = x + y
        return self.result
        
    def multiply(self, x, y):
        """곱셈"""  
        self.result = x * y
        return self.result

# 메인 실행
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(fibonacci(10))
```'''
    
    try:
        result = client.send_memory(
            content=code_content,
            metadata={"test_type": "code", "phase": 3}
        )
        print(f"   ✅ 코드 저장 완료: {result.get('id', 'N/A')[:8]}...")
    except Exception as e:
        print(f"   ❌ 코드 저장 실패: {e}")
    
    time.sleep(1)
    
    # 2. 문서 테스트
    print("2️⃣ 문서 청킹 테스트...")
    doc_content = '''# AI Memory Agent 프로젝트 개요

이 프로젝트는 긴 메시지와 복잡한 대화를 효과적으로 기억하고 검색할 수 있는 AI 메모리 시스템입니다.

## Phase 1: 지능형 청킹
- 단순 문자 수 제한을 넘어 의미 단위로 분할
- 문단, 문장 경계 고려
- 오버랩을 통한 컨텍스트 연결성 유지

## Phase 2: 계층적 메모리
- 긴 메시지를 요약본 + 상세 청크로 분리 저장
- 요약 우선 검색 → 연결된 청크 자동 확장
- 정보 완성도 95%+ 달성

## Phase 3: 적응형 청킹
- 내용 유형별 맞춤형 청킹 전략
- 코드: 함수/클래스 단위
- 문서: 섹션/헤더 단위  
- 대화: 화자/주제 변경 기준
- 데이터: 테이블/구조 보존 우선

## 성능 개선 효과
- 정보 손실: 70% → 0%
- 검색 정확도: 60% → 95%+
- 처리 속도: 50% 향상
- API 비용: 30% 절약'''

    try:
        result = client.send_memory(
            content=doc_content,
            metadata={"test_type": "document", "phase": 3}
        )
        print(f"   ✅ 문서 저장 완료: {result.get('id', 'N/A')[:8]}...")
    except Exception as e:
        print(f"   ❌ 문서 저장 실패: {e}")
    
    time.sleep(1)
    
    # 3. 검색 테스트
    print("3️⃣ 계층적 검색 테스트...")
    try:
        search_result = client.search_memories(
            query="fibonacci 함수 구현",
            limit=10
        )
        memories = search_result.get("memories", search_result.get("results", []))
        print(f"   ✅ 검색 완료: {len(memories)}건")
        
        for i, mem in enumerate(memories[:3]):
            content_preview = mem.get("content", "")[:60] + "..."
            score = mem.get("score", 0)
            print(f"      [{i+1}] (점수: {score:.3f}) {content_preview}")
            
    except Exception as e:
        print(f"   ❌ 검색 실패: {e}")
    
    print("🧪 적응형 청킹 테스트 완료!\n")


def main():
    parser = argparse.ArgumentParser(description="AI Memory Agent SDK 인터랙티브 데모")
    parser.add_argument("--api-key", help="Agent Instance API Key")
    parser.add_argument("--base-url", default="http://localhost:8000", help="서버 URL")
    parser.add_argument("--show-examples", action="store_true", help="시작 시 Phase 3 예시 표시")
    args = parser.parse_args()
    
    # SDK import
    try:
        from ai_memory_agent_sdk import SyncClient
    except ImportError:
        print("❌ ai_memory_agent_sdk 패키지가 설치되어 있지 않습니다.")
        print("   설치: pip install -e ai_memory_agent_sdk/")
        sys.exit(1)
    
    print_header()
    
    # API 키 조회
    api_key = args.api_key
    agent_id = ""
    agent_name = ""
    
    if not api_key:
        print("🔍 DB에서 API 키 조회 중...")
        result = get_api_key_from_db()
        if result:
            agent_id, api_key, agent_name = result
            print(f"   ✅ Agent: {agent_name}")
            print(f"   ✅ ID: {agent_id}")
        else:
            print("❌ DB에서 API 키를 찾을 수 없습니다.")
            print("   seed_demo를 먼저 실행하거나 --api-key 옵션을 사용하세요.")
            sys.exit(1)
    
    print(f"\n🌐 서버: {args.base_url}")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    # 클라이언트 초기화
    client = SyncClient(
        api_key=api_key,
        base_url=args.base_url,
        agent_id=agent_id
    )
    
    try:
        # 헬스 체크
        print("\n🏥 서버 연결 확인 중...")
        health = client.health_check()
        print("   ✅ 서버 정상 연결")
    except Exception as e:
        print(f"   ❌ 서버 연결 실패: {e}")
        print(f"   서버가 실행 중인지 확인하세요: {args.base_url}")
        sys.exit(1)
    
    print_commands()
    
    if args.show_examples:
        print_phase3_demo()
    
    print("💬 메시지를 입력하거나 명령어를 사용하세요. (/help 도움말)")
    
    while True:
        try:
            user_input = input("\n🔥 > ").strip()
            
            if not user_input:
                continue
            
            # 명령어 처리
            if user_input.startswith('/'):
                cmd_parts = user_input.split(' ', 1)
                cmd = cmd_parts[0].lower()
                args_text = cmd_parts[1] if len(cmd_parts) > 1 else ""
                
                if cmd == "/exit":
                    print("\n👋 데모를 종료합니다.")
                    break
                    
                elif cmd == "/help":
                    print_commands()
                    print_phase3_demo()
                    
                elif cmd == "/clear":
                    print("🗑️ 세션 초기화... (구현 예정)")
                    
                elif cmd == "/save":
                    if not args_text:
                        print("❌ 저장할 내용을 입력하세요. 예: /save 긴 프로젝트 설명...")
                        continue
                    
                    print(f"💾 메모리 저장 중... ({len(args_text)}자)")
                    try:
                        result = client.send_memory(
                            content=args_text,
                            metadata={
                                "source": "interactive_demo",
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "length": len(args_text)
                            }
                        )
                        memory_id = result.get("id", "N/A")
                        print(f"   ✅ 저장 완료: {memory_id[:8]}...")
                        
                        # 내용 유형 감지 결과 표시 (가능한 경우)
                        if len(args_text) > 1000:
                            print(f"   🌟 긴 내용 ({len(args_text)}자) → 적응형 청킹 적용")
                        
                    except Exception as e:
                        print(f"   ❌ 저장 실패: {e}")
                        
                elif cmd == "/search":
                    if not args_text:
                        print("❌ 검색할 내용을 입력하세요. 예: /search 프로젝트 현황")
                        continue
                    
                    print(f"🔍 메모리 검색 중: '{args_text}'")
                    try:
                        result = client.search_memories(
                            query=args_text,
                            limit=10
                        )
                        
                        memories = result.get("memories", result.get("results", []))
                        total = result.get("total", len(memories))
                        
                        print(f"   ✅ 검색 완료: {len(memories)}건 (총 {total}건)")
                        
                        if memories:
                            print("\n📋 검색 결과:")
                            for i, mem in enumerate(memories):
                                content = mem.get("content", "")
                                score = mem.get("score", 0)
                                mem_type = "요약" if content.startswith("[요약]") else "일반"
                                
                                preview = content[:80].replace('\n', ' ')
                                print(f"   {i+1}. [{mem_type}] (점수: {score:.3f})")
                                print(f"      {preview}...")
                                if i < len(memories) - 1:
                                    print()
                        else:
                            print("   📭 검색 결과가 없습니다.")
                        
                    except Exception as e:
                        print(f"   ❌ 검색 실패: {e}")
                        
                elif cmd == "/memory":
                    print("📊 저장된 메모리 조회 중...")
                    try:
                        result = client.get_agent_data(limit=20)
                        data = result.get("data", result.get("items", []))
                        total = result.get("total", len(data))
                        
                        print(f"   ✅ 메모리 목록: {len(data)}건 (총 {total}건)")
                        
                        if data:
                            print("\n📋 최근 메모리:")
                            for i, item in enumerate(data):
                                content = item.get("content", "")
                                data_type = item.get("data_type", "unknown")
                                created = item.get("created_at", "")
                                
                                preview = content[:60].replace('\n', ' ')
                                print(f"   {i+1}. [{data_type}] ({created[:10]})")
                                print(f"      {preview}...")
                                if i < len(data) - 1:
                                    print()
                        else:
                            print("   📭 저장된 메모리가 없습니다.")
                            
                    except Exception as e:
                        print(f"   ❌ 조회 실패: {e}")
                        
                elif cmd == "/sources":
                    print("📋 접근 가능한 메모리 소스 조회 중...")
                    try:
                        result = client.get_memory_sources()
                        sources = result.get("sources", result.get("chat_rooms", []))
                        
                        print(f"   ✅ 소스 목록: {len(sources)}개")
                        
                        if sources:
                            print("\n📁 메모리 소스:")
                            for i, source in enumerate(sources):
                                name = source.get("name", "Unknown")
                                source_type = source.get("type", "chatroom")
                                print(f"   {i+1}. [{source_type}] {name}")
                        else:
                            print("   📭 접근 가능한 소스가 없습니다.")
                            
                    except Exception as e:
                        print(f"   ❌ 조회 실패: {e}")
                        
                elif cmd == "/test":
                    test_adaptive_chunking(client)
                    
                elif cmd == "/ask":
                    if not args_text:
                        print("❌ 질문을 입력하세요. 예: /ask 프로젝트 진행 상황은?")
                        continue
                    
                    print(f"🤖 AI 질문 처리 중: '{args_text}'")
                    print("   (LLM 통합은 SDK 설정에 따라 다름)")
                    
                    # 우선 메모리 검색
                    try:
                        search_result = client.search_memories(query=args_text, limit=5)
                        memories = search_result.get("memories", search_result.get("results", []))
                        
                        if memories:
                            print(f"\n📚 관련 메모리 {len(memories)}건 발견:")
                            context = ""
                            for mem in memories:
                                content = mem.get("content", "")
                                context += content + "\n\n"
                                print(f"   - {content[:60]}...")
                            
                            print(f"\n💭 메모리 기반 답변:")
                            print(f"   질문 '{args_text}'에 대해 {len(memories)}개의 관련 메모리를 찾았습니다.")
                            print(f"   자세한 LLM 응답은 SDK의 LLM 설정이 필요합니다.")
                        else:
                            print("\n❓ 관련 메모리를 찾을 수 없습니다.")
                            print("   더 많은 정보를 저장한 후 다시 시도해보세요.")
                            
                    except Exception as e:
                        print(f"   ❌ 질문 처리 실패: {e}")
                        
                else:
                    print(f"❓ 알 수 없는 명령어: {cmd}")
                    print("   /help를 사용해서 사용 가능한 명령어를 확인하세요.")
            
            else:
                # 일반 메시지 (자동 저장)
                print(f"💬 메시지 자동 저장 중...")
                try:
                    result = client.send_memory(
                        content=user_input,
                        metadata={
                            "source": "user_message",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                    print(f"   ✅ 저장 완료")
                    
                    if len(user_input) > 500:
                        print(f"   🌟 긴 메시지 ({len(user_input)}자) → 적응형 청킹 적용")
                    
                except Exception as e:
                    print(f"   ❌ 저장 실패: {e}")
                
        except KeyboardInterrupt:
            print("\n\n👋 데모를 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            print(f"상세 정보:\n{traceback.format_exc()}")
    
    try:
        client.close()
    except:
        pass


if __name__ == "__main__":
    main()