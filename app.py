#!/usr/bin/env python3
"""Tiny static file server for local testing.

GitHub Pages serves these files as-is; this is only so you can open the study
locally (file:// can't fetch pairs.json or load videos reliably).

    python app.py            # serves http://localhost:8000
    python app.py --port 9000
"""
import argparse
import functools
import http.server
import socketserver


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description="Serve the study locally.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()

    handler = functools.partial(NoCacheHandler)
    with socketserver.TCPServer((args.bind, args.port), handler) as httpd:
        print(f"Serving on http://{args.bind}:{args.port}  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
