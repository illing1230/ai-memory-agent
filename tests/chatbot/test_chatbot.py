#!/usr/bin/env python3
"""
간단한 LLM 질문 답변형 챗봇
AI Memory Agent SDK를 사용하여 대화 내용을 메모리로 전송
"""

import asyncio
import os
import sys
from typing import Optional

# 프로젝트 루트 경로 추가 (tests/chatbot/에서 실행할 때)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# AI Memory Agent SDK 임포트
try:
    from ai_memory_agent_sdk import AIMemoryAgentSyncClient, AuthenticationError, APIError, ConnectionError
except ImportError:
    print("AI Memory Agent SDK가 설치되지 않았습니다.")
    print("설치: pip install -e ai_memory_agent_sdk")
    sys.exit(1)

# LLM Provider 임포트
try:
    from src.shared.providers import get_llm_provider
except ImportError:
    print("LLM Provider를 임포트할 수 없습니다.")
    print("프로젝트 루트 디렉토리에서 실행해주세요.")
    sys.exit(1)


class SimpleChatbot:
    """간단한 LLM 챗봇"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        llm_provider: str = "openai",
        agent_id: str = "test",
    ):
        """
        챗봇 초기화
        
        Args:
            api_key: AI Memory Agent API Key
            base_url: AI Memory Agent 서버 URL
            llm_provider: LLM 제공자 (openai, anthropic, ollama)
            agent_id: Agent Instance ID
        """
        self.agent_client = AIMemoryAgentSyncClient(
            api_key=api_key,
            base_url=base_url,
            agent_id=agent_id,
        )
        
        # LLM Provider 설정
        os.environ["LLM_PROVIDER"] = llm_provider
        self.llm = get_llm_provider()
        
        self.conversation_history = []
    
    def send_to_memory(self, content: str, data_type: str = "memory"):
        """
        AI Memory Agent로 데이터 전송
        
        Args:
            content: 전송할 내용
            data_type: 데이터 타입 (memory, message, log)
        """
        try:
            result = self.agent_client.send_memory(
                content=content,
                metadata={
                    "source": "test_chatbot",
                    "data_type": data_type,
                }
            )
            print(f"✅ 메모리 전송 성공: {result['id']}")
        except AuthenticationError as e:
            print(f"❌ 인증 오류: {e}")
        except APIError as e:
            print(f"❌ API 오류: {e}")
        except ConnectionError as e:
            print(f"❌ 연결 오류: {e}")
        except Exception as e:
            print(f"❌ 알 수 없는 오류: {e}")
    
    async def chat(self, user_input: str) -> str:
        """
        사용자 입력에 대한 응답 생성
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            LLM 응답
        """
        # 대화 기록에 추가
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # 사용자 메시지를 메모리로 전송
        print(f"\n📤 사용자 메시지를 메모리로 전송 중...")
        self.send_to_memory(user_input, "message")
        
        # LLM 응답 생성
        print(f"\n🤖 LLM 응답 생성 중...")
        try:
            # 대화 기록을 프롬프트로 변환
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_history
            ])
            
            response = await self.llm.generate(
                prompt=conversation_text,
                temperature=0.7,
                max_tokens=500,
            )
            assistant_message = response
            
            # 어시스턴트 응답을 메모리로 전송
            print(f"\n📤 어시스턴트 응답을 메모리로 전송 중...")
            self.send_to_memory(assistant_message, "message")
            
            # 대화 기록에 추가
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except Exception as e:
            error_msg = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def extract_memory(self, conversation: str) -> str:
        """
        대화에서 중요한 메모리 추출
        
        Args:
            conversation: 대화 내용
            
        Returns:
            추출된 메모리
        """
        print(f"\n🧠 대화에서 메모리 추출 중...")
        
        prompt = f"""다음 대화에서 사용자의 중요한 정보, 선호도, 관심사 등을 추출하여 요약해주세요:

대화:
{conversation}

추출된 메모리:"""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300,
            )
            
            memory = response.strip()
            
            # 추출된 메모리를 전송
            print(f"\n📤 추출된 메모리를 전송 중...")
            self.send_to_memory(memory, "memory")
            
            return memory
        except Exception as e:
            print(f"❌ 메모리 추출 실패: {e}")
            return ""
    
    async def run(self):
        """챗봇 실행"""
        print("=" * 60)
        print("🤖 AI Memory Agent 테스트 챗봇")
        print("=" * 60)
        print("\n명령어:")
        print("  /exit  - 챗봇 종료")
        print("  /clear - 대화 기록 초기화")
        print("  /memory - 대화에서 메모리 추출")
        print("  /help  - 도움말")
        print("=" * 60)
        
        # 서버 헬스 체크
        print("\n🔍 AI Memory Agent 서버 연결 확인 중...")
        if self.agent_client.health_check():
            print("✅ 서버 연결 성공")
        else:
            print("❌ 서버 연결 실패")
            print("서버가 실행 중인지 확인해주세요.")
            return
        
        print("\n💬 대화를 시작합니다. 메시지를 입력하세요.\n")
        
        while True:
            try:
                # 사용자 입력
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # 명령어 처리
                if user_input.lower() == "/exit":
                    print("\n👋 챗봇을 종료합니다.")
                    break
                
                elif user_input.lower() == "/clear":
                    self.conversation_history = []
                    print("✅ 대화 기록이 초기화되었습니다.")
                    continue
                
                elif user_input.lower() == "/memory":
                    if len(self.conversation_history) >= 2:
                        conversation_text = "\n".join([
                            f"{msg['role']}: {msg['content']}"
                            for msg in self.conversation_history[-10:]  # 최근 10개 메시지
                        ])
                        memory = await self.extract_memory(conversation_text)
                        if memory:
                            print(f"\n📝 추출된 메모리:\n{memory}\n")
                    else:
                        print("❌ 메모리를 추출할 대화가 부족합니다.")
                    continue
                
                elif user_input.lower() == "/help":
                    print("\n명령어:")
                    print("  /exit  - 챗봇 종료")
                    print("  /clear - 대화 기록 초기화")
                    print("  /memory - 대화에서 메모리 추출")
                    print("  /help  - 도움말")
                    print()
                    continue
                
                # 일반 대화 처리
                response = await self.chat(user_input)
                print(f"\n🤖 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 챗봇을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}\n")


async def main():
    """메인 함수"""
    # 환경 변수에서 API Key 가져오기
    api_key = os.getenv("AI_MEMORY_AGENT_API_KEY","sk_49ab5d01bc934f818cde6e68a55d7bb7")
    
    if not api_key:
        print("❌ AI_MEMORY_AGENT_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("\n사용법:")
        print("  export AI_MEMORY_AGENT_API_KEY='your_api_key_here'")
        print("  python tests/chatbot/test_chatbot.py")
        print("\n또는:")
        print("  AI_MEMORY_AGENT_API_KEY='your_api_key_here' python tests/chatbot/test_chatbot.py")
        sys.exit(1)
    
    # LLM Provider 설정
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    # 챗봇 실행
    chatbot = SimpleChatbot(
        api_key=api_key,
        base_url="http://10.244.14.73:8000",
        llm_provider=llm_provider,
    )
    
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())
