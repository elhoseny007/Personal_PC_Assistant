
import json
import secrets
from pathlib import Path

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# =========================
# Configuration
# =========================

BASE_DIR = Path(__file__).parent

CLIENT_SECRET_FILE = BASE_DIR / "secrets" / "client_secret_616614253236-2090chq1hmjibno31oae33nui3ajtfnf.apps.googleusercontent.com.json"
TOKEN_FILE = BASE_DIR / "secrets" / "token.json"

REDIRECT_URI = (
    "http://127.0.0.1:8000/api/google-drive/callback"
)

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]

# Single-user local application
_oauth_state = None
_oauth_code_verifier = None

# =========================
# OAuth Authentication
# =========================

def create_oauth_flow(state=None, code_verifier=None):
    if not CLIENT_SECRET_FILE.exists():
        raise FileNotFoundError(
            f"OAuth credentials not found: {CLIENT_SECRET_FILE}"
        )

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
    )

    flow.redirect_uri = REDIRECT_URI

    return flow


def get_authorization_url():
    global _oauth_state, _oauth_code_verifier

    _oauth_state = secrets.token_urlsafe(32)
    _oauth_code_verifier = secrets.token_urlsafe(64)

    flow = create_oauth_flow(
        state=_oauth_state,
        code_verifier=_oauth_code_verifier,
    )

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return authorization_url

def complete_oauth(code, state):
    global _oauth_state, _oauth_code_verifier

    if not _oauth_state or not secrets.compare_digest(
        state or "", _oauth_state
    ):
        raise ValueError("Invalid or expired OAuth state.")

    if not _oauth_code_verifier:
        raise ValueError("Missing OAuth code verifier.")

    flow = create_oauth_flow(
        state=_oauth_state,
        code_verifier=_oauth_code_verifier,
    )

    flow.fetch_token(code=code)

    credentials = flow.credentials

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    _oauth_state = None
    _oauth_code_verifier = None

    return True


# =========================
# Credentials
# =========================

def get_credentials():
    if not TOKEN_FILE.exists():
        return None

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    if not credentials.valid:
        return None

    return credentials


# =========================
# Google Drive Service
# =========================

def get_drive_service():
    credentials = get_credentials()

    if credentials is None:
        raise RuntimeError(
            "Google Drive is not connected. Please sign in first."
        )

    return build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def is_google_drive_connected():
    try:
        return get_credentials() is not None
    except Exception:
        return False
