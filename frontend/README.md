# AI Memory Agent — 사용 가이드

멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 AI 시스템의 종합 가이드입니다.

---

## 시작하기

### 회원가입
1. http://localhost:3000 접속
2. 로그인 화면에서 **회원가입** 클릭
3. 이름, 이메일, 비밀번호 입력 후 가입

### 로그인
- 이메일 + 비밀번호 입력
- 로그인 후 자동으로 대화방 목록 화면으로 이동
- 새로고침해도 로그인 상태 유지 (localStorage 기반)

### 첫 화면
- 왼쪽 사이드바: 대화방 목록, 메모리, 문서, 에이전트, 관리자(admin만)
- 메인 영역: 선택한 대화방의 채팅 화면

---

## 채팅

### 대화방
- **개인 대화방**: 기본 생성, 1인 사용
- **공유 대화방**: 멤버 초대로 그룹 채팅
- 대화방 생성: 사이드바 상단 `+` 버튼

### @ai 멘션
메시지에 `@ai`를 포함하면 AI가 자동으로 응답합니다.
AI는 대화 내용, RAG 문서, 메모리를 종합하여 답변합니다.

### 슬래시 커맨드 (7종)
| 커맨드 | 설명 |
|--------|------|
| `/remember <내용>` | 개인 + 대화방 메모리에 저장 |
| `/memory` | 최근 대화에서 중요 정보 자동 추출 (중복 자동 건너뜀) |
| `/search <검색어>` | 저장된 메모리 시맨틱 검색 |
| `/forget <검색어>` | 메모리 삭제 |
| `/members` | 현재 대화방 멤버 목록 확인 |
| `/invite <이메일>` | 멤버 초대 (대화방 관리자만) |
| `/help` | 도움말 표시 |

### 실시간 기능
- WebSocket 기반 메시지 실시간 전송/수신
- 타이핑 인디케이터
- 자동 재연결

---

## 메모리

### 자동 추출
`@ai`로 AI 응답을 받으면, 대화에서 중요한 정보가 자동으로 메모리로 추출됩니다.

### 수동 저장
- `/remember 김과장은 오전 회의를 선호한다` → 개인+대화방 메모리 동시 저장
- `/memory` → 최근 대화 20개에서 LLM이 자동 추출 (중복 벡터 유사도 0.85 기준으로 건너뜀)

### 시맨틱 검색
`/search` 또는 메모리 화면에서 의미 기반 검색. 벡터 유사도 + 최신성 가중치(60:40)로 리랭킹.

### 스코프
| 스코프 | 설명 | 접근 |
|--------|------|------|
| `personal` | 개인 메모리 | 본인만 |
| `chatroom` | 대화방 메모리 | 대화방 멤버 전체 |

### 컨텍스트 소스 설정
대화방 설정에서 AI가 참조할 메모리 소스를 선택할 수 있습니다:
- 현재 대화방 메모리
- 다른 대화방 메모리
- 개인 메모리

---

## RAG 문서

### 업로드
- 대화방 설정 또는 문서 화면에서 PDF/TXT 파일 업로드
- 업로드 시 자동으로 시맨틱 청킹 → 임베딩 → 벡터 DB 저장

### 시맨틱 청킹
의미 단위로 문서를 분할합니다. 문장 간 코사인 유사도를 계산하여 의미가 크게 변하는 지점에서 청크를 나눕니다.

### 문서 연결
- 문서를 하나 이상의 대화방에 연결 (다대다)
- 연결된 대화방에서 `@ai` 질문 시 해당 문서를 컨텍스트로 활용

### 하이브리드 검색
- **벡터 검색** (Qdrant): 의미적 유사성 기반
- **키워드 검색** (SQLite FTS5): 정확한 단어 매칭
- 두 결과를 결합하여 더 정확한 문서 청크 검색

### Reranker
Jina Reranker를 사용하여 검색 결과의 최종 순위를 정밀하게 재조정합니다.

---

## Agent 연동

### Marketplace
- 등록된 Agent Type 목록 조회
- Agent Type: 특정 용도의 AI 에이전트 정의 (시스템 프롬프트, 메모리 스코프 등)

### Instance
- Marketplace에서 Agent Type을 선택하여 Instance 생성
- Instance별 API Key 발급 → 외부에서 API 호출 가능

### API Key
- Instance별 고유 API Key 생성
- Python SDK(`ai_memory_agent_sdk`)로 외부 챗봇에서 메모리 저장/검색/응답 생성

---

## 관리자

관리자(`role: admin`) 전용 기능입니다.

### 시스템 대시보드
전체 사용자 수, 대화방 수, 메모리 수, 메시지 수, 부서/프로젝트 수 확인.

### 지식 대시보드
팀 지식의 상태를 한눈에 파악:
- **상단 요약**: 활성 메모리, 문서 수, 오래된 지식, 핫 토픽 수
- **메모리 분포**: scope별, category별, 중요도별 가로 바 차트
- **핫 토픽 TOP 15**: 자주 언급되는 엔티티 + 멘션 수 + 타입 뱃지
- **오래된 지식**: 30일/60일/90일 미접근 메모리 수 (녹/황/적)
- **기여도 랭킹**: 사용자별 메모리 생성 수 + 활용 수
- **문서 통계**: 타입별/상태별 분포, 전체 청크 수

### 관리 기능
- 사용자: 목록 조회, 역할 변경 (user/admin), 삭제
- 대화방: 목록 조회, 삭제
- 메모리: 페이지네이션 목록, 삭제
- 부서/프로젝트: 목록 조회

---

## 개발 가이드

### 기술 스택

| 영역 | 기술 |
|------|------|
| **Framework** | React 18 + TypeScript |
| **Build Tool** | Vite |
| **Styling** | Tailwind CSS |
| **상태 관리** | Zustand (persist middleware) |
| **서버 상태** | TanStack Query (React Query) |
| **라우팅** | React Router v6 |
| **실시간** | WebSocket (Native) |
| **아이콘** | Lucide React |
| **유틸리티** | clsx, tailwind-merge, date-fns |

### 폴더 구조

```
src/
├── App.tsx                 # 라우팅 및 인증 설정
├── main.tsx                # 엔트리포인트
├── index.css               # Tailwind CSS 설정
├── components/             # 공용 컴포넌트 (ui/, layout/, common/)
├── features/               # 기능별 모듈
│   ├── admin/              # 관리자 (대시보드, 지식 대시보드, CRUD)
│   ├── agent/              # Agent (Marketplace, Instance, Type)
│   ├── auth/               # 인증 (로그인, 스토어)
│   ├── chat/               # 채팅 (방, 메시지, 멤버, 설정)
│   ├── document/           # 문서 (업로드, 목록, 미리보기)
│   ├── memory/             # 메모리 (검색, 목록)
│   ├── project/            # 프로젝트 관리
│   └── share/              # 대화방 공유
├── hooks/                  # 전역 훅 (useWebSocket)
├── lib/                    # API 클라이언트 (api.ts), 유틸 (utils.ts)
├── stores/                 # Zustand 전역 스토어
└── types/                  # TypeScript 타입 정의
```

### API 클라이언트

```typescript
import { get, post, put, del } from '@/lib/api'

const rooms = await get<ChatRoom[]>('/chat-rooms')
const newRoom = await post<ChatRoom>('/chat-rooms', { name: 'Room' })
await put<ChatRoom>(`/chat-rooms/${id}`, { name: 'Updated' })
await del(`/chat-rooms/${id}`)
```

에러 처리:
```typescript
import { ApiError } from '@/lib/api'

try {
  await post('/memories', data)
} catch (error) {
  if (error instanceof ApiError) {
    console.log(error.status, error.message, error.data)
  }
}
```

### WebSocket

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const { isConnected, sendMessage, startTyping, stopTyping } = useWebSocket({
  roomId: 'room-123',
  token: 'your-token',
  onMessage: (data) => { /* 새 메시지 */ },
  onConnect: () => { /* 연결됨 */ },
})
```

### 환경 설정

**Vite 프록시** (`vite.config.ts`):
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true },
    '/ws': { target: 'ws://localhost:8000', ws: true },
  },
}
```

**Path Alias**: `@/` → `src/`

```bash
# 개발
npm run dev

# 빌드
npm run build

# 린트
npm run lint
```

---

## 라이선스

Internal Use Only - Samsung Electronics
