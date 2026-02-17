import torch
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from scope.core.pipelines.base_pipeline import BasePipeline
from .schema import TDTestConfig


class TDRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for TouchDesigner communication."""

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/message':
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))

                message = data.get('message', 'No message')

                # Update pipeline's current message
                self.server.pipeline.current_message = message

                # Print to Scope console
                print(f"✅ RECEIVED FROM TOUCHDESIGNER: {message}")

                # Send response
                response = json.dumps({
                    'status': 'success',
                    'received': message
                })
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))

            except Exception as e:
                print(f"❌ Error: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'status': 'error', 'message': str(e)})
                self.wfile.write(error_response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/ping':
            response = json.dumps({
                'status': 'alive',
                'current_message': self.server.pipeline.current_message
            })
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class TDTestPipeline(BasePipeline):
    """Minimal test pipeline that receives HTTP messages from TouchDesigner."""

    config_class = TDTestConfig

    def __init__(self, config: TDTestConfig):
        super().__init__(config)
        self.config = config

        # Current message from TouchDesigner
        self.current_message = config.message

        # Start HTTP server in background thread
        self.http_server = None
        self.server_thread = None
        self.start_http_server()

    def start_http_server(self):
        """Start HTTP server in background thread using built-in http.server."""
        def run_server():
            self.http_server = HTTPServer(('0.0.0.0', self.config.http_port), TDRequestHandler)
            self.http_server.pipeline = self  # Pass pipeline instance to handler
            self.http_server.serve_forever()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        print(f"🚀 TD Test HTTP server started on port {self.config.http_port}")
        print(f"   Test with: curl -X POST http://localhost:{self.config.http_port}/message -H 'Content-Type: application/json' -d '{{\"message\": \"Hello from curl!\"}}'")

    def __call__(self, **kwargs) -> dict:
        """Render the current message as text on screen."""
        # Get frame dimensions from kwargs or use defaults
        height = kwargs.get("height", 512)
        width = kwargs.get("width", 512)

        # Create image
        img = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(img)

        # Use default font (simple for testing)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except:
            font = ImageFont.load_default()

        # Draw message in center
        text = self.current_message
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        draw.text((x, y), text, fill='white', font=font)

        # Convert to tensor [T, H, W, C] format
        frame = np.array(img).astype(np.float32) / 255.0
        tensor = torch.from_numpy(frame).unsqueeze(0)  # Add time dimension

        return {"frames": tensor}
