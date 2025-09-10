from datetime import datetime, timedelta, timezone
from jose import jwt
from werkzeug.security import check_password_hash, generate_password_hash
from app.core.config import settings


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha utilizando o mesmo esquema do cliente (Werkzeug PBKDF2, compatível com bcrypt se presente)."""
    try:
        return check_password_hash(hashed_password or "", plain_password or "")
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Gera hash PBKDF2 (padrão do Werkzeug)."""
    return generate_password_hash(password or "")
