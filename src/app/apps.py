from fastapi import FastAPI
from src.config.database import engine, Base
from src.app.internal.presentation.api.user_controller import router as user_router
from src.app.internal.presentation.api.auth_controller  import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="My API",
    description="API для управления пользователями",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(user_router)
app.include_router(auth_router)