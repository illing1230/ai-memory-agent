# AI Memory Agent Frontend

멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템의 React 프론트엔드입니다.

## 🛠 기술 스택

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **상태 관리**: Zustand (persist middleware 포함)
- **서버 상태**: TanStack Query (React Query)
- **라우팅**: React Router v6
- **실시간 통신**: WebSocket (Native)
- **아이콘**: Lucide React
- **유틸리티**: clsx, tailwind-merge, date-fns

## 📁 폴더 구조

```
src/
├── App.tsx                 # 라우팅 및 인증 설정
├── main.tsx                # 엔트리포인트
├── index.css               # Tailwind CSS 설정
│
├── components/             # 공용 컴포넌트
│   ├── ui/                 # 기본 UI 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   └── ...
│   ├── layout/             # 레이아웃 컴포넌트
│   │   ├── MainLayout.tsx
│   │   └── Sidebar.tsx
│   └── common/             # 공통 컴포넌트
│       ├── Loading.tsx
│       └── EmptyState.tsx
│
├── features/               # 기능별 모듈 (Feature-based 구조)
│   ├── auth/               # 인증
│   │   ├── api/
│   │   │   └── authApi.ts
│   │   ├── components/
│   │   │   └── LoginForm.tsx
│   │   └── store/
│   │       └── authStore.ts
│   ├── chat/               # 채팅
│   │   ├── api/
│   │   │   └── chatApi.ts
│   │   ├── components/
│   │   │   ├── ChatRoom.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── MessageInput.tsx
│   │   └── hooks/
│   │       └── useChat.ts
│   ├── memory/             # 메모리
│   │   ├── api/
│   │   │   └── memoryApi.ts
│   │   └── components/
│   │       ├── MemorySearch.tsx
│   │       └── MemoryList.tsx
│   ├── project/            # 프로젝트
│   │   └── components/
│   │       └── ProjectManagement.tsx
│   └── workspace/          # 워크스페이스
│
├── hooks/                  # 전역 커스텀 훅
│   ├── index.ts
│   └── useWebSocket.ts     # WebSocket 연결 관리
│
├── lib/                    # 유틸리티
│   ├── api.ts              # API 클라이언트 (fetch 래퍼)
│   └── utils.ts            # 헬퍼 함수
│
├── stores/                 # 전역 상태 (Zustand)
│   └── ...
│
└── types/                  # TypeScript 타입 정의
    ├── index.ts
    └── common.types.ts
```

## 🚀 시작하기

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

### 3. 빌드

```bash
npm run build
```

### 4. 프로덕션 미리보기

```bash
npm run preview
```

## 🔐 인증

### 인증 플로우

1. 로그인 시 `access_token`과 `user` 정보를 받아 localStorage에 저장
2. 모든 API 요청에 자동으로 인증 헤더 추가:
   - `Authorization: Bearer <token>`
   - `X-User-ID: <user_id>`
3. Zustand persist로 새로고침 시에도 인증 상태 유지

### authStore 사용

```typescript
import { useAuthStore } from '@/features/auth/store/authStore'

// 상태 조회
const { user, isAuthenticated, token } = useAuthStore()

// 액션
const { login, logout, setUser } = useAuthStore()

// 로그인
login(user, token)

// 로그아웃
logout()
```

## 🌐 API 클라이언트

### 기본 사용

```typescript
import { get, post, put, del } from '@/lib/api'

// GET 요청
const rooms = await get<ChatRoom[]>('/chat-rooms')

// POST 요청
const newRoom = await post<ChatRoom>('/chat-rooms', { name: 'New Room' })

// PUT 요청
await put<ChatRoom>(`/chat-rooms/${id}`, { name: 'Updated' })

// DELETE 요청
await del(`/chat-rooms/${id}`)
```

### 에러 처리

```typescript
import { ApiError } from '@/lib/api'

try {
  await post('/memories', data)
} catch (error) {
  if (error instanceof ApiError) {
    console.log(error.status)  // HTTP 상태 코드
    console.log(error.message) // 에러 메시지
    console.log(error.data)    // 에러 상세 데이터
  }
}
```

## 🔄 WebSocket

### useWebSocket 훅

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const {
  isConnected,
  sendMessage,
  startTyping,
  stopTyping,
} = useWebSocket({
  roomId: 'room-123',
  token: 'your-token',
  onMessage: (data) => console.log('New message:', data),
  onConnect: () => console.log('Connected'),
  onDisconnect: () => console.log('Disconnected'),
})

// 메시지 전송
sendMessage('Hello!')

// 타이핑 상태
startTyping()
stopTyping()
```

### 메시지 타입

```typescript
// 수신 메시지 타입
type: "message:new"     // 새 메시지
type: "member:join"     // 멤버 입장
type: "member:leave"    // 멤버 퇴장
type: "memory:extracted" // 메모리 추출됨
type: "room:info"       // 대화방 정보
type: "typing:start"    // 타이핑 시작
type: "typing:stop"     // 타이핑 종료
type: "pong"            // 핑 응답
```

## 🎨 주요 기능

### 채팅
- 대화방 목록/생성/관리
- 실시간 메시지 전송 (WebSocket)
- `@ai` 멘션으로 AI 응답
- 타이핑 인디케이터
- 자동 재연결

### 메모리
- 시맨틱 검색
- Scope 필터링 (개인/대화방/프로젝트/부서)
- 메모리 생성/삭제

### UI/UX
- Notion 스타일 사이드바
- 반응형 디자인
- 로딩/에러 상태 표시
- React Query 캐싱

## ⚙️ 개발 환경 설정

### Vite 프록시

개발 시 Vite의 프록시 설정으로 백엔드 API와 연동됩니다:

```typescript
// vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    },
  },
}
```

### 환경 변수

```env
# .env.local (선택사항)
VITE_API_URL=http://localhost:8000/api/v1
```

### Path Alias

`@/` 경로 alias가 설정되어 있습니다:

```typescript
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/features/auth/store/authStore'
```

## 🧪 린트

```bash
npm run lint
```

## 📦 주요 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| react | ^18.3.1 | UI 라이브러리 |
| react-router-dom | ^6.28.0 | 라우팅 |
| @tanstack/react-query | ^5.60.0 | 서버 상태 관리 |
| zustand | ^5.0.1 | 클라이언트 상태 관리 |
| axios | ^1.7.7 | HTTP 클라이언트 |
| socket.io-client | ^4.8.1 | WebSocket (참조용) |
| tailwindcss | ^3.4.14 | 스타일링 |
| lucide-react | ^0.460.0 | 아이콘 |
| date-fns | ^4.1.0 | 날짜 포매팅 |

## 📄 라이선스

Internal Use Only - Samsung Electronics
