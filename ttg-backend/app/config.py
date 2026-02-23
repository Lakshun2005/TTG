from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ttg.db"
    secret_key: str = "supersecretkey"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
