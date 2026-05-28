import base64
import json
from datetime import datetime
from typing import Optional
from uuid import UUID


def encode_cursor(imported_date: datetime, image_id: UUID) -> str:
    payload = json.dumps({"d": imported_date.isoformat(), "i": str(image_id)})
    return base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()


def decode_cursor(cursor: str) -> Optional[tuple[datetime, UUID]]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return datetime.fromisoformat(payload["d"]), UUID(payload["i"])
    except Exception:
        return None
