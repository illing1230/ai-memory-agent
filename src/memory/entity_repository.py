"""EntityRepository - 엔티티 데이터 접근 계층

메모리에서 추출한 엔티티(사람, 미팅, 프로젝트 등)를 관리하고,
엔티티 기반 크로스룸 메모리 검색을 지원한다.
"""

import uuid
import unicodedata
import re
from datetime import datetime

import aiosqlite


class EntityRepository:
    """엔티티 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    @staticmethod
    def normalize_entity_name(name: str) -> str:
        """엔티티 이름 정규화: strip, NFKC, lowercase, 공백 정리"""
        name = name.strip()
        name = unicodedata.normalize("NFKC", name)
        name = name.lower()
        name = re.sub(r"\s+", " ", name)
        return name

    async def get_or_create_entity(
        self,
        name: str,
        entity_type: str,
        owner_id: str,
    ) -> dict:
        """normalized 이름으로 엔티티 조회 → 없으면 생성"""
        name_normalized = self.normalize_entity_name(name)

        cursor = await self.db.execute(
            """SELECT * FROM entities
               WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?""",
            (name_normalized, entity_type, owner_id),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)

        entity_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """INSERT INTO entities (id, name, name_normalized, entity_type, owner_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entity_id, name.strip(), name_normalized, entity_type, owner_id, now, now),
        )
        await self.db.commit()

        cursor = await self.db.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = await cursor.fetchone()
        return dict(row)

    async def link_memory_entity(
        self,
        memory_id: str,
        entity_id: str,
        relation_type: str = "mentioned",
    ) -> None:
        """메모리-엔티티 연결 (이미 존재하면 무시)"""
        link_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT OR IGNORE INTO memory_entities (id, memory_id, entity_id, relation_type)
               VALUES (?, ?, ?, ?)""",
            (link_id, memory_id, entity_id, relation_type),
        )
        await self.db.commit()

    @staticmethod
    def _strip_korean_particles(word: str) -> str:
        """한국어 조사/어미 제거 (간이)"""
        particles = (
            "이랑", "에서", "한테", "까지", "부터", "에게", "으로", "처럼",
            "만큼", "대로", "보다", "같이", "마다", "조차", "밖에",
            "랑", "과", "와", "의", "에", "를", "을", "는", "은",
            "가", "이", "도", "로", "만", "며", "고", "서",
        )
        for p in particles:
            if word.endswith(p) and len(word) > len(p):
                return word[: -len(p)]
        return word

    async def find_entities_by_query(
        self,
        query: str,
        owner_id: str,
    ) -> list[dict]:
        """쿼리 텍스트로 엔티티 검색: exact → LIKE partial 2단계"""
        query_normalized = self.normalize_entity_name(query)
        results = []
        seen_ids = set()

        # 1단계: exact match
        cursor = await self.db.execute(
            """SELECT * FROM entities
               WHERE name_normalized = ? AND owner_id = ?""",
            (query_normalized, owner_id),
        )
        for row in await cursor.fetchall():
            entity = dict(row)
            if entity["id"] not in seen_ids:
                results.append(entity)
                seen_ids.add(entity["id"])

        # 2단계: partial match (LIKE) — 쿼리의 각 단어로 검색 (조사 제거 포함)
        words = query_normalized.split()
        search_tokens = set()
        for word in words:
            # 특수문자 제거
            cleaned = re.sub(r"[?!.,;:~]", "", word)
            if len(cleaned) >= 2:
                search_tokens.add(cleaned)
            # 조사 제거 버전도 추가
            stripped = self._strip_korean_particles(cleaned)
            if len(stripped) >= 2 and stripped != cleaned:
                search_tokens.add(stripped)

        for token in search_tokens:
            cursor = await self.db.execute(
                """SELECT * FROM entities
                   WHERE name_normalized LIKE ? AND owner_id = ?""",
                (f"%{token}%", owner_id),
            )
            for row in await cursor.fetchall():
                entity = dict(row)
                if entity["id"] not in seen_ids:
                    results.append(entity)
                    seen_ids.add(entity["id"])

        return results

    async def get_memory_ids_by_entity_ids(
        self,
        entity_ids: list[str],
    ) -> list[str]:
        """엔티티 ID 목록으로 연결된 메모리 ID 조회 (superseded 제외)"""
        if not entity_ids:
            return []

        placeholders = ",".join("?" * len(entity_ids))
        cursor = await self.db.execute(
            f"""SELECT DISTINCT me.memory_id
                FROM memory_entities me
                JOIN memories m ON m.id = me.memory_id
                WHERE me.entity_id IN ({placeholders})
                  AND m.superseded = 0""",
            entity_ids,
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def get_entity_ids_by_memory_ids(
        self,
        memory_ids: list[str],
    ) -> list[str]:
        """메모리 ID 목록에 연결된 엔티티 ID 조회"""
        if not memory_ids:
            return []

        placeholders = ",".join("?" * len(memory_ids))
        cursor = await self.db.execute(
            f"""SELECT DISTINCT entity_id FROM memory_entities
                WHERE memory_id IN ({placeholders})""",
            memory_ids,
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def create_relation(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relation_type: str,
        owner_id: str,
    ) -> None:
        """엔티티 간 관계 생성 (이미 존재하면 무시)"""
        relation_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT OR IGNORE INTO entity_relations
               (id, source_entity_id, target_entity_id, relation_type, owner_id)
               VALUES (?, ?, ?, ?, ?)""",
            (relation_id, source_entity_id, target_entity_id, relation_type.upper(), owner_id),
        )
        await self.db.commit()

    async def get_related_entity_ids(
        self,
        entity_ids: list[str],
        owner_id: str,
    ) -> list[str]:
        """주어진 엔티티와 관계된 다른 엔티티 ID 반환 (양방향)"""
        if not entity_ids:
            return []

        placeholders = ",".join("?" * len(entity_ids))

        # source → target
        cursor = await self.db.execute(
            f"""SELECT DISTINCT target_entity_id FROM entity_relations
                WHERE source_entity_id IN ({placeholders}) AND owner_id = ?""",
            [*entity_ids, owner_id],
        )
        rows = await cursor.fetchall()
        related = {row[0] for row in rows}

        # target → source
        cursor = await self.db.execute(
            f"""SELECT DISTINCT source_entity_id FROM entity_relations
                WHERE target_entity_id IN ({placeholders}) AND owner_id = ?""",
            [*entity_ids, owner_id],
        )
        rows = await cursor.fetchall()
        related.update(row[0] for row in rows)

        # 입력 entity_ids 제외
        related -= set(entity_ids)
        return list(related)

    async def get_entities_by_ids(self, entity_ids: list[str]) -> list[dict]:
        """엔티티 ID 목록으로 엔티티 정보 조회"""
        if not entity_ids:
            return []

        placeholders = ",".join("?" * len(entity_ids))
        cursor = await self.db.execute(
            f"SELECT * FROM entities WHERE id IN ({placeholders})",
            entity_ids,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def delete_memory_entity_links(self, memory_id: str) -> None:
        """메모리에 연결된 엔티티 링크 삭제"""
        await self.db.execute(
            "DELETE FROM memory_entities WHERE memory_id = ?",
            (memory_id,),
        )
        await self.db.commit()

    async def list_entities(
        self,
        owner_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """사용자 소유 엔티티 목록 (관계 포함)"""
        cursor = await self.db.execute(
            """SELECT e.*, COUNT(me.id) as mention_count
               FROM entities e
               LEFT JOIN memory_entities me ON me.entity_id = e.id
               WHERE e.owner_id = ?
               GROUP BY e.id
               ORDER BY mention_count DESC
               LIMIT ? OFFSET ?""",
            (owner_id, limit, offset),
        )
        return [dict(row) for row in await cursor.fetchall()]
