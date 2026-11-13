def run_capture(args) -> int:
    raise NotImplementedError(
        "capture is not implemented. Fix WarcWriter (CRLF + mutex), write warcinfo, "
        "request/response pairs, revisits, charset identified-type, and truncated records."
    )
