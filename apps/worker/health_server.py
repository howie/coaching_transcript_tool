"""
Simple HTTP server for Cloud Run health checks
Required because Cloud Run needs an HTTP endpoint for health monitoring
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "celery-worker",
                "port": os.environ.get("PORT", 8080),
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass


def start_health_server():
    """Start HTTP server for health checks"""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health server starting on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    start_health_server()
