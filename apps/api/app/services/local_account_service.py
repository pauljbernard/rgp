import base64
import hashlib
import hmac
import os


class LocalAccountService:
    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
        return f"pbkdf2_sha256$600000${base64.b64encode(salt).decode('ascii')}${base64.b64encode(derived).decode('ascii')}"

    def verify_password(self, password: str, encoded: str | None) -> bool:
        if not encoded:
            return False
        try:
            algorithm, rounds, salt_b64, digest_b64 = encoded.split("$", 3)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt_b64.encode("ascii")),
            int(rounds),
        )
        return hmac.compare_digest(derived, base64.b64decode(digest_b64.encode("ascii")))


local_account_service = LocalAccountService()
