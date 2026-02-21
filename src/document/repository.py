"""문서 리포지토리"""

import json
import uuid
from datetime import datetime
from typing import Any, Literal

import aiosqlite


class DocumentRepository:
    """문서 DB 접근 레이어"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create_document(
        self,
        name: str,
        file_type: Literal["pdf", "txt"],
        file_size: int,
        owner_id: str,
        chat_room_id: str | None = None,
    ) -> dict[str, Any]:
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """INSERT INTO documents (id, name, file_type, file_size, owner_id, chat_room_id, status, chunk_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'processing', 0, ?)""",
            (doc_id, name, file_type, file_size, owner_id, chat_room_id, now),
        )
        await self.db.commit()
        return await self.get_document(doc_id)

    async def get_document(self, doc_id: str) -> dict[str, Any] | None:
        cursor = await self.db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_documents(
        self,
        owner_id: str | None = None,
        chat_room_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if chat_room_id:
            # 대화방에 연결된 문서 + 직접 업로드된 문서
            cursor = await self.db.execute(
                """SELECT DISTINCT d.* FROM documents d
                   LEFT JOIN document_chat_rooms dcr ON d.id = dcr.document_id
                   WHERE d.chat_room_id = ? OR dcr.chat_room_id = ?
                   ORDER BY d.created_at DESC
                   LIMIT ? OFFSET ?""",
                (chat_room_id, chat_room_id, limit, offset),
            )
        elif owner_id:
            cursor = await self.db.execute(
                """SELECT * FROM documents WHERE owner_id = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (owner_id, limit, offset),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_document_status(
        self, doc_id: str, status: str, chunk_count: int = 0
    ) -> None:
        await self.db.execute(
            "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
            (status, chunk_count, doc_id),
        )
        await self.db.commit()

    async def delete_document(self, doc_id: str) -> bool:
        await self.db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await self.db.commit()
        return True

    async def create_chunk(
        self,
        document_id: str,
        content: str,
        chunk_index: int,
        vector_id: str,
    ) -> dict[str, Any]:
        chunk_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO document_chunks (id, document_id, content, chunk_index, vector_id)
               VALUES (?, ?, ?, ?, ?)""",
            (chunk_id, document_id, content, chunk_index, vector_id),
        )
        await self.db.commit()
        return {
            "id": chunk_id,
            "document_id": document_id,
            "content": content,
            "chunk_index": chunk_index,
            "vector_id": vector_id,
        }

    async def get_chunks(self, document_id: str) -> list[dict[str, Any]]:
        cursor = await self.db.execute(
            "SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_chunk_vector_ids(self, document_id: str) -> list[str]:
        cursor = await self.db.execute(
            "SELECT vector_id FROM document_chunks WHERE document_id = ? AND vector_id IS NOT NULL",
            (document_id,),
        )
        rows = await cursor.fetchall()
        return [row["vector_id"] for row in rows]

    async def link_document_to_room(
        self, document_id: str, chat_room_id: str
    ) -> dict[str, Any]:
        link_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """INSERT OR IGNORE INTO document_chat_rooms (id, document_id, chat_room_id, linked_at)
               VALUES (?, ?, ?, ?)""",
            (link_id, document_id, chat_room_id, now),
        )
        await self.db.commit()
        return {
            "document_id": document_id,
            "chat_room_id": chat_room_id,
            "linked_at": now,
        }

    async def unlink_document_from_room(
        self, document_id: str, chat_room_id: str
    ) -> bool:
        await self.db.execute(
            "DELETE FROM document_chat_rooms WHERE document_id = ? AND chat_room_id = ?",
            (document_id, chat_room_id),
        )
        await self.db.commit()
        return True

    async def get_linked_document_ids(self, chat_room_id: str) -> list[str]:
        """대화방에 연결된 문서 ID 목록 (직접 업로드 + 링크)"""
        cursor = await self.db.execute(
            """SELECT DISTINCT d.id FROM documents d
               LEFT JOIN document_chat_rooms dcr ON d.id = dcr.document_id
               WHERE d.chat_room_id = ? OR dcr.chat_room_id = ?""",
            (chat_room_id, chat_room_id),
        )
        rows = await cursor.fetchall()
        return [row["id"] for row in rows]

    async def search_chunks_by_keyword(
        self, query: str, document_ids: list[str], limit: int = 10
    ) -> list[dict]:
        """FTS5 키워드 검색 (chunk_index 포함)"""
        if not document_ids or not query.strip():
            return []

        placeholders = ",".join("?" * len(document_ids))
        try:
            cursor = await self.db.execute(
                f"""SELECT fts.chunk_id, fts.document_id, fts.content,
                           dc.chunk_index,
                           fts.rank * -1 as score
                    FROM document_chunks_fts fts
                    LEFT JOIN document_chunks dc ON dc.id = fts.chunk_id
                    WHERE document_chunks_fts MATCH ?
                      AND fts.document_id IN ({placeholders})
                    ORDER BY fts.rank
                    LIMIT ?""",
                [query, *document_ids, limit],
            )
            return [dict(row) for row in await cursor.fetchall()]
        except Exception as e:
            print(f"FTS 키워드 검색 실패: {e}")
            return []
