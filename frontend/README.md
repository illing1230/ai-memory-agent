# AI Memory Agent Frontend

멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템의 React 프론트엔드입니다.

## 기술 스택

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **상태 관리**: Zustand
- **서버 상태**: TanStack Query (React Query)
- **라우팅**: React Router v6
- **아이콘**: Lucide React

## 시작하기

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

## 폴더 구조

```
src/
├── components/           # 공용 컴포넌트
│   ├── ui/              # 기본 UI 컴포넌트 (Button, Input 등)
│   ├── layout/          # 레이아웃 컴포넌트 (Sidebar, MainLayout)
│   └── common/          # 공통 컴포넌트 (Loading, EmptyState)
│
├── features/            # 기능별 모듈 (Feature-based 구조)
│   ├── auth/            # 인증
│   ├── chat/            # 채팅
│   ├── memory/          # 메모리
│   └── workspace/       # 워크스페이스
│
├── lib/                 # 유틸리티 (api, utils)
├── stores/              # 전역 상태 (Zustand)
└── types/               # 타입 정의
```

## 주요 기능

### 채팅
- 채팅방 목록/생성/관리
- 실시간 메시지 전송
- `@ai` 멘션으로 AI 응답
- Slash Command 지원 (`/remember`, `/search`, `/forget` 등)

### 메모리
- 시맨틱 검색
- Scope 필터링 (개인/채팅방/프로젝트/부서)
- 메모리 삭제

### UI/UX
- Notion 스타일 사이드바
- 다크 모드 지원
- 반응형 디자인
- 키보드 단축키

## 백엔드 연동

개발 시 Vite의 프록시 설정으로 백엔드 API(`localhost:8000`)와 연동됩니다.

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 라이선스

Internal Use Only - Samsung Electronics
