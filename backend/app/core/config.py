from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LM Studio (local LLM) - no API key required
    lm_studio_base_url: str = "http://localhost:1234/v1"

    # Spotify OAuth
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/callback"

    # Frontend (for OAuth callback redirect) - use localhost to match Vite dev server
    frontend_url: str = "http://localhost:5173"

    # CORS allowed origins (comma-separated)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Database
    database_url: str = "sqlite:///./tempo_tailor.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
