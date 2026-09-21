import hashlib
import hmac
import time
from urllib.parse import parse_qsl

from .config import BOT_TOKEN, INITDATA_MAX_AGE


def validate_telegram_init_data(init_data: str) -> dict:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not configured")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing Telegram hash")

    auth_date = int(pairs.get("auth_date", "0"))

    if auth_date <= 0 or time.time() - auth_date > INITDATA_MAX_AGE:
        raise ValueError("Expired Telegram initData")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(pairs.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    expected = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("Invalid Telegram initData")

    return pairs
