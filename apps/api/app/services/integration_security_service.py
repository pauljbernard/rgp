import base64
import hashlib
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.db.models import IntegrationTable

SECRET_SETTING_KEYS = {"api_key", "access_token"}


class IntegrationSecurityService:
    def _fernet(self) -> Fernet:
        secret = settings.integration_secret_key or settings.auth_token_secret
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    def encrypt_secret(self, value: str) -> str:
        if value.startswith("enc:"):
            return value
        token = self._fernet().encrypt(value.encode("utf-8")).decode("utf-8")
        return f"enc:{token}"

    def decrypt_secret(self, value: str | None) -> str | None:
        if not value:
            return None
        if not value.startswith("enc:"):
            return value
        try:
            return self._fernet().decrypt(value[4:].encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Stored integration secret could not be decrypted") from exc

    def prepare_settings_for_storage(
        self,
        existing: dict | None,
        updates: dict | None,
        *,
        clear_api_key: bool = False,
        clear_access_token: bool = False,
    ) -> dict:
        merged = dict(existing or {})
        for key, value in (updates or {}).items():
            if value in (None, ""):
                continue
            if key in SECRET_SETTING_KEYS:
                merged[key] = self.encrypt_secret(str(value))
            else:
                merged[key] = value
        if clear_api_key:
            merged.pop("api_key", None)
        if clear_access_token:
            merged.pop("access_token", None)
        return merged

    def sanitize_settings_for_response(self, settings_dict: dict | None) -> dict:
        sanitized = dict(settings_dict or {})
        for key in SECRET_SETTING_KEYS:
            sanitized.pop(key, None)
        return sanitized

    def has_secret(self, settings_dict: dict | None, key: str) -> bool:
        if key not in SECRET_SETTING_KEYS:
            return False
        return bool((settings_dict or {}).get(key))

    def setting(self, integration: IntegrationTable, key: str) -> str | None:
        raw = (integration.settings or {}).get(key)
        if key in SECRET_SETTING_KEYS:
            return self.decrypt_secret(raw if isinstance(raw, str) else None)
        if isinstance(raw, str):
            value = raw.strip()
            return value or None
        return raw if raw is not None else None

    def validate_outbound_target(self, url: str, *, allowed_hosts: list[str], allow_http_loopback: bool = False) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Integration URL must use http or https")
        if not parsed.hostname:
            raise ValueError("Integration URL must include a hostname")
        hostname = parsed.hostname.lower()
        if parsed.scheme == "http":
            is_loopback = hostname in {"localhost", "127.0.0.1"} or hostname.endswith(".localhost")
            if not (allow_http_loopback and is_loopback):
                raise ValueError("Plain HTTP is only allowed for localhost integrations")
        normalized = [item.lower() for item in allowed_hosts]
        if normalized and hostname not in normalized:
            raise ValueError(f"Outbound host {hostname} is not in the allowlist")
        return url.rstrip("/")


integration_security_service = IntegrationSecurityService()
