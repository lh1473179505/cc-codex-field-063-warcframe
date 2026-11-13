"""Draft WARC writer. Line endings and concurrency are wrong; see docs/warc.md."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def record_id() -> str:
    return "<urn:uuid:%s>" % uuid.uuid4()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class WarcWriter:
    def __init__(self, path: str):
        self.path = path
        self.fp = open(path, "ab")

    def write_record(self, typ: str, headers: dict, payload: bytes = b"") -> str:
        rid = headers.get("WARC-Record-ID") or record_id()
        headers = dict(headers)
        headers.setdefault("WARC-Record-ID", rid)
        headers.setdefault("WARC-Date", now())
        headers.setdefault("WARC-Type", typ)
        headers["Content-Length"] = str(len(payload))
        # BUG: uses \n instead of \r\n; no mutex
        lines = ["WARC/1.1"]
        for k, v in headers.items():
            if k == "Content-Length":
                continue
            lines.append(f"{k}: {v}")
        lines.append(f"Content-Length: {headers['Content-Length']}")
        head = "\n".join(lines) + "\n\n"
        self.fp.write(head.encode("utf-8") + payload + b"\n\n")
        self.fp.flush()
        return rid

    def close(self):
        self.fp.close()
