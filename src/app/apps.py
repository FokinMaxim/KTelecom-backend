from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import src.app.internal.data.models
from src.config.database import engine, Base
from src.app.internal.presentation.api.user_controller import router as user_router
from src.app.internal.presentation.api.auth_controller  import router as auth_router
from src.app.internal.presentation.api.queue_controller  import router as queque_router
from src.app.internal.presentation.api.record_controller  import router as record_router
from src.app.internal.presentation.api.comment_controller  import router as comment_router
from src.app.internal.presentation.api.attachment_controller  import router as attachment_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="My API",
    description="API для управления пользователями",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(queque_router)
app.include_router(record_router)
app.include_router(comment_router)
app.include_router(attachment_router)