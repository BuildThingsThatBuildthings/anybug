"""Serve the bundled viewer. Run 'python3 serve.py --lan' for home Wi-Fi."""

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


class ViewerHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        name = unquote(urlsplit(self.path).path).lstrip("/") or "index.html"
        path = (ROOT / name).resolve()
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            return self.send_error(404)
        allowed = rel.as_posix() in {"index.html", "specimens/catalog.json"}
        if rel.parts and rel.parts[0] in {"viewer", "vendor"}:
            allowed = all(not item.startswith(".") for item in rel.parts)
        if len(rel.parts) == 3 and rel.parts[0] == "specimens":
            allowed = rel.parts[1] in self.server.species and rel.name in {
                "anatomy.json",
                "specimen.glb",
            }
        if not allowed or not path.is_file():
            return self.send_error(404)
        return super().send_head()

    def list_directory(self, path):
        return self.send_error(404)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4179)
    parser.add_argument(
        "--lan", action="store_true", help="Listen on your local network"
    )
    args = parser.parse_args()
    host = "0.0.0.0" if args.lan else "127.0.0.1"
    with ThreadingHTTPServer(
        (host, args.port), partial(ViewerHandler, directory=str(ROOT))
    ) as server:
        server.species = {
            p["id"] for p in json.loads((ROOT / "specimens/catalog.json").read_text())
        }
        print(f"AnyBug is ready at http://127.0.0.1:{server.server_port}/", flush=True)
        if args.lan:
            print(
                "On the same Wi-Fi, open http://<computer local IP>:"
                + str(server.server_port)
                + "/",
                flush=True,
            )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
