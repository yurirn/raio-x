from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import settings
from app.routes import router

app = FastAPI(
    title="Raio X API", version="0.1.0", description="Backend do sistema operacional Raio X"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
