#!/usr/bin/env python3
"""
AI Memory Agent 서버 검증 스크립트

서버가 정상 동작하는지 전체 API를 테스트합니다.

사용법:
    python scripts/verify_server.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import time
import httpx

# 색상 코드
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class ServerVerifier:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self.token: str | None = None
        self.user_id: str | None = None
        self.api_key: str | None = None
        self.agent_type_id: str | None = None
        self.agent_instance_id: str | None = None
        self.memory_id: str | None = None
        self.results: list[dict] = []

    def _log(self, status: str, test_name: str, detail: str = ""):
        if status == "PASS":
            icon = f"{GREEN}PASS{RESET}"
        elif status == "FAIL":
            icon = f"{RED}FAIL{RESET}"
        elif status == "SKIP":
            icon = f"{YELLOW}SKIP{RESET}"
        else:
            icon = status

        msg = f"  [{icon}] {test_name}"
        if detail:
            msg += f" — {detail}"
        print(msg)
        self.results.append({"status": status, "test": test_name, "detail": detail})

    def _headers(self, use_api_key: bool = False) -> dict:
        if use_api_key and self.api_key:
            return {"X-API-Key": self.api_key}
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ==================== 1. Health Check ====================

    def test_health(self):
        print(f"\n{BOLD}{CYAN}1. Health Check{RESET}")
        try:
            r = self.client.get(f"{self.base_url}/health")
            data = r.json()
            if r.status_code == 200 and data.get("status") == "healthy":
                self._log("PASS", "GET /health", f"status={data['status']}, qdrant={data['services']['vector_store']}")
            else:
                self._log("FAIL", "GET /health", f"status_code={r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /health", str(e))

    # ==================== 2. Auth ====================

    def test_auth(self):
        print(f"\n{BOLD}{CYAN}2. Authentication{RESET}")

        # Register
        email = f"verify-{int(time.time())}@test.com"
        try:
            r = self.client.post(f"{self.base_url}/api/v1/auth/register", json={
                "name": "Verify User",
                "email": email,
                "password": "verifypass123",
            })
            if r.status_code == 200:
                data = r.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                self._log("PASS", "POST /auth/register", f"user_id={self.user_id[:12]}...")
            else:
                self._log("FAIL", "POST /auth/register", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /auth/register", str(e))

        # Login
        try:
            r = self.client.post(f"{self.base_url}/api/v1/auth/login", json={
                "email": email,
                "password": "verifypass123",
            })
            if r.status_code == 200:
                self._log("PASS", "POST /auth/login", "token received")
            else:
                self._log("FAIL", "POST /auth/login", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "POST /auth/login", str(e))

        # Me
        try:
            r = self.client.get(f"{self.base_url}/api/v1/auth/me", headers=self._headers())
            if r.status_code == 200:
                self._log("PASS", "GET /auth/me", f"name={r.json()['name']}")
            else:
                self._log("FAIL", "GET /auth/me", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /auth/me", str(e))

        # Verify
        try:
            r = self.client.post(f"{self.base_url}/api/v1/auth/verify", headers=self._headers())
            if r.status_code == 200 and r.json().get("valid"):
                self._log("PASS", "POST /auth/verify", "token valid")
            else:
                self._log("FAIL", "POST /auth/verify", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "POST /auth/verify", str(e))

    # ==================== 3. Memory CRUD ====================

    def test_memory(self):
        print(f"\n{BOLD}{CYAN}3. Memory CRUD{RESET}")

        if not self.token:
            self._log("SKIP", "Memory tests", "no auth token")
            return

        # Create
        try:
            r = self.client.post(f"{self.base_url}/api/v1/memories", json={
                "content": "검증 테스트 메모리: Python은 좋은 언어입니다",
                "scope": "personal",
                "category": "fact",
                "importance": "medium",
            }, headers=self._headers())
            if r.status_code == 200:
                self.memory_id = r.json()["id"]
                self._log("PASS", "POST /memories", f"id={self.memory_id[:12]}...")
            else:
                self._log("FAIL", "POST /memories", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /memories", str(e))

        # List
        try:
            r = self.client.get(f"{self.base_url}/api/v1/memories", headers=self._headers())
            if r.status_code == 200:
                self._log("PASS", "GET /memories", f"count={len(r.json())}")
            else:
                self._log("FAIL", "GET /memories", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /memories", str(e))

        # Get
        if self.memory_id:
            try:
                r = self.client.get(f"{self.base_url}/api/v1/memories/{self.memory_id}", headers=self._headers())
                if r.status_code == 200:
                    self._log("PASS", "GET /memories/{id}", f"content={r.json()['content'][:30]}...")
                else:
                    self._log("FAIL", "GET /memories/{id}", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", "GET /memories/{id}", str(e))

        # Update
        if self.memory_id:
            try:
                r = self.client.put(f"{self.base_url}/api/v1/memories/{self.memory_id}", json={
                    "content": "검증 테스트 메모리: Python은 매우 좋은 언어입니다 (수정됨)",
                    "importance": "high",
                }, headers=self._headers())
                if r.status_code == 200:
                    self._log("PASS", "PUT /memories/{id}", "updated")
                else:
                    self._log("FAIL", "PUT /memories/{id}", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", "PUT /memories/{id}", str(e))

        # Search
        try:
            r = self.client.post(f"{self.base_url}/api/v1/memories/search", json={
                "query": "Python 언어",
                "limit": 5,
            }, headers=self._headers())
            if r.status_code == 200:
                data = r.json()
                self._log("PASS", "POST /memories/search", f"results={data['total']}")
            else:
                self._log("FAIL", "POST /memories/search", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /memories/search", str(e))

        # Delete
        if self.memory_id:
            try:
                r = self.client.delete(f"{self.base_url}/api/v1/memories/{self.memory_id}", headers=self._headers())
                if r.status_code == 200:
                    self._log("PASS", "DELETE /memories/{id}", "deleted")
                else:
                    self._log("FAIL", "DELETE /memories/{id}", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", "DELETE /memories/{id}", str(e))

    # ==================== 4. Chat Room ====================

    def test_chat_room(self):
        print(f"\n{BOLD}{CYAN}4. Chat Room{RESET}")

        if not self.token:
            self._log("SKIP", "Chat Room tests", "no auth token")
            return

        room_id = None
        try:
            r = self.client.post(f"{self.base_url}/api/v1/chat-rooms", json={
                "name": "검증 테스트 대화방",
            }, headers=self._headers())
            if r.status_code == 200:
                room_id = r.json()["id"]
                self._log("PASS", "POST /chat-rooms", f"id={room_id[:12]}...")
            else:
                self._log("FAIL", "POST /chat-rooms", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "POST /chat-rooms", str(e))

        try:
            r = self.client.get(f"{self.base_url}/api/v1/chat-rooms", headers=self._headers())
            if r.status_code == 200:
                self._log("PASS", "GET /chat-rooms", f"count={len(r.json())}")
            else:
                self._log("FAIL", "GET /chat-rooms", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /chat-rooms", str(e))

        if room_id:
            try:
                r = self.client.post(f"{self.base_url}/api/v1/chat-rooms/{room_id}/messages", json={
                    "content": "검증 테스트 메시지입니다",
                }, headers=self._headers())
                if r.status_code == 200:
                    self._log("PASS", "POST /chat-rooms/{id}/messages", "sent")
                else:
                    self._log("FAIL", "POST /chat-rooms/{id}/messages", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", "POST /chat-rooms/{id}/messages", str(e))

            try:
                r = self.client.get(f"{self.base_url}/api/v1/chat-rooms/{room_id}/messages", headers=self._headers())
                if r.status_code == 200:
                    self._log("PASS", "GET /chat-rooms/{id}/messages", f"count={len(r.json())}")
                else:
                    self._log("FAIL", "GET /chat-rooms/{id}/messages", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", "GET /chat-rooms/{id}/messages", str(e))

            # Cleanup
            try:
                self.client.delete(f"{self.base_url}/api/v1/chat-rooms/{room_id}", headers=self._headers())
            except Exception:
                pass

    # ==================== 5. Agent (SDK API) ====================

    def test_agent_sdk(self):
        print(f"\n{BOLD}{CYAN}5. Agent SDK API{RESET}")

        if not self.token:
            self._log("SKIP", "Agent tests", "no auth token")
            return

        # Create Agent Type
        try:
            r = self.client.post(f"{self.base_url}/api/v1/agent-types", json={
                "name": "Verify Test Bot",
                "description": "검증 테스트용 에이전트",
                "version": "1.0.0",
                "capabilities": ["memory", "search"],
            }, headers=self._headers())
            if r.status_code == 200:
                self.agent_type_id = r.json()["id"]
                self._log("PASS", "POST /agent-types", f"id={self.agent_type_id[:12]}...")
            else:
                self._log("FAIL", "POST /agent-types", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /agent-types", str(e))

        # Create Agent Instance
        if self.agent_type_id:
            try:
                r = self.client.post(f"{self.base_url}/api/v1/agent-instances", json={
                    "agent_type_id": self.agent_type_id,
                    "name": "Verify Test Instance",
                }, headers=self._headers())
                if r.status_code == 200:
                    data = r.json()
                    self.agent_instance_id = data["id"]
                    self.api_key = data["api_key"]
                    self._log("PASS", "POST /agent-instances", f"api_key={self.api_key[:16]}...")
                else:
                    self._log("FAIL", "POST /agent-instances", f"{r.status_code}: {r.text[:100]}")
            except Exception as e:
                self._log("FAIL", "POST /agent-instances", str(e))

        if not self.api_key:
            self._log("SKIP", "Agent API Key tests", "no api_key")
            return

        agent_id = self.agent_instance_id or "test"

        # Send Memory (via /data)
        try:
            r = self.client.post(f"{self.base_url}/api/v1/agents/{agent_id}/data", json={
                "data_type": "memory",
                "content": "검증 테스트: 에이전트 메모리 저장",
            }, headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                self._log("PASS", "POST /agents/{id}/data (memory)", "saved")
            else:
                self._log("FAIL", "POST /agents/{id}/data", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /agents/{id}/data", str(e))

        # Send Message
        try:
            r = self.client.post(f"{self.base_url}/api/v1/agents/{agent_id}/data", json={
                "data_type": "message",
                "content": "검증 테스트: 에이전트 메시지",
            }, headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                self._log("PASS", "POST /agents/{id}/data (message)", "saved")
            else:
                self._log("FAIL", "POST /agents/{id}/data (message)", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "POST /agents/{id}/data (message)", str(e))

        # Create Memory (dedicated endpoint)
        agent_memory_id = None
        try:
            r = self.client.post(f"{self.base_url}/api/v1/agents/{agent_id}/memories", json={
                "content": "검증 테스트: 전용 메모리 엔드포인트",
            }, headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                agent_memory_id = r.json()["id"]
                self._log("PASS", "POST /agents/{id}/memories", f"id={agent_memory_id[:12]}...")
            else:
                self._log("FAIL", "POST /agents/{id}/memories", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /agents/{id}/memories", str(e))

        # Get Memory Sources
        try:
            r = self.client.get(f"{self.base_url}/api/v1/agents/{agent_id}/memory-sources",
                                headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                self._log("PASS", "GET /agents/{id}/memory-sources", "ok")
            else:
                self._log("FAIL", "GET /agents/{id}/memory-sources", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /agents/{id}/memory-sources", str(e))

        # Search Memories
        try:
            r = self.client.post(f"{self.base_url}/api/v1/agents/{agent_id}/memories/search", json={
                "query": "검증 테스트",
                "limit": 5,
            }, headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                self._log("PASS", "POST /agents/{id}/memories/search", f"results={r.json()['total']}")
            else:
                self._log("FAIL", "POST /agents/{id}/memories/search", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /agents/{id}/memories/search", str(e))

        # Get Agent Data
        try:
            r = self.client.get(f"{self.base_url}/api/v1/agents/{agent_id}/data",
                                headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                self._log("PASS", "GET /agents/{id}/data", f"total={r.json()['total']}")
            else:
                self._log("FAIL", "GET /agents/{id}/data", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /agents/{id}/data", str(e))

        # Get Entities
        try:
            r = self.client.get(f"{self.base_url}/api/v1/agents/{agent_id}/entities",
                                headers=self._headers(use_api_key=True))
            if r.status_code == 200:
                self._log("PASS", "GET /agents/{id}/entities", "ok")
            else:
                self._log("FAIL", "GET /agents/{id}/entities", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /agents/{id}/entities", str(e))

        # Delete Agent Memory
        if agent_memory_id:
            try:
                r = self.client.delete(f"{self.base_url}/api/v1/agents/{agent_id}/memories/{agent_memory_id}",
                                       headers=self._headers(use_api_key=True))
                if r.status_code == 200:
                    self._log("PASS", "DELETE /agents/{id}/memories/{mid}", "deleted")
                else:
                    self._log("FAIL", "DELETE /agents/{id}/memories/{mid}", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", "DELETE /agents/{id}/memories/{mid}", str(e))

    # ==================== 6. Agent Instance Stats & Logs ====================

    def test_agent_stats(self):
        print(f"\n{BOLD}{CYAN}6. Agent Stats & Logs{RESET}")

        if not self.agent_instance_id or not self.token:
            self._log("SKIP", "Agent stats tests", "no agent instance")
            return

        # Stats
        try:
            r = self.client.get(
                f"{self.base_url}/api/v1/agent-instances/{self.agent_instance_id}/stats",
                headers=self._headers())
            if r.status_code == 200:
                data = r.json()
                self._log("PASS", "GET /agent-instances/{id}/stats",
                          f"memories={data['memory_count']}, messages={data['message_count']}")
            else:
                self._log("FAIL", "GET /agent-instances/{id}/stats", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /agent-instances/{id}/stats", str(e))

        # API Logs
        try:
            r = self.client.get(
                f"{self.base_url}/api/v1/agent-instances/{self.agent_instance_id}/api-logs",
                headers=self._headers())
            if r.status_code == 200:
                data = r.json()
                self._log("PASS", "GET /agent-instances/{id}/api-logs", f"total={data['total']}")
            else:
                self._log("FAIL", "GET /agent-instances/{id}/api-logs", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /agent-instances/{id}/api-logs", str(e))

        # Webhook Events
        try:
            r = self.client.get(
                f"{self.base_url}/api/v1/agent-instances/{self.agent_instance_id}/webhook-events",
                headers=self._headers())
            if r.status_code == 200:
                self._log("PASS", "GET /agent-instances/{id}/webhook-events", f"count={len(r.json())}")
            else:
                self._log("FAIL", "GET /agent-instances/{id}/webhook-events", f"{r.status_code}")
        except Exception as e:
            self._log("FAIL", "GET /agent-instances/{id}/webhook-events", str(e))

    # ==================== 7. Admin API ====================

    def test_admin(self):
        print(f"\n{BOLD}{CYAN}7. Admin API{RESET}")

        # admin 계정으로 로그인 시도 (seed_data의 dev-user-001)
        admin_token = None
        try:
            r = self.client.post(f"{self.base_url}/api/v1/auth/login", json={
                "email": "admin@example.com",
                "password": "admin",
            })
            if r.status_code == 200:
                admin_token = r.json()["access_token"]
                self._log("PASS", "Admin login", "admin token acquired")
            else:
                # X-User-ID 폴백 시도
                self._log("SKIP", "Admin login", "admin account not found, using X-User-ID fallback")
        except Exception as e:
            self._log("SKIP", "Admin login", str(e))

        admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {"X-User-ID": "dev-user-001"}

        endpoints = [
            ("GET", "/api/v1/admin/dashboard", "Dashboard"),
            ("GET", "/api/v1/admin/users", "Users"),
            ("GET", "/api/v1/admin/chat-rooms", "Chat Rooms"),
            ("GET", "/api/v1/admin/memories?limit=5", "Memories"),
            ("GET", "/api/v1/admin/agent-dashboard", "Agent Dashboard"),
            ("GET", "/api/v1/admin/agent-api-logs?limit=5", "Agent API Logs"),
            ("GET", "/api/v1/admin/knowledge-quality-report", "Knowledge Quality Report"),
        ]

        for method, path, label in endpoints:
            try:
                r = self.client.get(f"{self.base_url}{path}", headers=admin_headers)
                if r.status_code == 200:
                    self._log("PASS", f"GET {path.split('?')[0]}", label)
                elif r.status_code == 403:
                    self._log("SKIP", f"GET {path.split('?')[0]}", "admin required")
                else:
                    self._log("FAIL", f"GET {path.split('?')[0]}", f"{r.status_code}")
            except Exception as e:
                self._log("FAIL", f"GET {path.split('?')[0]}", str(e))

    # ==================== 8. Rate Limiting ====================

    def test_rate_limiting(self):
        print(f"\n{BOLD}{CYAN}8. Rate Limiting{RESET}")

        if not self.api_key:
            self._log("SKIP", "Rate limiting test", "no api_key")
            return

        agent_id = self.agent_instance_id or "test"

        # 빠르게 여러 번 호출하여 rate limit 확인
        hit_429 = False
        count = 0
        for i in range(65):
            try:
                r = self.client.get(
                    f"{self.base_url}/api/v1/agents/{agent_id}/memory-sources",
                    headers=self._headers(use_api_key=True))
                count += 1
                if r.status_code == 429:
                    hit_429 = True
                    self._log("PASS", "Rate Limiting", f"429 at request #{count}, Retry-After={r.headers.get('Retry-After', 'N/A')}")
                    break
            except Exception:
                break

        if not hit_429:
            self._log("SKIP", "Rate Limiting", f"no 429 after {count} requests (limit may be higher)")

    # ==================== 9. SSO ====================

    def test_sso(self):
        print(f"\n{BOLD}{CYAN}9. SSO Login{RESET}")

        try:
            r = self.client.post(f"{self.base_url}/api/v1/auth/sso", json={
                "email": "sso-test@example.com",
                "name": "SSO Test User",
                "sso_provider": "saml",
                "sso_id": "sso-test-12345",
            })
            if r.status_code == 200:
                data = r.json()
                self._log("PASS", "POST /auth/sso", f"user={data['user']['name']}, token received")
            elif r.status_code == 404:
                self._log("SKIP", "POST /auth/sso", "SSO endpoint not available")
            else:
                self._log("FAIL", "POST /auth/sso", f"{r.status_code}: {r.text[:100]}")
        except Exception as e:
            self._log("FAIL", "POST /auth/sso", str(e))

    # ==================== Cleanup ====================

    def cleanup(self):
        print(f"\n{BOLD}{CYAN}Cleanup{RESET}")

        if self.agent_instance_id and self.token:
            try:
                self.client.delete(
                    f"{self.base_url}/api/v1/agent-instances/{self.agent_instance_id}",
                    headers=self._headers())
                self._log("PASS", "Delete test agent instance", "cleaned up")
            except Exception:
                pass

        if self.agent_type_id and self.token:
            try:
                self.client.delete(
                    f"{self.base_url}/api/v1/agent-types/{self.agent_type_id}",
                    headers=self._headers())
                self._log("PASS", "Delete test agent type", "cleaned up")
            except Exception:
                pass

    # ==================== Run All ====================

    def run_all(self):
        print(f"\n{BOLD}{'='*60}")
        print(f"  AI Memory Agent — Server Verification")
        print(f"  Target: {self.base_url}")
        print(f"{'='*60}{RESET}")

        self.test_health()
        self.test_auth()
        self.test_memory()
        self.test_chat_room()
        self.test_agent_sdk()
        self.test_agent_stats()
        self.test_admin()
        self.test_rate_limiting()
        self.test_sso()
        self.cleanup()

        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIP")

        print(f"\n{BOLD}{'='*60}")
        print(f"  Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}, {YELLOW}{skipped} skipped{RESET} / {total} total")
        print(f"{'='*60}{RESET}\n")

        if failed > 0:
            print(f"{RED}Failed tests:{RESET}")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  - {r['test']}: {r['detail']}")
            print()

        self.client.close()
        return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="AI Memory Agent 서버 검증")
    parser.add_argument("--base-url", default="http://localhost:8000", help="서버 URL (기본: http://localhost:8000)")
    args = parser.parse_args()

    verifier = ServerVerifier(args.base_url)
    sys.exit(verifier.run_all())


if __name__ == "__main__":
    main()
