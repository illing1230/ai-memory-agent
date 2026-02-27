# AI Memory Agent 업데이트 내역
날짜: 2026-02-27

---

## 1. seed_demo.py 수정 및 Git 병합

### seed_demo.py 데이터 정리
- **목적**: 데모 데이터를 초기화하여 사용자가 직접 대화방, 메모리, MChat 매핑을 생성할 수 있도록 함

**변경 내용:**
- `CHAT_ROOMS = []` (빈 리스트)
- `CHAT_ROOM_MEMBERS = {}` (빈 딕셔너리)
- `MEMORIES = []` (모든 메모리 삭제 - 개인/프로젝트 대화방 메모리, 일정 메모리 포함)
- `ENTITY_RELATIONS = []` (메모리가 없으므로 관계도 삭제)
- `MCHAT_CHANNEL_MAPPINGS = []`
- `MCHAT_SUMMARY_LOGS = []`
- `SHARES = []`
- 데모 문서 업로드 로직 건너뜀 (대화방이 없으므로)

### 사용자 업데이트 (19명)
**삭제:**
- dev-user-001 (로컬 테스트용 계정)

**추가:**
- developer (developer@samsung.com, role: admin)

**기존 11명 사용자 이메일 변경:**
- 김품질 → hc.hyun@samsung.com
- 이검사 → kyoo1670@samsung.com
- 박관리 → sh1228.kim@samsung.com
- 최개발 → jegon.kim@samsung.com
- 정백엔드 → hajun2.kim@samsung.com
- 강프론트 → jw3544.bae@samsung.com
- 윤데이터 → jh7909.byon@samsung.com
- 한기획 → jaehoon.shim@samsung.com
- 서전략 → joongmin.ahn@samsung.com
- 임분석 → sdave.woo@samsung.com
- hy.joo → hy.joo@samsung.com

**추가 6명 사용자:**
- yk6522.woo@samsung.com
- heechae.yoon@samsung.com
- jungoh.lee@samsung.com
- jiho22.lee@samsung.com
- neoio.lee@samsung.com
- sbchang@samsung.com

### 프로젝트 수정
- MemGate → AI-Memory (프로젝트 이름 변경)

### PROJECT_MEMBERS 수정
- AI-Memory 프로젝트에서 dev-user-001 제거
- 기존 멤버: [0, 1, 5, 6, 7, 8] → 변경: [1, 5, 6, 7, 8]
- 모든 사용자 비밀번호: settings.test_user_password 사용 (.env의 test_user_password=1234qwer로 설정 가능)

### Git 작업
- feat/feature_update 브랜치 병합 (feat/feature_update → main)
- 병합 전략: feat/feature_update 브랜치 우선 (-X theirs 옵션 사용)
- 원격 저장소에 푸시 완료

**커밋:**
- "Update seed_demo.py: clean up demo data and update users"
- "Add department and project update/delete APIs"

---

## 2. 부서/프로젝트 수정/삭제 기능 구현 (백엔드)

### API 스키마 추가 (src/admin/schemas.py)
```python
class UpdateDepartmentRequest(BaseModel):
    name: str
    description: Optional[str] = None

class UpdateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None
```

### 서비스 메서드 추가 (src/admin/service.py)
```python
async def update_department(department_id, name, description)
async def delete_department(department_id)
    - 소속 사용자의 department_id를 NULL로 설정 후 삭제
    
async def update_project(project_id, name, description, department_id)
async def delete_project(project_id)
    - project_members 먼저 삭제 후 프로젝트 삭제
```

### API 라우터 추가 (src/admin/router.py)
- `PUT /api/admin/departments/{department_id}` - 부서 수정
- `DELETE /api/admin/departments/{department_id}` - 부서 삭제
- `PUT /api/admin/projects/{project_id}` - 프로젝트 수정
- `DELETE /api/admin/projects/{project_id}` - 프로젝트 삭제

---

## 3. 관리자 메뉴 간소화

### 사이드바 메뉴 수정 (frontend/src/components/layout/Sidebar.tsx)
**제거된 메뉴:**
- 지식 관리 (/admin/knowledge)
- 사용자 관리 (/admin/users)
- 부서 관리 (/admin/departments)
- 프로젝트 관리 (/admin/projects)

**유지 메뉴:**
- 대시보드 (/admin) - 관리자 페이지의 기본 탭

### 관리자 페이지 탭 구조 (frontend/src/features/admin/components/AdminPage.tsx)
**최종 탭:**
1. 대시보드 - 부서/프로젝트 관리 포함
2. 지식 대시보드 (KnowledgeDashboardTab) - 원복 완료
3. Agent (AgentDashboardTab) - 신규 추가
4. 대화방
5. 메모리
6. Mchat

---

## 4. 대시보드에 부서/프로젝트 관리 UI 추가

### DashboardTab.tsx 수정 (frontend/src/features/admin/components/DashboardTab.tsx)

**추가 기능:**
- 통계 카드: 사용자, 대화방, 메모리, 메시지, 부서, 프로젝트
- **부서 목록 섹션:**
  - 부서 이름, 설명, 멤버 수 표시
  - 편집 버튼 클릭 시 인라인 편집 모드
  - 이름, 설명 수정 가능
  - 삭제 기능 (확인 다이얼로그 포함)
  - 삭제 시 소속 사용자의 department_id를 NULL로 설정

- **프로젝트 목록 섹션:**
  - 프로젝트 이름, 설명, 부서, 멤버 수 표시
  - 편집 버튼 클릭 시 인라인 편집 모드
  - 이름, 설명, 부서 수정 가능 (부서 선택 드롭다운)
  - 삭제 기능 (확인 다이얼로그 포함)

**API 통합:**
- `useAdminDepartments()`, `useUpdateDepartment()`, `useDeleteDepartment()`
- `useAdminProjects()`, `useUpdateProject()`, `useDeleteProject()`

---

## 5. Agent 대시보드 탭 추가

### 백엔드 API 구조 확인
**실제 응답 구조** (AgentRepository.get_all_instances_stats()):
```python
{
    "total_instances": 총 인스턴스 수,
    "active_instances": 활성 인스턴스 수,
    "total_memories": 총 메모리 수,
    "total_messages": 총 메시지 수,
    "top_agents": [
        {
            "id": 인스턴스 ID,
            "name": 인스턴스 이름,
            "memory_count": 메모리 수,
            "last_active": 마지막 활동 시간
        }
    ],
    "daily_activity": [
        {
            "date": 날짜,
            "memory_count": 메모리 수,
            "message_count": 메시지 수
        }
    ]
}
```

### 프론트엔드 수정 사항

**타입 정의** (frontend/src/types/common.types.ts):
```typescript
export interface AgentDashboard {
  total_instances: number
  active_instances: number
  total_memories: number
  total_messages: number
  top_agents: Array<{
    id: string
    name: string
    memory_count: number
    last_active: string
  }>
  daily_activity: Array<{
    date: string
    memory_count: number
    message_count: number
  }>
}
```

**컴포넌트 수정** (AgentDashboardTab.tsx):
- 백엔드 API 응답 구조에 맞게 수정
- undefined 값 체크로 에러 수정
- 통계 카드: 전체 인스턴스, 전체 데이터, 활성 인스턴스, 메모리 수
- 인스턴스 목록: 이름, 메모리 수, 마지막 활동 시간 표시
- 확장 가능한 아코디언 UI
- API 로그 표시 (전체 및 인스턴스별)

**에러 수정:**
- 원래: `dashboard.avg_response_time.toFixed(2)` → undefined 에러
- 수정: 해당 필드 제거, 백엔드 응답에 없는 필드 제거

### API 추가 (frontend/src/features/admin/api/adminApi.ts)
```typescript
export async function getAgentDashboard(): Promise<AgentDashboard>
export async function getAdminAgentApiLogs(
  instanceId?: string,
  dateFrom?: string,
  dateTo?: string,
  limit = 50,
  offset = 0
): Promise<{ logs: AgentApiLog[]; total: number }>
```

### 훅 추가 (frontend/src/features/admin/hooks/useAdmin.ts)
```typescript
export function useAgentDashboard()
export function useAdminAgentApiLogs(instanceId?, dateFrom?, dateTo?, limit, offset)
```

---

## 6. Git 커밋 내역

```
c64f196 - Fix Agent dashboard: match API response structure and fix undefined errors
412ac41 - Add Agent dashboard tab to admin page
main 업데이트 전 (사이드바 메뉴 간소화)
65f57e1 - Update admin page: remove unused menus and add department/project edit UI in dashboard
```

---

## 7. 사용자 정보

### 로그인 계정
- **developer**: developer@samsung.com / 1234qwer
- **hy.joo**: hy.joo@samsung.com / 1234qwer
- **기타 사용자**: (이름)@samsung.com / 1234qwer

### 전체 사용자 목록 (19명)
1. developer (admin)
2. hy.joo (admin)
3. hc.hyun
4. kyoo1670
5. sh1228.kim
6. jegon.kim
7. hajun2.kim
8. jw3544.bae
9. jh7909.byon
10. jaehoon.shim
11. joongmin.ahn
12. sdave.woo
13. yk6522.woo
14. heechae.yoon
15. jungoh.lee
16. jiho22.lee
17. neoio.lee
18. sbchang

---

## 8. 부서 정보
1. 품질팀 - 제품 품질 관리 및 검사 담당
2. 개발팀 - 소프트웨어 개발 및 시스템 운영
3. 기획팀 - 제품 기획 및 전략 수립

---

## 9. 프로젝트 정보
1. PLM 시스템 - 제품 생명주기 관리 시스템
2. AI-Memory - AI 메모리 관리 플랫폼 (MemGate → 이름 변경)
3. RAG 시스템 - 검색 증강 생성 시스템
4. 품질 대시보드 - 품질 지표 시각화 대시보드
5. 신제품 기획 - 2026년 신제품 기획 프로젝트

---

## 10. 주요 변경 사항 요약

### 삭제된 기능/데이터
- 대화방, 메모리, 엔티티 관계, MChat 매핑, 공유 데이터
- dev-user-001 사용자
- 사이드바 메뉴: 지식 관리, 사용자 관리, 부서 관리, 프로젝트 관리

### 추가된 기능
- 부서/프로젝트 수정/삭제 API
- 대시보드 탭 내부에서의 부서/프로젝트 관리 UI
- Agent 대시보드 탭 (인스턴스 통계, API 로그)

### 변경된 기능
- 사용자 이메일 도메인 → @samsung.com
- 프로젝트 이름 → AI-Memory
- 지식 대시보드 탭 원복 (삭제되었던 탭 복원)

---

## 11. 기술 스택

**백엔드:**
- FastAPI
- SQLite
- Python

**프론트엔드:**
- React + TypeScript
- Vite
- Tailwind CSS
- Lucide React Icons
- TanStack Query (React Query)

---

## 12. 다음 단계

사용자가 직접 생성해야 하는 항목:
- 대화방 생성
- 메모리 생성
- MChat 채널 매핑 (사용자가 직접 설정 예정)
- 문서 업로드 (대화방 생성 후 가능)