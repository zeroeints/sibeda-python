from fastapi import FastAPI
import model.models as models
from routers import users as users_router, auth as auth_router, dinas as dinas_router
from routers import vehicle as vehicle_router, wallet as wallet_router
from database.database import SessionLocal, engine
from contextlib import asynccontextmanager
from middleware import RequestLoggingMiddleware, add_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist (development). In production, prefer migrations.
    models.Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: add cleanup if needed.

app = FastAPI(title="SIBEDA API", version="0.1.0", lifespan=lifespan)

# Register middleware
app.add_middleware(RequestLoggingMiddleware)

# Register global exception handlers
add_exception_handlers(app)

# Include modular routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(dinas_router.router)
app.include_router(vehicle_router.router)
app.include_router(wallet_router.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


## Legacy endpoints removed; now provided via routers.vehicle & routers.wallet