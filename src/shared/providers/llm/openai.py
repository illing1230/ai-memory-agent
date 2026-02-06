"""OpenAI LLM Provider (OpenAI 호환 API 포함 - Qwen3 등)"""

import json
import re
from typing import Any, AsyncGenerator

import httpx

from src.shared.providers.base import BaseLLMProvider
from src.shared.exceptions import ProviderException


MEMORY_EXTRACTION_PROMPT = """다음 대화에서 장기적으로 기억할 가치가 있는 정보를 추출하세요.

중요 규칙:
- 대화에 명시적으로 언급된 정보만 추출하세요.
- 대화에 없는 내용을 추론하거나 가정하지 마세요.
- 불확실한 정보는 추출하지 마세요.

추출 기준:
- 사용자의 선호도, 습관, 특성
- 중요한 사실이나 결정 사항
- 프로젝트/업무 관련 정보
- 관계 정보 (사람, 조직 등)

응답 형식 (반드시 유효한 JSON 배열만 출력):
[
  {
    "content": "추출된 메모리 내용",
    "category": "preference|fact|decision|relationship",
    "importance": "high|medium|low"
  }
]

예시:
[
  {
    "content": "김과장은 오전 회의를 선호한다",
    "category": "preference",
    "importance": "medium"
  },
  {
    "content": "프로젝트 마감일은 3월 15일이다",
    "category": "fact",
    "importance": "high"
  }
]

중요:
- 추출할 메모리가 없으면 빈 배열 []만 반환하세요.
- JSON 배열 외에 다른 텍스트, 설명, 주석은 절대 포함하지 마세요.
- 코드 블록(```json) 없이 JSON 배열만 직접 출력하세요.

대화:
{conversation}"""


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI 호환 LLM Provider (Qwen3-32B 등 지원)"""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """텍스트 생성"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if self.api_key.startswith("Bearer "):
                headers["Authorization"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            # 내부망 직접 접속: 프록시 완전 비활성화
            # trust_env=False로 환경변수 프록시 설정 무시
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=30.0),  # 5분으로 증가
                verify=False,
                trust_env=False,  # 환경변수 HTTP_PROXY/HTTPS_PROXY 무시
            ) as client:
                print(f"[LLM] 요청 URL: {self.base_url}/chat/completions")
                print(f"[LLM] 모델: {self.model}")
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                
                print(f"[LLM] 응답 상태: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"[LLM] 에러 응답: {error_text[:500]}")
                    raise ProviderException("OpenAI LLM", f"HTTP {response.status_code}: {error_text[:200]}")
                
                data = response.json()
                
                print(f"[LLM] 응답 데이터 구조: {list(data.keys())}")
                
                if "choices" not in data or len(data["choices"]) == 0:
                    print(f"[LLM] 잘못된 응답 형식: {data}")
                    raise ProviderException("OpenAI LLM", f"잘못된 응답 형식: choices 없음")
                
                choice = data["choices"][0]
                print(f"[LLM] choice 구조: {list(choice.keys())}")
                
                if "message" not in choice:
                    print(f"[LLM] choice에 message가 없음: {choice}")
                    raise ProviderException("OpenAI LLM", f"잘못된 응답 형식: message 없음")
                
                message = choice["message"]
                print(f"[LLM] message 구조: {list(message.keys())}")
                
                content = message.get("content")
                
                # content가 None이거나 빈 문자열인 경우 처리
                if content is None:
                    print(f"[LLM] 응답 content가 None입니다. 전체 message: {message}")
                    # gpt-oss-120b 모델은 reasoning_content 필드를 사용
                    content = message.get("reasoning_content", "")
                    if content:
                        print(f"[LLM] reasoning_content에서 응답을 찾았습니다")
                    else:
                        # 빈 문자열로 처리하여 계속 진행
                        content = ""
                
                if not isinstance(content, str):
                    print(f"[LLM] 응답 content가 문자열이 아님: {type(content)}, 값: {content}")
                    content = str(content) if content else ""
                
                # <think> 태그 제거 (Qwen3 등)
                content = re.sub(r"<think>[\s\S]*?</think>", "", content)
                content = content.strip()
                
                print(f"[LLM] 응답 길이: {len(content)}자")
                return content

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 오류: {e.response.status_code}"
            try:
                error_body = e.response.text
                print(f"[LLM] HTTPStatusError: {error_msg}, Body: {error_body[:500]}")
                error_msg += f" - {error_body[:200]}"
            except Exception:
                pass
            raise ProviderException("OpenAI LLM", error_msg)
        except httpx.ConnectError as e:
            print(f"[LLM] 연결 오류: {e}")
            raise ProviderException("OpenAI LLM", f"연결 실패: {self.base_url} - {e}")
        except httpx.TimeoutException as e:
            print(f"[LLM] 타임아웃: {e}")
            raise ProviderException("OpenAI LLM", f"타임아웃 (120초): {self.base_url}")
        except ProviderException:
            raise
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[LLM] 예상치 못한 오류: {type(e).__name__}: {e}")
            print(f"[LLM] Traceback: {error_detail}")
            raise ProviderException("OpenAI LLM", f"{type(e).__name__}: {e}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """텍스트 스트리밍 생성"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if self.api_key.startswith("Bearer "):
                headers["Authorization"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,  # 스트리밍 활성화
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(300.0, connect=30.0),  # 5분으로 증가
                verify=False,
                trust_env=False,
            ) as client:
                print(f"[LLM 스트리밍] 요청 URL: {self.base_url}/chat/completions")
                print(f"[LLM 스트리밍] 모델: {self.model}")
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"[LLM 스트리밍] 에러 응답: {error_text[:500]}")
                        raise ProviderException("OpenAI LLM", f"HTTP {response.status_code}: {error_text[:200]}")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # "data: " 제거
                            
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        # </think> 태그 제거
                                        content = re.sub(r"</think>[\s\S]*?</think>", "", content)
                                        yield content
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 오류: {e.response.status_code}"
            raise ProviderException("OpenAI LLM", error_msg)
        except httpx.ConnectError as e:
            error_msg = f"연결 오류: {e}"
            raise ProviderException("OpenAI LLM", f"연결 실패: {self.base_url} - {e}")
        except httpx.TimeoutException as e:
            error_msg = f"타임아웃: {e}"
            raise ProviderException("OpenAI LLM", f"타임아웃 (120초): {self.base_url}")
        except ProviderException:
            raise
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[LLM 스트리밍] 예상치 못한 오류: {type(e).__name__}: {e}")
            print(f"[LLM 스트리밍] Traceback: {error_detail}")
            raise ProviderException("OpenAI LLM", f"{type(e).__name__}: {e}")

    async def extract_memories(
        self,
        conversation: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출"""
        # 대화 포맷팅
        conv_text = "\n".join(
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation
        )

        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conv_text)

        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt="당신은 대화에서 중요한 정보를 추출하는 AI입니다. 반드시 유효한 JSON 배열만 응답하세요. 다른 텍스트는 포함하지 마세요.",
                temperature=0.1,
                max_tokens=2000,
            )
        except Exception as e:
            # LLM 호출 실패 시 빈 리스트 반환
            print(f"메모리 추출 LLM 호출 실패: {e}")
            return []

        # JSON 파싱
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> list[dict[str, Any]]:
        """LLM 응답에서 JSON 파싱 (강화된 에러 핸들링)"""
        if not response:
            print(f"[JSON 파싱] 빈 응답")
            return []
        
        response = response.strip()
        print(f"[JSON 파싱] 원본 응답 (길이: {len(response)}): {response[:300]}...")
        
        # 코드 블록 제거
        if "```" in response:
            # ```json ... ``` 또는 ``` ... ``` 형식 처리
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
            if match:
                response = match.group(1).strip()
                print(f"[JSON 파싱] 코드 블록 제거 후: {response[:200]}...")
        
        # JSON 배열 찾기
        # [ 로 시작하고 ] 로 끝나는 부분 추출
        match = re.search(r"\[[\s\S]*\]", response)
        if match:
            response = match.group(0)
            print(f"[JSON 파싱] JSON 배열 추출: {response[:200]}...")
        else:
            print(f"[JSON 파싱] JSON 배열 패턴을 찾을 수 없음")
            return []
        
        try:
            memories = json.loads(response)
            if isinstance(memories, list):
                # 유효한 메모리만 필터링
                valid_memories = []
                for mem in memories:
                    if isinstance(mem, dict) and mem.get("content"):
                        valid_memories.append({
                            "content": str(mem.get("content", "")),
                            "category": str(mem.get("category", "fact")),
                            "importance": str(mem.get("importance", "medium")),
                        })
                print(f"[JSON 파싱] 성공: {len(valid_memories)}개의 메모리 추출")
                return valid_memories
            print(f"[JSON 파싱] 응답이 리스트가 아님: {type(memories)}")
            return []
        except json.JSONDecodeError as e:
            print(f"[JSON 파싱] JSON 파싱 실패: {e}")
            print(f"[JSON 파싱] 파싱 실패한 응답: {response}")
            return []
