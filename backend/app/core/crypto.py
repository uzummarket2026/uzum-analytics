"""Maxfiy ma'lumotlarni (Uzum API token va b.) shifrlash/qaytarish.

Encryption kalit:
- ENCRYPTION_KEY env (urlsafe base64, 32 bayt) bo'lsa — shu ishlatiladi
- Yo'q bo'lsa — SECRET_KEY'dan SHA-256 orqali derive qilinadi

Format:
- Shifrlangan qiymat 'enc:v1:' prefix bilan saqlanadi
- Eski plaintext qiymatlar (prefix'siz) avtomatik tan olinadi va
  birinchi yozuvda shifrlangan formatga o'tadi
"""
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_PREFIX = "enc:v1:"


def _derive_key() -> bytes:
    if settings.ENCRYPTION_KEY:
        # Foydalanuvchi to'g'ri formatdagi kalit bergan bo'lsa
        try:
            raw = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY.encode())
            if len(raw) == 32:
                return settings.ENCRYPTION_KEY.encode()
        except Exception:
            pass
        # Aks holda string'ni hash qilamiz
        digest = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    # Fallback: SECRET_KEY'dan derive
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_key())


def encrypt(plaintext: Optional[str]) -> Optional[str]:
    if plaintext is None or plaintext == "":
        return plaintext
    if plaintext.startswith(_PREFIX):
        return plaintext  # allaqachon shifrlangan
    token = _fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
    return _PREFIX + token


def decrypt(value: Optional[str]) -> Optional[str]:
    """Shifrlangan qiymatni qaytaradi. Eski plaintext qiymatlar o'zicha qaytadi."""
    if value is None or value == "":
        return value
    if not value.startswith(_PREFIX):
        # Eski (shifrlanmagan) qiymat — orqaga moslik
        return value
    try:
        token = value[len(_PREFIX):].encode("ascii")
        return _fernet.decrypt(token).decode("utf-8")
    except InvalidToken:
        return None
