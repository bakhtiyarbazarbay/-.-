from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Google Antigravity"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Секретный ключ для JWT
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Заглушка
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 дней
    
    # База данных
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "antigravity"
    DATABASE_URL: str | None = None
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            # SQLAlchemy asyncpg requires 'postgresql+asyncpg://'
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
