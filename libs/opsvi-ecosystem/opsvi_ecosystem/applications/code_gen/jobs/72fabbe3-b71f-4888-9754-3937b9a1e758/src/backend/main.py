import asyncio
import logging
import os

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel
from starlette.websockets import WebSocketState

from backend.alerts import alert_manager_task, get_active_alerts
from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
)
from backend.config import settings
from backend.db import engine, get_session
from backend.metrics import (
    get_historical_metrics,
    get_realtime_metrics,
    metrics_collector_task,
)
from backend.models import Threshold, User
from backend.schemas import (
    AlertRead,
    MetricSampleRead,
    MetricsHistoryQuery,
    ThresholdRead,
    ThresholdUpdate,
    Token,
    UserCreate,
    UserRead,
)
from backend.websocket_manager import WebSocketManager

app = FastAPI(
    title="System Monitoring Dashboard API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS Settings (allow frontend)
origins = settings.CORS_ALLOW_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for frontend build (if served from backend)
frontend_build_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.isdir(frontend_build_dir):
    app.mount(
        "/", StaticFiles(directory=frontend_build_dir, html=True), name="frontend"
    )

# Routers
api_router = APIRouter(prefix="/api")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    )


@app.on_event("startup")
def startup_event():
    setup_logging()
    SQLModel.metadata.create_all(engine)
    # Start metrics collector and alert manager
    asyncio.create_task(metrics_collector_task())
    asyncio.create_task(alert_manager_task())
    logging.getLogger(__name__).info(
        "Application started and background tasks running."
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


############### AUTH API #######################
@api_router.post("/token", response_model=Token, tags=["auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post("/users/", response_model=UserRead, tags=["auth"])
def register(user: UserCreate, db: Session = Depends(get_session)):
    # Only allow registering if no users exist (admin bootstrap)
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Registration is closed.")
    user_obj = User(
        username=user.username, hashed_password=get_password_hash(user.password)
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


############### METRICS API #######################


@api_router.get("/metrics/realtime", response_model=MetricSampleRead, tags=["metrics"])
def api_get_realtime_metrics(user: User = Depends(get_current_user)):
    return get_realtime_metrics()


@api_router.post(
    "/metrics/history", response_model=list[MetricSampleRead], tags=["metrics"]
)
def api_get_historical_metrics(
    query: MetricsHistoryQuery, user: User = Depends(get_current_user)
):
    return get_historical_metrics(query.metric_type, query.start_ts, query.end_ts)


############### THRESHOLD API ###################


@api_router.get("/thresholds", response_model=ThresholdRead, tags=["thresholds"])
def api_get_thresholds(
    user: User = Depends(get_current_user), db: Session = Depends(get_session)
):
    th = db.query(Threshold).first()
    if not th:
        th = Threshold()
        db.add(th)
        db.commit()
        db.refresh(th)
    return th


@api_router.put("/thresholds", response_model=ThresholdRead, tags=["thresholds"])
def api_update_thresholds(
    update: ThresholdUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    th = db.query(Threshold).first()
    if not th:
        th = Threshold()
    for field, value in update.dict(exclude_unset=True).items():
        setattr(th, field, value)
    db.add(th)
    db.commit()
    db.refresh(th)
    return th


############### ALERTS API ###################
@api_router.get("/alerts", response_model=list[AlertRead], tags=["alerts"])
def api_get_active_alerts(user: User = Depends(get_current_user)):
    return get_active_alerts()


app.include_router(api_router)

############### WEBSOCKET ENDPOINT ###################

ws_manager = WebSocketManager()


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket, token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token=token)
    await ws_manager.connect(websocket)
    try:
        while True:
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            await asyncio.sleep(30)  # Keep connection open
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logging.getLogger("websocket").error(f"WebSocket error: {exc}")
        ws_manager.disconnect(websocket)


# Custom error handler for 404 for API
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not found"})
