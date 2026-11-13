import argparse

def main(argv=None):
    p = argparse.ArgumentParser(prog="warcframe")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("site")
    s.add_argument("--port", type=int, default=8764)
    s.add_argument("--host", default="127.0.0.1")
    c = sub.add_parser("capture")
    c.add_argument("--base", required=True)
    c.add_argument("--seeds", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--workers", type=int, default=3)
    v = sub.add_parser("verify")
    v.add_argument("--warc", required=True)
    v.add_argument("--expect", required=True)
    args = p.parse_args(argv)
    if args.cmd == "site":
        from warcframe.site import serve
        serve(args.host, args.port)
        return 0
    if args.cmd == "capture":
        from warcframe.capture import run_capture
        return run_capture(args)
    if args.cmd == "verify":
        from warcframe.verify import run_verify
        return run_verify(args)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
