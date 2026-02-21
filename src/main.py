"""FastAPI 애플리케이션 엔트리포인트"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.shared.database import init_database, close_database
from src.shared.vector_store import init_vector_store, close_vector_store, is_vector_store_available


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 생명주기 관리"""
    settings = get_settings()

    # 시작 시 초기화
    await init_database()
    await init_vector_store()

    # 서비스 상태 출력
    qdrant_status = "✅" if is_vector_store_available() else "❌"
    print(f"🚀 AI Memory Agent 시작 (환경: {settings.app_env})")
    print(f"   - SQLite: ✅")
    print(f"   - Qdrant: {qdrant_status}")

    yield

    # 종료 시 정리
    await close_database()
    await close_vector_store()

    print("👋 AI Memory Agent 종료")


def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    settings = get_settings()

    app = FastAPI(
        title="AI Memory Agent",
        description="멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    from src.user.router import router as user_router
    from src.memory.router import router as memory_router
    from src.chat.router import router as chat_router
    from src.permission.router import router as permission_router
    from src.auth.router import router as auth_router
    from src.websocket.router import router as websocket_router
    from src.admin.router import router as admin_router
    from src.document.router import router as document_router
    from src.share.router import router as share_router
    from src.agent.router import router as agent_router

    # REST API 라우터
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(memory_router, prefix="/api/v1/memories", tags=["memories"])
    app.include_router(chat_router, prefix="/api/v1/chat-rooms", tags=["chat-rooms"])
    app.include_router(permission_router, prefix="/api/v1/permissions", tags=["permissions"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(document_router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(share_router, prefix="/api/v1", tags=["shares"])
    app.include_router(agent_router, prefix="/api/v1", tags=["agents"])

    # WebSocket 라우터
    app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

    @app.get("/health")
    async def health_check():
        """헬스 체크"""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "services": {
                "database": True,  # SQLite는 항상 사용 가능
                "vector_store": is_vector_store_available(),
            }
        }

    # 프론트엔드 정적 파일 서빙 (빌드된 dist)
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    frontend_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
    if os.path.exists(frontend_dist):
        # API 라우트 이후에 마운트 (API 우선)
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="static-assets")
        
        # SPA fallback — 알려지지 않은 경로는 index.html로
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = os.path.join(frontend_dist, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )
