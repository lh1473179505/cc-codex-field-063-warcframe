from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

PAGES = {
    "/page/a": b"""<!doctype html><html><head><meta charset="utf-8"><title>A</title></head>
<body><h1>Page A</h1><p><a href="/page/b">b</a> <a href="/page/a">self</a></p></body></html>""",
    "/page/b": b"""<!doctype html><html><head><meta charset="utf-8"><title>B</title></head>
<body><h1>Page B</h1><p><a href="/page/a">a</a> <a href="/charset/mixed">mixed</a></p></body></html>""",
}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        return

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in PAGES:
            body = PAGES[path]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/charset/mixed":
            # UTF-8 BOM + utf-8 meta, but header claims latin-1
            body = b"\xef\xbb\xbf<!doctype html><html><head><meta charset=\"utf-8\"><title>Mix</title></head><body>caf\xc3\xa9</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=iso-8859-1")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/partial/stream":
            body = b"X" * 40
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", "400")  # lie, then close
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"missing")

def serve(host="127.0.0.1", port=8764):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"warcframe fixture site on http://{host}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    serve()
