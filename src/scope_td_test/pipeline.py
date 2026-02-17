import torch
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from scope.core.pipelines.base_pipeline import BasePipeline
from .schema import TDTestConfig


class TDTestPipeline(BasePipeline):
    """Minimal test pipeline that receives HTTP messages from TouchDesigner."""

    config_class = TDTestConfig

    def __init__(self, config: TDTestConfig):
        super().__init__(config)
        self.config = config

        # Current message from TouchDesigner
        self.current_message = config.message

        # Start HTTP server in background thread
        self.server_thread = None
        self.start_http_server()

    def start_http_server(self):
        """Start Flask HTTP server in background thread."""
        app = Flask(__name__)
        CORS(app)  # Allow requests from anywhere

        @app.route('/message', methods=['POST'])
        def receive_message():
            """Receive message from TouchDesigner."""
            try:
                data = request.get_json()
                message = data.get('message', 'No message')

                # Update current message
                self.current_message = message

                # Print to Scope console so you can see it worked!
                print(f"✅ RECEIVED FROM TOUCHDESIGNER: {message}")

                return jsonify({
                    'status': 'success',
                    'received': message
                }), 200

            except Exception as e:
                print(f"❌ Error receiving message: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 400

        @app.route('/ping', methods=['GET'])
        def ping():
            """Simple ping endpoint to test if server is running."""
            return jsonify({
                'status': 'alive',
                'current_message': self.current_message
            }), 200

        # Run server in background thread
        def run_server():
            app.run(host='0.0.0.0', port=self.config.http_port, debug=False, use_reloader=False)

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
