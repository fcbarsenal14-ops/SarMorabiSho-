import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

ADMIN_TELEGRAM_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
    if x.strip().isdigit()
}

INITDATA_MAX_AGE = int(
    os.getenv("INITDATA_MAX_AGE", "86400")
)
