from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # Valores defaults atualizados e lógica para escolher URL correta
    # Em produção (Railway), use o host interno: postgres.railway.internal:5432
    # Em ambiente local, use a URL pública (proxy): gondola.proxy.rlwy.net:20145
    DATABASE_URL: str | None = None
    DATABASE_PUBLIC_URL: str | None = None

    JWT_SECRET: str = "a_very_secret_key_that_should_be_changed"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Railway environment detection
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Auto-detect Railway environment
        in_railway = bool(os.getenv("RAILWAY_ENVIRONMENT"))
        if in_railway:
            self.ENVIRONMENT = "production"
            self.PORT = int(os.getenv("PORT", 8000))

        # Resolver URL do banco
        db_url_env = os.getenv("DATABASE_URL") or self.DATABASE_URL
        public_url_env = os.getenv("DATABASE_PUBLIC_URL") or self.DATABASE_PUBLIC_URL

        if in_railway:
            # Preferir URL interna quando em Railway; fallback para pública se necessário
            resolved = db_url_env or public_url_env
        else:
            # Fora do Railway, preferir URL pública; fallback para interna se pública não existir
            resolved = public_url_env or db_url_env

        # Defaults caso nada esteja definido via env/.env
        if not resolved:
            if in_railway:
                # Host interno (sem proxy) - porta padrão 5432
                resolved = (
                    "postgresql://postgres:yjZJwfkbcNTlNUNQUjbHoRpUtVtGVkpQ@postgres.railway.internal:5432/railway"
                )
            else:
                # Host público (proxy) - porta exposta
                resolved = (
                    "postgresql://postgres:yjZJwfkbcNTlNUNQUjbHoRpUtVtGVkpQ@gondola.proxy.rlwy.net:20145/railway"
                )

        # Garantir driver asyncpg
        if resolved.startswith("postgresql://"):
            resolved = resolved.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.DATABASE_URL = resolved


settings = Settings()
