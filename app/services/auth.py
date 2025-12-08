from google.auth.transport import requests
from google.oauth2 import id_token

from app.config import settings
from app.exceptions import AuthenticationError


def verify_google_token(token: str) -> str:
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.google_client_id
        )
        email = id_info.get("email")
        if not email:
            raise AuthenticationError("Email not found in token")
        return email
    except Exception as e:
        raise AuthenticationError(f"Token verification failed: {str(e)}")

