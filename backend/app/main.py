from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .database import init_db
from .loader import load_csv


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Sensor Telemetry API")
    app.state.db_path = db_path
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        init_db(db_path)
        load_csv(db_path=db_path)

    app.include_router(router)
    return app


app = create_app()
