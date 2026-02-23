"""데모용 시드 데이터 생성 스크립트

모든 주요 기능(대화방, 메모리, RAG 문서, Agent, Mchat)을 데모할 수 있는
완전한 시드 데이터를 생성합니다.

Usage:
    python -m src.scripts.seed_demo
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite

from src.config import get_settings
from src.shared.database import init_database, close_database, get_db_sync
from src.shared.vector_store import init_vector_store, close_vector_store, upsert_vector
from src.shared.providers import get_embedding_provider
from src.shared.auth import hash_password


# ==================== 데모 데이터 정의 ====================

KST = timezone(timedelta(hours=9))

DEPARTMENTS = [
    {"name": "품질팀", "description": "제품 품질 관리 및 검사 담당"},
    {"name": "개발팀", "description": "소프트웨어 개발 및 시스템 운영"},
    {"name": "기획팀", "description": "제품 기획 및 전략 수립"},
]

# 인덱스: 0=관리자, 1=김품질, 2=이검사, 3=박관리, 4=최개발, 5=정백엔드, 6=강프론트, 7=윤데이터, 8=한기획, 9=서전략, 10=임분석
USERS = [
    {"id": "dev-user-001", "name": "관리자", "email": "admin@test.com", "dept_idx": 1, "role": "admin"},
    {"name": "김품질", "email": "kim.quality@company.com", "dept_idx": 0},
    {"name": "이검사", "email": "lee.inspector@company.com", "dept_idx": 0},
    {"name": "박관리", "email": "park.manager@company.com", "dept_idx": 0},
    {"name": "최개발", "email": "choi.dev@company.com", "dept_idx": 1},
    {"name": "정백엔드", "email": "jung.backend@company.com", "dept_idx": 1},
    {"name": "강프론트", "email": "kang.frontend@company.com", "dept_idx": 1},
    {"name": "윤데이터", "email": "yoon.data@company.com", "dept_idx": 1},
    {"name": "한기획", "email": "han.planner@company.com", "dept_idx": 2},
    {"name": "서전략", "email": "seo.strategy@company.com", "dept_idx": 2},
    {"name": "임분석", "email": "lim.analyst@company.com", "dept_idx": 2},
]

PROJECTS = [
    {"name": "PLM 시스템", "description": "제품 생명주기 관리 시스템", "dept_idx": 0},
    {"name": "MemGate", "description": "AI 메모리 관리 플랫폼", "dept_idx": 1},
    {"name": "RAG 시스템", "description": "검색 증강 생성 시스템", "dept_idx": 1},
    {"name": "품질 대시보드", "description": "품질 지표 시각화 대시보드", "dept_idx": 0},
    {"name": "신제품 기획", "description": "2026년 신제품 기획 프로젝트", "dept_idx": 2},
]

PROJECT_MEMBERS = {
    0: [1, 2, 3],        # PLM 시스템 - 품질팀
    1: [0, 4, 5, 6, 7],  # MemGate - 개발팀
    2: [4, 5, 7],         # RAG 시스템 - 개발팀 일부
    3: [1, 2, 8],         # 품질 대시보드
    4: [8, 9, 10],        # 신제품 기획 - 기획팀
}

CHAT_ROOMS = [
    # 개인
    {"name": "관리자의 메모", "room_type": "personal", "owner_idx": 0},
    {"name": "김품질의 메모", "room_type": "personal", "owner_idx": 1},
    {"name": "최개발의 메모", "room_type": "personal", "owner_idx": 4},
    {"name": "한기획의 메모", "room_type": "personal", "owner_idx": 8},
    # 프로젝트
    {"name": "PLM 개발 채팅", "room_type": "project", "owner_idx": 1, "project_idx": 0},
    {"name": "MemGate 개발 채팅", "room_type": "project", "owner_idx": 0, "project_idx": 1},
    {"name": "RAG 논의", "room_type": "project", "owner_idx": 5, "project_idx": 2},
    # 부서
    {"name": "품질팀 공유", "room_type": "department", "owner_idx": 1, "dept_idx": 0},
    {"name": "개발팀 공유", "room_type": "department", "owner_idx": 0, "dept_idx": 1},
    {"name": "기획팀 공유", "room_type": "department", "owner_idx": 8, "dept_idx": 2},
]

CHAT_ROOM_MEMBERS = {
    0: [0],
    1: [1],
    2: [4],
    3: [8],
    4: [1, 2, 3],
    5: [0, 4, 5, 6, 7],
    6: [4, 5, 7],
    7: [1, 2, 3, 0],   # 품질팀 공유 - 관리자도 포함(데모용)
    8: [0, 4, 5, 6, 7],
    9: [8, 9, 10],
}

# ---- 메모리 ----
MEMORIES = [
    # 개인 메모리
    {"content": "김품질은 코드 리뷰를 오전에 하는 것을 선호한다", "scope": "personal", "owner_idx": 1, "category": "preference", "importance": "medium", "topic_key": "김품질 코드 리뷰 시간"},
    {"content": "최개발은 Python보다 Rust를 선호한다", "scope": "personal", "owner_idx": 4, "category": "preference", "importance": "high", "topic_key": "최개발 언어 선호"},
    {"content": "한기획은 매주 금요일에 주간 보고서를 작성한다", "scope": "personal", "owner_idx": 8, "category": "fact", "importance": "medium", "topic_key": "한기획 주간 보고서"},
    {"content": "김품질은 커피보다 녹차를 선호한다", "scope": "personal", "owner_idx": 1, "category": "preference", "importance": "low", "topic_key": "김품질 음료 선호"},
    {"content": "최개발의 업무 집중 시간은 오후 2시~5시이다", "scope": "personal", "owner_idx": 4, "category": "preference", "importance": "medium", "topic_key": "최개발 업무 시간"},

    # 대화방(프로젝트) 메모리 — 엔티티 포함
    {
        "content": "박관리가 PLM 시스템 프로젝트를 총괄 관리하고 있다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 4,
        "category": "relationship", "importance": "high", "topic_key": "박관리 PLM 관리",
        "entities": [{"name": "박관리", "type": "person"}, {"name": "PLM 시스템", "type": "project"}],
    },
    {
        "content": "김품질이 매주 월요일 품질검사 미팅에 참석한다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 4,
        "category": "fact", "importance": "high", "topic_key": "김품질 품질검사 미팅",
        "entities": [{"name": "김품질", "type": "person"}, {"name": "품질검사 미팅", "type": "meeting"}],
    },
    {
        "content": "품질검사 미팅은 PLM 시스템 프로젝트의 정기 회의이다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 4,
        "category": "fact", "importance": "medium", "topic_key": "품질검사 미팅 PLM",
        "entities": [{"name": "품질검사 미팅", "type": "meeting"}, {"name": "PLM 시스템", "type": "project"}],
    },
    {
        "content": "이검사가 PLM 시스템의 테스트 자동화를 담당하고 있다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 4,
        "category": "relationship", "importance": "high", "topic_key": "이검사 테스트 자동화",
        "entities": [{"name": "이검사", "type": "person"}, {"name": "PLM 시스템", "type": "project"}],
    },
    {
        "content": "최개발이 MemGate 프로젝트의 백엔드 아키텍처를 설계했다",
        "scope": "chatroom", "owner_idx": 0, "chat_room_idx": 5,
        "category": "fact", "importance": "high", "topic_key": "최개발 MemGate 아키텍처",
        "entities": [{"name": "최개발", "type": "person"}, {"name": "MemGate", "type": "project"}],
    },
    {
        "content": "정백엔드가 MemGate 프로젝트의 RAG 파이프라인을 구현 중이다",
        "scope": "chatroom", "owner_idx": 0, "chat_room_idx": 5,
        "category": "fact", "importance": "high", "topic_key": "정백엔드 RAG 구현",
        "entities": [{"name": "정백엔드", "type": "person"}, {"name": "MemGate", "type": "project"}],
    },
    {
        "content": "3월 릴리즈 일정이 MemGate 프로젝트의 첫 번째 마일스톤이다",
        "scope": "chatroom", "owner_idx": 0, "chat_room_idx": 5,
        "category": "decision", "importance": "high", "topic_key": "MemGate 3월 릴리즈",
        "entities": [{"name": "3월 릴리즈", "type": "date"}, {"name": "MemGate", "type": "project"}],
    },

    # ---- 엔티티 그래프 데모용: 크로스룸 메모리 ----
    # 김품질이 PLM 대화방(4)에서 남긴 메모리 → 품질팀 공유(7)에서 검색 시 엔티티로 연결
    {
        "content": "박관리가 PLM 시스템 v2.0 업그레이드 일정을 3월 말로 확정했다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 4,
        "category": "decision", "importance": "high", "topic_key": "PLM v2.0 일정",
        "entities": [{"name": "박관리", "type": "person"}, {"name": "PLM 시스템", "type": "project"}, {"name": "3월 릴리즈", "type": "date"}],
    },
    {
        "content": "이검사가 PLM 시스템의 자동 검사 모듈에서 외관검사 정확도를 95%까지 올렸다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 4,
        "category": "fact", "importance": "high", "topic_key": "이검사 외관검사 정확도",
        "entities": [{"name": "이검사", "type": "person"}, {"name": "PLM 시스템", "type": "project"}, {"name": "외관검사", "type": "topic"}],
    },
    # 품질팀 공유(7)에서의 메모리 — 다른 방이지만 엔티티로 연결됨
    {
        "content": "외관검사 기준이 2026년 1월부터 변경되어 스크래치 허용 한도가 0.3mm로 강화되었다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 7,
        "category": "fact", "importance": "high", "topic_key": "외관검사 기준 변경",
        "entities": [{"name": "외관검사", "type": "topic"}],
    },
    {
        "content": "김품질이 A라인 불량률 개선 프로젝트를 주도하고 있으며 목표는 1.5% 이하이다",
        "scope": "chatroom", "owner_idx": 1, "chat_room_idx": 7,
        "category": "fact", "importance": "high", "topic_key": "김품질 A라인 불량률",
        "entities": [{"name": "김품질", "type": "person"}, {"name": "A라인 불량률 개선", "type": "project"}],
    },
    # 개인 메모리 — 엔티티로 연결
    {
        "content": "박관리는 품질 감사 시 ISO 9001:2015 체크리스트를 항상 사용한다",
        "scope": "personal", "owner_idx": 1, "category": "fact", "importance": "medium", "topic_key": "박관리 ISO 감사",
        "entities": [{"name": "박관리", "type": "person"}],
    },
    # MemGate 대화방(5)에서 — PLM 관련 엔티티 연결
    {
        "content": "MemGate의 문서 RAG 기능이 PLM 시스템 품질 매뉴얼 검색에도 활용될 예정이다",
        "scope": "chatroom", "owner_idx": 0, "chat_room_idx": 5,
        "category": "decision", "importance": "high", "topic_key": "MemGate PLM 연동",
        "entities": [{"name": "MemGate", "type": "project"}, {"name": "PLM 시스템", "type": "project"}],
    },
]

ENTITY_RELATIONS = [
    {"source": "박관리", "source_type": "person", "target": "PLM 시스템", "target_type": "project", "relation": "MANAGES", "owner_idx": 1},
    {"source": "김품질", "source_type": "person", "target": "품질검사 미팅", "target_type": "meeting", "relation": "ATTENDS", "owner_idx": 1},
    {"source": "품질검사 미팅", "source_type": "meeting", "target": "PLM 시스템", "target_type": "project", "relation": "PART_OF", "owner_idx": 1},
    {"source": "이검사", "source_type": "person", "target": "PLM 시스템", "target_type": "project", "relation": "WORKS_ON", "owner_idx": 1},
    {"source": "최개발", "source_type": "person", "target": "MemGate", "target_type": "project", "relation": "WORKS_ON", "owner_idx": 0},
    {"source": "정백엔드", "source_type": "person", "target": "MemGate", "target_type": "project", "relation": "WORKS_ON", "owner_idx": 0},
    {"source": "3월 릴리즈", "source_type": "date", "target": "MemGate", "target_type": "project", "relation": "PART_OF", "owner_idx": 0},
    # 크로스룸 엔티티 연결
    {"source": "김품질", "source_type": "person", "target": "A라인 불량률 개선", "target_type": "project", "relation": "MANAGES", "owner_idx": 1},
    {"source": "김품질", "source_type": "person", "target": "외관검사", "target_type": "topic", "relation": "RELATED_TO", "owner_idx": 1},
    {"source": "이검사", "source_type": "person", "target": "외관검사", "target_type": "topic", "relation": "WORKS_ON", "owner_idx": 1},
    {"source": "외관검사", "source_type": "topic", "target": "PLM 시스템", "target_type": "project", "relation": "PART_OF", "owner_idx": 1},
    {"source": "3월 릴리즈", "source_type": "date", "target": "PLM 시스템", "target_type": "project", "relation": "PART_OF", "owner_idx": 1},
    {"source": "MemGate", "source_type": "project", "target": "PLM 시스템", "target_type": "project", "relation": "RELATED_TO", "owner_idx": 0},
]

# ---- Agent Types ----
AGENT_TYPES = [
    {
        "name": "품질 모니터링",
        "description": "생산 라인 품질 데이터를 실시간 수집·분석하는 에이전트. 불량률, 공정 능력 지수 등을 모니터링하여 품질 이상 시 알림을 전송합니다.",
        "developer_idx": 0,
        "version": "1.0.0",
        "capabilities": ["memory", "message", "log"],
        "public_scope": "public",
        "status": "active",
    },
    {
        "name": "기술문서 분석",
        "description": "기술 문서를 분석하고 핵심 내용을 요약하는 에이전트. PDF, PPTX 등의 문서를 자동으로 인덱싱하고 질의응답에 활용합니다.",
        "developer_idx": 0,
        "version": "1.0.0",
        "capabilities": ["memory", "log"],
        "public_scope": "public",
        "status": "active",
    },
    {
        "name": "코드 리뷰 봇",
        "description": "코드 변경사항을 자동으로 리뷰하고 개선 사항을 제안하는 봇",
        "developer_idx": 4,
        "version": "1.0.0",
        "capabilities": ["memory", "message"],
        "public_scope": "project",
        "project_idx": 1,
        "status": "active",
    },
]

# ---- Agent Instances ----
AGENT_INSTANCES = [
    {
        "name": "품질 모니터링 봇",
        "agent_type_idx": 0,
        "owner_idx": 0,
        "status": "active",
    },
    {
        "name": "기술문서 분석 봇",
        "agent_type_idx": 1,
        "owner_idx": 0,
        "status": "active",
    },
    {
        "name": "품질팀 전용 봇",
        "agent_type_idx": 0,
        "owner_idx": 1,
        "status": "active",
    },
]

# ---- Agent Data (봇이 수집한 데이터) ----
AGENT_DATA = [
    # 품질 모니터링 봇 데이터
    {
        "agent_instance_idx": 0,
        "external_user_id": "sensor-001",
        "internal_user_idx": 0,
        "data_type": "memory",
        "content": "오늘(2026-02-20) A라인 불량률 2.3%, 전일 대비 0.5% 증가. 주요 불량: 외관 스크래치",
        "metadata": {"source": "quality_system", "line": "A", "timestamp": "2026-02-20T17:00:00+09:00"},
    },
    {
        "agent_instance_idx": 0,
        "external_user_id": "sensor-001",
        "internal_user_idx": 0,
        "data_type": "memory",
        "content": "B라인 CPK 지수 1.45로 안정 상태 유지 중 (기준: 1.33 이상)",
        "metadata": {"source": "quality_system", "line": "B", "timestamp": "2026-02-20T17:00:00+09:00"},
    },
    {
        "agent_instance_idx": 0,
        "external_user_id": "sensor-002",
        "internal_user_idx": 0,
        "data_type": "log",
        "content": "A라인 외관검사 장비 교정 완료. 다음 교정일: 2026-03-20",
        "metadata": {"source": "quality_system", "timestamp": "2026-02-19T10:00:00+09:00"},
    },
    {
        "agent_instance_idx": 0,
        "external_user_id": "sensor-001",
        "internal_user_idx": 0,
        "data_type": "memory",
        "content": "이번 주 전체 불량률 1.8%, 목표치(2.0%) 이내. C등급(경결함) 비율이 전체의 70% 차지",
        "metadata": {"source": "quality_system", "timestamp": "2026-02-21T09:00:00+09:00"},
    },
    # 기술문서 분석 봇 데이터
    {
        "agent_instance_idx": 1,
        "external_user_id": "doc-scanner",
        "internal_user_idx": 0,
        "data_type": "memory",
        "content": "MemGate 아키텍처 문서 분석 결과: FastAPI + React + Qdrant 벡터 DB 구성. 주요 기능은 대화 메모리, 문서 RAG, 에이전트 연동",
        "metadata": {"source": "document_analysis", "document": "architecture.pdf", "timestamp": "2026-02-18T14:00:00+09:00"},
    },
    {
        "agent_instance_idx": 1,
        "external_user_id": "doc-scanner",
        "internal_user_idx": 0,
        "data_type": "memory",
        "content": "API 명세서 업데이트: 문서 업로드 API에 PPTX 지원 추가, 슬라이드 이미지 조회 엔드포인트 신규",
        "metadata": {"source": "document_analysis", "document": "api_spec.md", "timestamp": "2026-02-22T11:00:00+09:00"},
    },
    # 품질팀 전용 봇 데이터
    {
        "agent_instance_idx": 2,
        "external_user_id": "quality-user-kim",
        "internal_user_idx": 1,
        "data_type": "memory",
        "content": "품질 검사는 매주 월요일과 목요일에 진행된다. 월요일은 A라인, 목요일은 B라인 집중 검사",
        "metadata": {"source": "chat", "timestamp": "2026-02-17T09:00:00+09:00"},
    },
]

EXTERNAL_USER_MAPPINGS = [
    {"agent_instance_idx": 0, "external_user_id": "sensor-001", "internal_user_idx": 0, "external_system_name": "quality_monitoring_system"},
    {"agent_instance_idx": 0, "external_user_id": "sensor-002", "internal_user_idx": 0, "external_system_name": "quality_monitoring_system"},
    {"agent_instance_idx": 1, "external_user_id": "doc-scanner", "internal_user_idx": 0, "external_system_name": "document_analysis_system"},
    {"agent_instance_idx": 2, "external_user_id": "quality-user-kim", "internal_user_idx": 1, "external_system_name": "quality_system"},
]

AGENT_INSTANCE_SHARES = [
    {"agent_instance_idx": 0, "shared_with_user_idx": 1, "role": "viewer"},  # 품질 모니터링 봇 → 김품질
    {"agent_instance_idx": 0, "shared_with_user_idx": 4, "role": "viewer"},  # 품질 모니터링 봇 → 최개발
    {"agent_instance_idx": 1, "shared_with_user_idx": 4, "role": "member"},  # 기술문서 분석 봇 → 최개발
    {"agent_instance_idx": 2, "shared_with_user_idx": 2, "role": "member"},  # 품질팀 전용 봇 → 이검사
]

# ---- Mchat 매핑 ----
MCHAT_USER_MAPPINGS = [
    {"mchat_user_id": "mchat-kim-001", "mchat_username": "kim.quality", "agent_user_idx": 1},
    {"mchat_user_id": "mchat-lee-002", "mchat_username": "lee.inspector", "agent_user_idx": 2},
    {"mchat_user_id": "mchat-park-003", "mchat_username": "park.manager", "agent_user_idx": 3},
    {"mchat_user_id": "mchat-admin-000", "mchat_username": "admin", "agent_user_idx": 0},
]

# Mchat 채널 매핑 (chat_room_idx로 MemGate 대화방과 연결)
MCHAT_CHANNEL_MAPPINGS = [
    {"mchat_channel_id": "mchat-ch-quality", "mchat_channel_name": "#품질관리", "mchat_team_id": "team-001", "agent_room_idx": 7, "sync_enabled": True},
    {"mchat_channel_id": "mchat-ch-dev", "mchat_channel_name": "#개발팀-일반", "mchat_team_id": "team-001", "agent_room_idx": 8, "sync_enabled": True},
]

# Mchat 대화 요약 로그
MCHAT_SUMMARY_LOGS = [
    {
        "mchat_channel_id": "mchat-ch-quality",
        "channel_name": "#품질관리",
        "period_start_ms": 1708300800000,  # 2026-02-19 00:00 KST
        "period_end_ms": 1708387200000,    # 2026-02-20 00:00 KST
        "message_count": 45,
        "participant_count": 4,
        "summary_content": "품질팀 채널 대화 요약 (2/19):\n- A라인 외관검사 장비 교정 완료 보고 (이검사)\n- 이번 주 불량률 추이 공유: 1.8% (목표 2.0% 이내)\n- 박관리: 다음 주 월요일 품질검사 미팅 안건 요청\n- 김품질: 스크래치 불량 증가 원인 분석 필요",
    },
    {
        "mchat_channel_id": "mchat-ch-dev",
        "channel_name": "#개발팀-일반",
        "period_start_ms": 1708300800000,
        "period_end_ms": 1708387200000,
        "message_count": 32,
        "participant_count": 5,
        "summary_content": "개발팀 채널 대화 요약 (2/19):\n- PPTX 슬라이드 검색 기능 구현 완료 (정백엔드)\n- 3월 릴리즈 범위 확정: 문서 RAG + PPTX + Agent 연동\n- 프론트엔드 슬라이드 이미지 표시 UI 작업 시작 (강프론트)\n- Docker 배포 환경 LibreOffice 패키지 추가 필요 확인",
    },
]

SHARES = [
    {"resource_type": "project", "resource_idx": 0, "target_type": "user", "target_idx": 4, "role": "member", "created_by_idx": 1},
    {"resource_type": "project", "resource_idx": 1, "target_type": "user", "target_idx": 1, "role": "viewer", "created_by_idx": 0},
    {"resource_type": "chat_room", "resource_idx": 5, "target_type": "user", "target_idx": 1, "role": "viewer", "created_by_idx": 0},
    {"resource_type": "chat_room", "resource_idx": 7, "target_type": "department", "target_idx": 1, "role": "viewer", "created_by_idx": 1},
]


# ==================== 시드 실행 ====================

async def seed_demo():
    """데모용 전체 시드 데이터 생성"""
    print("=" * 60)
    print("  MemGate 데모 시드 데이터 생성")
    print("=" * 60)

    await init_database()

    try:
        await asyncio.wait_for(init_vector_store(), timeout=10)
    except asyncio.TimeoutError:
        print("⚠️  Qdrant 연결 타임아웃 (벡터 검색 비활성화)")
    except Exception as e:
        print(f"⚠️  Qdrant 연결 실패: {e}")

    db = await get_db_sync()

    embedding_provider = None
    try:
        embedding_provider = get_embedding_provider()
        print("✅ Embedding Provider 연결됨")
    except Exception as e:
        print(f"⚠️  Embedding Provider 연결 실패: {e}")

    settings = get_settings()
    test_password = getattr(settings, "test_user_password", "test123")
    test_password_hash = hash_password(test_password)
    embedding_failed = False

    try:
        now_fn = lambda: (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()

        # ---- 1. 부서 ----
        print("\n📁 부서 생성...")
        dept_ids = []
        for dept in DEPARTMENTS:
            did = str(uuid.uuid4())
            await db.execute("INSERT INTO departments (id, name, description) VALUES (?, ?, ?)", (did, dept["name"], dept["description"]))
            dept_ids.append(did)
            print(f"  ✓ {dept['name']}")

        # ---- 2. 사용자 ----
        print("\n👤 사용자 생성...")
        user_ids = []
        for user in USERS:
            uid = user.get("id", str(uuid.uuid4()))
            role = user.get("role", "user")
            pw = None if uid == "dev-user-001" else test_password_hash
            now = now_fn()
            await db.execute(
                "INSERT INTO users (id, name, email, role, department_id, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (uid, user["name"], user["email"], role, dept_ids[user["dept_idx"]], pw, now, now),
            )
            user_ids.append(uid)
            pw_info = f" (pw: {test_password})" if pw else " (SSO only)"
            print(f"  ✓ {user['name']} ({user['email']}){pw_info}")

        # ---- 3. 프로젝트 ----
        print("\n📋 프로젝트 생성...")
        project_ids = []
        for p in PROJECTS:
            pid = str(uuid.uuid4())
            now = now_fn()
            await db.execute("INSERT INTO projects (id, name, description, department_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                             (pid, p["name"], p["description"], dept_ids[p["dept_idx"]], now, now))
            project_ids.append(pid)
            print(f"  ✓ {p['name']}")

        # ---- 4. 프로젝트 멤버 ----
        print("\n👥 프로젝트 멤버...")
        for pidx, members in PROJECT_MEMBERS.items():
            for i, uidx in enumerate(members):
                role = "owner" if i == 0 else "member"
                await db.execute("INSERT INTO project_members (id, project_id, user_id, role) VALUES (?, ?, ?, ?)",
                                 (str(uuid.uuid4()), project_ids[pidx], user_ids[uidx], role))
            print(f"  ✓ {PROJECTS[pidx]['name']}: {len(members)}명")

        # ---- 5. 대화방 ----
        print("\n💬 대화방 생성...")
        room_ids = []
        for r in CHAT_ROOMS:
            rid = str(uuid.uuid4())
            proj_id = project_ids[r["project_idx"]] if "project_idx" in r else None
            dep_id = dept_ids[r["dept_idx"]] if "dept_idx" in r else None

            # 컨텍스트 소스 기본값 (에이전트 메모리 포함 설정)
            ctx = json.dumps({"memory": {"include_this_room": True, "other_chat_rooms": [], "agent_instances": []}, "rag": {"collections": [], "filters": {}}})

            await db.execute("INSERT INTO chat_rooms (id, name, room_type, owner_id, project_id, department_id, context_sources) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (rid, r["name"], r["room_type"], user_ids[r["owner_idx"]], proj_id, dep_id, ctx))
            room_ids.append(rid)
            print(f"  ✓ {r['name']} ({r['room_type']})")

        # ---- 6. 대화방 멤버 ----
        print("\n👥 대화방 멤버...")
        for ridx, members in CHAT_ROOM_MEMBERS.items():
            for i, uidx in enumerate(members):
                role = "owner" if i == 0 else "member"
                await db.execute("INSERT INTO chat_room_members (id, chat_room_id, user_id, role) VALUES (?, ?, ?, ?)",
                                 (str(uuid.uuid4()), room_ids[ridx], user_ids[uidx], role))
            print(f"  ✓ {CHAT_ROOMS[ridx]['name']}: {len(members)}명")

        # ---- 7. Agent Types ----
        print("\n🤖 Agent Types...")
        atype_ids = []
        for at in AGENT_TYPES:
            atid = str(uuid.uuid4())
            now = now_fn()
            proj_id = project_ids[at["project_idx"]] if "project_idx" in at else None
            await db.execute(
                "INSERT INTO agent_types (id, name, description, developer_id, version, capabilities, public_scope, project_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (atid, at["name"], at["description"], user_ids[at["developer_idx"]], at["version"],
                 json.dumps(at["capabilities"]), at["public_scope"], proj_id, at["status"], now, now))
            atype_ids.append(atid)
            print(f"  ✓ {at['name']}")

        # ---- 8. Agent Instances ----
        print("\n🤖 Agent Instances...")
        ainst_ids = []
        for ai_inst in AGENT_INSTANCES:
            aiid = str(uuid.uuid4())
            api_key = f"sk_{uuid.uuid4().hex}"
            now = now_fn()
            await db.execute(
                "INSERT INTO agent_instances (id, agent_type_id, name, owner_id, api_key, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (aiid, atype_ids[ai_inst["agent_type_idx"]], ai_inst["name"], user_ids[ai_inst["owner_idx"]], api_key, ai_inst["status"], now, now))
            ainst_ids.append(aiid)
            print(f"  ✓ {ai_inst['name']} (key: {api_key[:20]}...)")

        # ---- 9. External User Mappings ----
        print("\n🔗 External User Mappings...")
        for m in EXTERNAL_USER_MAPPINGS:
            await db.execute(
                "INSERT INTO external_user_mappings (id, agent_instance_id, external_user_id, internal_user_id, external_system_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), ainst_ids[m["agent_instance_idx"]], m["external_user_id"], user_ids[m["internal_user_idx"]], m["external_system_name"], now_fn()))
            print(f"  ✓ {m['external_user_id']} → {USERS[m['internal_user_idx']]['name']}")

        # ---- 10. Agent Data ----
        print("\n📊 Agent Data...")
        for ad in AGENT_DATA:
            await db.execute(
                "INSERT INTO agent_data (id, agent_instance_id, external_user_id, internal_user_id, data_type, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), ainst_ids[ad["agent_instance_idx"]], ad["external_user_id"], user_ids[ad["internal_user_idx"]],
                 ad["data_type"], ad["content"], json.dumps(ad["metadata"]), now_fn()))
            print(f"  ✓ [{ad['data_type']}] {ad['content'][:50]}...")

        # ---- 11. Agent 메모리 (type=memory인 Agent Data) ----
        print("\n🤖 Agent 메모리...")
        agent_emb_failed = False
        for ad in AGENT_DATA:
            if ad["data_type"] != "memory":
                continue
            mid = str(uuid.uuid4())
            vid = str(uuid.uuid4())
            now = now_fn()
            vector = None
            if embedding_provider and not agent_emb_failed:
                try:
                    vector = await asyncio.wait_for(embedding_provider.embed(ad["content"]), timeout=10)
                except Exception as e:
                    print(f"  ⚠ 임베딩 실패: {e}")
                    agent_emb_failed = True
                    vid = None
            else:
                vid = None
            meta = {**ad["metadata"], "source": "agent", "agent_instance_id": ainst_ids[ad["agent_instance_idx"]], "agent_instance_name": AGENT_INSTANCES[ad["agent_instance_idx"]]["name"]}
            await db.execute(
                "INSERT INTO memories (id, content, vector_id, scope, owner_id, category, importance, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mid, ad["content"], vid, "agent", user_ids[ad["internal_user_idx"]], "fact", "medium", json.dumps(meta), now, now))
            if vector and vid:
                await upsert_vector(vid, vector, {"memory_id": mid, "scope": "agent", "owner_id": user_ids[ad["internal_user_idx"]], "agent_instance_id": ainst_ids[ad["agent_instance_idx"]]})
            print(f"  🤖 {ad['content'][:50]}...")

        # ---- 12. Agent Instance Shares ----
        print("\n🔗 Agent Instance Shares...")
        for s in AGENT_INSTANCE_SHARES:
            await db.execute("INSERT INTO agent_instance_shares (id, agent_instance_id, shared_with_user_id, role, created_at) VALUES (?, ?, ?, ?, ?)",
                             (str(uuid.uuid4()), ainst_ids[s["agent_instance_idx"]], user_ids[s["shared_with_user_idx"]], s["role"], now_fn()))
            print(f"  ✓ {AGENT_INSTANCES[s['agent_instance_idx']]['name']} → {USERS[s['shared_with_user_idx']]['name']} ({s['role']})")

        # ---- 13. 메모리 + 엔티티 ----
        print("\n🧠 메모리 + 엔티티...")
        memory_ids = []
        for mem in MEMORIES:
            mid = str(uuid.uuid4())
            vid = str(uuid.uuid4())
            now = now_fn()
            vector = None
            if embedding_provider and not embedding_failed:
                try:
                    vector = await asyncio.wait_for(embedding_provider.embed(mem["content"]), timeout=10)
                except Exception as e:
                    print(f"  ⚠ 임베딩 실패: {e}")
                    embedding_failed = True
                    vid = None
            else:
                vid = None
            cr_id = room_ids[mem["chat_room_idx"]] if "chat_room_idx" in mem else None
            await db.execute(
                "INSERT INTO memories (id, content, vector_id, scope, owner_id, chat_room_id, category, importance, topic_key, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mid, mem["content"], vid, mem["scope"], user_ids[mem["owner_idx"]], cr_id, mem.get("category"), mem.get("importance", "medium"), mem.get("topic_key"), now, now))
            if vector and vid:
                payload = {"memory_id": mid, "scope": mem["scope"], "owner_id": user_ids[mem["owner_idx"]]}
                if cr_id:
                    payload["chat_room_id"] = cr_id
                await upsert_vector(vid, vector, payload)
            # 엔티티
            if "entities" in mem:
                for ent in mem["entities"]:
                    norm = ent["name"].strip().lower()
                    oid = user_ids[mem["owner_idx"]]
                    cur = await db.execute("SELECT id FROM entities WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?", (norm, ent["type"], oid))
                    row = await cur.fetchone()
                    if row:
                        eid = row[0]
                    else:
                        eid = str(uuid.uuid4())
                        await db.execute("INSERT INTO entities (id, name, name_normalized, entity_type, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                         (eid, ent["name"], norm, ent["type"], oid, now, now))
                    await db.execute("INSERT OR IGNORE INTO memory_entities (id, memory_id, entity_id, relation_type) VALUES (?, ?, ?, ?)",
                                     (str(uuid.uuid4()), mid, eid, "mentioned"))
            memory_ids.append(mid)
            print(f"  ✓ {mem['content'][:50]}...")

        # ---- 14. 엔티티 관계 ----
        print("\n🔗 엔티티 관계...")
        for rel in ENTITY_RELATIONS:
            oid = user_ids[rel["owner_idx"]]
            cur = await db.execute("SELECT id FROM entities WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?", (rel["source"].strip().lower(), rel["source_type"], oid))
            src = await cur.fetchone()
            cur = await db.execute("SELECT id FROM entities WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?", (rel["target"].strip().lower(), rel["target_type"], oid))
            tgt = await cur.fetchone()
            if src and tgt:
                await db.execute("INSERT OR IGNORE INTO entity_relations (id, source_entity_id, target_entity_id, relation_type, owner_id) VALUES (?, ?, ?, ?, ?)",
                                 (str(uuid.uuid4()), src[0], tgt[0], rel["relation"], oid))
                print(f"  ✓ {rel['source']} →{rel['relation']}→ {rel['target']}")

        # ---- 15. Mchat 사용자 매핑 ----
        print("\n💬 Mchat 사용자 매핑...")
        for m in MCHAT_USER_MAPPINGS:
            await db.execute("INSERT INTO mchat_user_mapping (id, mchat_user_id, mchat_username, agent_user_id, created_at) VALUES (?, ?, ?, ?, ?)",
                             (str(uuid.uuid4()), m["mchat_user_id"], m["mchat_username"], user_ids[m["agent_user_idx"]], now_fn()))
            print(f"  ✓ @{m['mchat_username']} → {USERS[m['agent_user_idx']]['name']}")

        # ---- 16. Mchat 채널 매핑 ----
        print("\n💬 Mchat 채널 매핑...")
        for ch in MCHAT_CHANNEL_MAPPINGS:
            await db.execute(
                "INSERT INTO mchat_channel_mapping (id, mchat_channel_id, mchat_channel_name, mchat_team_id, agent_room_id, sync_enabled, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), ch["mchat_channel_id"], ch["mchat_channel_name"], ch["mchat_team_id"], room_ids[ch["agent_room_idx"]], ch["sync_enabled"], now_fn()))
            print(f"  ✓ {ch['mchat_channel_name']} ↔ {CHAT_ROOMS[ch['agent_room_idx']]['name']}")

        # ---- 17. Mchat 대화 요약 로그 ----
        print("\n📝 Mchat 대화 요약...")
        for sl in MCHAT_SUMMARY_LOGS:
            await db.execute(
                "INSERT INTO mchat_summary_log (id, mchat_channel_id, channel_name, period_start_ms, period_end_ms, message_count, participant_count, summary_content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), sl["mchat_channel_id"], sl["channel_name"], sl["period_start_ms"], sl["period_end_ms"],
                 sl["message_count"], sl["participant_count"], sl["summary_content"], now_fn()))
            print(f"  ✓ {sl['channel_name']} ({sl['message_count']}건)")

        # ---- 18. 공유 설정 ----
        print("\n🔗 공유 설정...")
        for sh in SHARES:
            res_id = project_ids[sh["resource_idx"]] if sh["resource_type"] == "project" else room_ids[sh["resource_idx"]]
            if sh["target_type"] == "user":
                tgt_id = user_ids[sh["target_idx"]]
            elif sh["target_type"] == "project":
                tgt_id = project_ids[sh["target_idx"]]
            else:
                tgt_id = dept_ids[sh["target_idx"]]
            await db.execute(
                "INSERT INTO shares (id, resource_type, resource_id, target_type, target_id, role, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), sh["resource_type"], res_id, sh["target_type"], tgt_id, sh["role"], now_fn(), user_ids[sh["created_by_idx"]]))
            print(f"  ✓ {sh['resource_type']}→{sh['target_type']} ({sh['role']})")

        # ---- 19. 데모 문서 생성 + 업로드 ----
        print("\n📄 데모 문서 생성...")
        try:
            from src.scripts.create_demo_documents import create_all_demo_documents
            doc_files = create_all_demo_documents()

            # 문서 자동 업로드 (품질팀 공유 대화방에 PPTX, MemGate 개발 채팅에 TXT)
            from src.document.service import DocumentService
            doc_service = DocumentService(db)

            for f in doc_files:
                fname = f.name
                content = f.read_bytes()
                target_room_idx = 7 if fname.endswith(".pptx") else 5  # 품질팀 공유 / MemGate 개발 채팅
                owner_idx = 1 if fname.endswith(".pptx") else 0  # 김품질 / 관리자

                try:
                    doc = await doc_service.upload_document(
                        file_content=content,
                        filename=fname,
                        owner_id=user_ids[owner_idx],
                        chat_room_id=room_ids[target_room_idx],
                    )
                    print(f"  ✅ {fname} → {CHAT_ROOMS[target_room_idx]['name']} (chunks: {doc.get('chunk_count', '?')})")
                except Exception as e:
                    print(f"  ⚠️ {fname} 업로드 실패: {e}")
        except Exception as e:
            print(f"  ⚠️ 데모 문서 생성 실패: {e}")

        await db.commit()

        # ---- 요약 ----
        print("\n" + "=" * 60)
        print("  ✅ 데모 시드 데이터 생성 완료!")
        print("=" * 60)
        print(f"  📁 부서: {len(DEPARTMENTS)}")
        print(f"  👤 사용자: {len(USERS)}")
        print(f"  📋 프로젝트: {len(PROJECTS)}")
        print(f"  💬 대화방: {len(CHAT_ROOMS)}")
        print(f"  🧠 메모리: {len(MEMORIES)}")
        print(f"  🤖 Agent Types: {len(AGENT_TYPES)}")
        print(f"  🤖 Agent Instances: {len(AGENT_INSTANCES)}")
        print(f"  📊 Agent Data: {len(AGENT_DATA)}")
        print(f"  🔗 Mchat 사용자 매핑: {len(MCHAT_USER_MAPPINGS)}")
        print(f"  🔗 Mchat 채널 매핑: {len(MCHAT_CHANNEL_MAPPINGS)}")
        print(f"  📝 Mchat 대화 요약: {len(MCHAT_SUMMARY_LOGS)}")
        print(f"  📄 데모 문서: 2개")
        print("=" * 60)
        print()
        print("📌 데모 로그인 계정:")
        print(f"  관리자: admin@test.com / {test_password}")
        print(f"  김품질: kim.quality@company.com / {test_password}")
        print(f"  최개발: choi.dev@company.com / {test_password}")
        print()
        print("📌 주요 대화방:")
        for i, r in enumerate(CHAT_ROOMS):
            print(f"  [{i}] {r['name']} ({r['room_type']})")
        print()

    finally:
        await db.close()
        await close_database()
        await close_vector_store()


if __name__ == "__main__":
    asyncio.run(seed_demo())
