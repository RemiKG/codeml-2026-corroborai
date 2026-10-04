"""Loopback-only local UI. Start with: python app.py --port 8114."""
from __future__ import annotations
import argparse
import base64
import json
import secrets
import threading
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from corroborai.demo import make_files
from corroborai.engine import reconcile
from corroborai.io import InputError, csv_bytes, xlsx_bytes

HTML = Path(__file__).with_name("ui") / "index.html"


def serve(port=8114):
    token = secrets.token_urlsafe(24)
    runs = OrderedDict()
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No employee values or arbitrary request paths in logs.

        def send(self, code, content, kind="application/json; charset=utf-8", filename=None):
            if not isinstance(content, bytes):
                content = json.dumps(content, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(content)

        def allowed_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def do_GET(self):
            if not self.allowed_host():
                return self.send(403, {"error": "Local host required."})
            path = urlsplit(self.path).path
            if path == "/":
                return self.send(200, HTML.read_text(encoding="utf-8").replace("__TOKEN__", token).encode("utf-8"), "text/html; charset=utf-8")
            if path == "/api/health":
                return self.send(200, {"status": "ok", "mode": "local-only"})
            if path.startswith("/api/download/"):
                name = path.rsplit("/", 1)[-1]
                runid, _, extension = name.partition(".")
                with lock:
                    run = runs.get(runid)
                if not run or extension not in ("csv", "xlsx"):
                    return self.send(404, {"error": "Run not found; compare again."})
                payload = csv_bytes(run) if extension == "csv" else xlsx_bytes(run)
                kind = "text/csv; charset=utf-8" if extension == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                return self.send(200, payload, kind, "corroboration." + extension)
            return self.send(404, {"error": "Not found."})

        def do_POST(self):
            if not self.allowed_host() or self.headers.get("X-Corroborai-Token") != token:
                return self.send(403, {"error": "Reload the local page before comparing."})
            origin = self.headers.get("Origin")
            if origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
                return self.send(403, {"error": "Local origin required."})
            path = urlsplit(self.path).path
            if path not in ("/api/compare", "/api/demo"):
                return self.send(404, {"error": "Not found."})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 40_000_000:
                    raise InputError("Request must be nonempty and at most 40 MB.")
                request = json.loads(self.rfile.read(size))
                if path == "/api/demo":
                    files = make_files()
                else:
                    files = {k: (Path(v["name"].replace("\\", "/")).name, base64.b64decode(v["base64"], validate=True)) for k, v in request["files"].items()}
                with lock:  # One bounded computation at a time.
                    run = reconcile(files, prefixes=request.get("prefixes", ["dev-08-v2_"]), as_of=request.get("reference_date") or None)
                    runid = secrets.token_hex(12)
                    runs[runid] = run
                    while len(runs) > 3:
                        runs.popitem(last=False)
                return self.send(200, {"run_id": runid, **run})
            except (InputError, ValueError, KeyError, TypeError) as exc:
                message = str(exc) if isinstance(exc, InputError) else "Malformed request; supply the five XLSX files."
                return self.send(400, {"error": message})
            except Exception:
                return self.send(500, {"error": "Unexpected local processing error. No result was produced; inspect inputs with the CLI."})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"CorroborAI local UI: http://127.0.0.1:{port} (no browser opened)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8114)
    serve(parser.parse_args().port)
