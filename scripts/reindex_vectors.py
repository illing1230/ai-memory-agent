"""누락된 벡터 재생성 스크립트 — SQLite에는 있지만 Qdrant에 없는 메모리를 재인덱싱"""
import asyncio
import sys
sys.path.insert(0, ".")

from qdrant_client import QdrantClient
import aiosqlite
import httpx

QDRANT_URL = "http://localhost:6333"
COLLECTION = "ai-memory-agent"
EMBEDDING_URL = "http://localhost:7997"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
DB_PATH = "./data/memory.db"


async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{EMBEDDING_URL}/embeddings",
            json={"input": text, "model": EMBEDDING_MODEL},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]


async def main():
    # Get all memory vector_ids from SQLite
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT id, content, vector_id, scope, owner_id, chat_room_id FROM memories WHERE vector_id IS NOT NULL")
    memories = [dict(row) for row in await cursor.fetchall()]
    await db.close()
    
    print(f"Total memories with vector_id: {len(memories)}")
    
    # Check which ones exist in Qdrant
    client = QdrantClient(url=QDRANT_URL)
    
    missing = []
    for mem in memories:
        try:
            results = client.retrieve(COLLECTION, ids=[mem["vector_id"]], with_payload=False, with_vectors=False)
            if not results:
                missing.append(mem)
        except Exception:
            missing.append(mem)
    
    print(f"Missing from Qdrant: {len(missing)}")
    
    if not missing:
        print("All vectors are present! Nothing to do.")
        return
    
    # Re-embed and upsert missing vectors
    from qdrant_client.models import PointStruct
    
    for i, mem in enumerate(missing, 1):
        try:
            vector = await embed(mem["content"])
            client.upsert(
                collection_name=COLLECTION,
                points=[
                    PointStruct(
                        id=mem["vector_id"],
                        vector=vector,
                        payload={
                            "memory_id": mem["id"],
                            "scope": mem["scope"],
                            "owner_id": mem["owner_id"],
                            "chat_room_id": mem["chat_room_id"],
                        },
                    )
                ],
            )
            print(f"  [{i}/{len(missing)}] ✅ {mem['content'][:60]}")
        except Exception as e:
            print(f"  [{i}/{len(missing)}] ❌ {e}")
    
    print(f"\nDone! Re-indexed {len(missing)} vectors.")


if __name__ == "__main__":
    asyncio.run(main())
