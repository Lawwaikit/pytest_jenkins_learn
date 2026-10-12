
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Hello from Jenkins deployed app!")

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Application listening on port 8000")
    server.serve_forever()
