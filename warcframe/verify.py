from __future__ import annotations
import json, re, hashlib
from pathlib import Path

def parse_warc(data: bytes):
    if b"\r\nWARC/" not in data and not data.startswith(b"WARC/"):
        # still try CRLF split
        pass
    recs = []
    if not data.startswith(b"WARC/"):
        raise ValueError("file does not start with WARC/")
    parts = re.split(br"\r\n\r\n", data, maxsplit=0)
    # proper parse: records separated by CRLF CRLF after payload
    i = 0
    while i < len(data):
        if data[i:i+5] != b"WARC/" and i != 0:
            # skip leftover newlines
            if data[i:i+2] == b"\r\n":
                i += 2
                continue
            raise ValueError(f"junk or interleaved bytes at {i}")
        # find header end
        end = data.find(b"\r\n\r\n", i)
        if end < 0:
            raise ValueError("unterminated header")
        header = data[i:end].decode("utf-8", errors="replace")
        fields = {}
        first, *rest = header.split("\r\n")
        if not first.startswith("WARC/"):
            raise ValueError("bad version line: " + first)
        for line in rest:
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        n = int(fields.get("Content-Length", "0"))
        start = end + 4
        payload = data[start:start+n]
        if len(payload) != n:
            raise ValueError("short payload")
        recs.append({"headers": fields, "payload": payload, "version": first})
        i = start + n
        if data[i:i+4] == b"\r\n\r\n":
            i += 4
        elif data[i:i+2] == b"\r\n":
            i += 2
        elif i < len(data) and data[i:i+5] != b"WARC/":
            raise ValueError(f"missing record separator at {i}")
    return recs

def run_verify(args) -> int:
    data = Path(args.warc).read_bytes()
    expect = json.loads(Path(args.expect).read_text())
    errors = []
    try:
        recs = parse_warc(data)
    except Exception as e:
        print("verify failed: cannot parse warc:", e)
        return 1
    if not recs or recs[0]["headers"].get("WARC-Type") != "warcinfo":
        errors.append("first record must be warcinfo")
    types = [r["headers"].get("WARC-Type") for r in recs]
    uris = [r["headers"].get("WARC-Target-URI", "") for r in recs]
    def has_uri_type(frag, typ):
        return any(typ == t and frag in (u or "") for t,u in zip(types, uris))
    for frag, typ in expect.get("must_have", []):
        if not has_uri_type(frag, typ):
            errors.append(f"missing {typ} for {frag}")
    # charset
    mixed = [r for r in recs if "/charset/mixed" in (r["headers"].get("WARC-Target-URI") or "") and r["headers"].get("WARC-Type")=="response"]
    if not mixed:
        errors.append("missing charset/mixed response")
    else:
        ident = mixed[0]["headers"].get("WARC-Identified-Payload-Type", "")
        if "charset=utf-8" not in ident.replace(" ", "").lower() and "charset=utf-8" not in ident.lower():
            errors.append(f"charset mixed identified type {ident!r}")
    trunc = [r for r in recs if "/partial/stream" in (r["headers"].get("WARC-Target-URI") or "") and r["headers"].get("WARC-Type")=="response"]
    if not trunc:
        errors.append("missing partial/stream response")
    elif trunc[0]["headers"].get("WARC-Truncated") != "disconnect":
        errors.append(f"partial truncated {trunc[0]['headers'].get('WARC-Truncated')!r}")
    revisits = [r for r in recs if r["headers"].get("WARC-Type")=="revisit"]
    if expect.get("require_revisit_for"):
        frag = expect["require_revisit_for"]
        if not any(frag in (r["headers"].get("WARC-Target-URI") or "") for r in revisits):
            errors.append(f"missing revisit for {frag}")
        else:
            rv = next(r for r in revisits if frag in (r["headers"].get("WARC-Target-URI") or ""))
            digest = rv["headers"].get("WARC-Payload-Digest", "")
            if not digest.startswith("sha256:"):
                errors.append(f"revisit digest {digest!r}")
            first = next((r for r in recs if r["headers"].get("WARC-Type")=="response" and frag in (r["headers"].get("WARC-Target-URI") or "")), None)
            if first:
                exp = "sha256:" + hashlib.sha256(first["payload"].split(b"\r\n\r\n",1)[-1] if False else _http_body(first["payload"])).hexdigest()
                # payload is HTTP headers + body; digest is of HTTP response body only? docs say 响应正文
                # we'll compare against HTTP body if present, else whole payload — expected written accordingly
                body = _http_body(first["payload"])
                exp = "sha256:" + hashlib.sha256(body).hexdigest()
                if digest != exp:
                    # also allow digest of full payload in case implementer hashed the block
                    exp2 = "sha256:" + hashlib.sha256(first["payload"]).hexdigest()
                    if digest not in {exp, exp2}:
                        errors.append("revisit digest does not match first response body")
    if errors:
        print("verify failed:")
        for e in errors:
            print(" -", e)
        return 1
    print("verify ok")
    return 0

def _http_body(payload: bytes) -> bytes:
    if b"\r\n\r\n" in payload:
        return payload.split(b"\r\n\r\n", 1)[1]
    if b"\n\n" in payload:
        return payload.split(b"\n\n", 1)[1]
    return payload
