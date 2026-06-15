from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time

from ..models.database import _get_client

_bearer = HTTPBearer()
_token_cache = {}


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    token_str = credentials.credentials
    now = time.time()

    # Verifica cache (TTL 5 minutos)
    if token_str in _token_cache:
        cached_sub, timestamp = _token_cache[token_str]
        if now - timestamp < 300:
            return {"sub": cached_sub}

    client = _get_client()
    try:
        res = client.auth.get_user(token_str)
        if not res or not res.user:
            raise ValueError("Invalid user")
        
        user_id = str(res.user.id)
        # Salva no cache
        _token_cache[token_str] = (user_id, now)
        
        return {"sub": user_id}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )
