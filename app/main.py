"""FastAPI 엔트리포인트.

애플리케이션 생성, 미들웨어 설정, 라우터 등록을 수행함.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.settings import get_settings

# structlog 설정
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """FastAPI 애플리케이션을 생성함."""
    settings = get_settings()

    app = FastAPI(
        title="고객센터 운영 비용 최적화 에이전트",
        description=(
            "FAQ 자동 응답으로 상담원 투입 건수를 최소화하고, "
            "처리 건수 대비 운영 비용을 지속적으로 낮추는 비용 절감 에이전트"
        ),
        version="0.1.0",
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(router)

    @app.on_event("startup")
    async def startup_event():
        logger.info(
            "애플리케이션 시작",
            env=settings.app_env,
            use_mock=settings.use_mock,
        )

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("애플리케이션 종료")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_env == "development"),
    )
