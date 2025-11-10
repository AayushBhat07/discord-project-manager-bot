from flask import Flask, request, jsonify
import hmac
import hashlib
import logging
import asyncio
from typing import Callable

logger = logging.getLogger(__name__)


class WebhookServer:
    """Flask server to receive GitHub webhooks"""
    
    def __init__(self, port: int, webhook_secret: str, webhook_handler: Callable):
        self.app = Flask(__name__)
        self.port = port
        self.webhook_secret = webhook_secret
        self.webhook_handler = webhook_handler
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register Flask routes"""
        
        @self.app.route('/webhook/github', methods=['POST'])
        def github_webhook():
            """Handle GitHub webhook POST requests"""
            
            # Verify signature
            if not self._verify_signature(request):
                logger.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 403
            
            # Get event type
            event_type = request.headers.get('X-GitHub-Event')
            
            if event_type != 'pull_request':
                return jsonify({'message': 'Event type not supported'}), 200
            
            # Parse payload
            payload = request.json
            
            # Check if PR was merged
            action = payload.get('action')
            pr_data = payload.get('pull_request', {})
            
            if action == 'closed' and pr_data.get('merged'):
                logger.info(f"PR #{pr_data.get('number')} was merged, triggering review")
                
                # Extract data
                repo_full_name = payload.get('repository', {}).get('full_name')
                pr_number = pr_data.get('number')
                
                # Trigger webhook handler asynchronously
                asyncio.create_task(
                    self.webhook_handler(repo_full_name, pr_number, payload)
                )
                
                return jsonify({'message': 'Webhook received, review queued'}), 200
            
            return jsonify({'message': 'PR not merged, skipping'}), 200
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({'status': 'ok'}), 200
    
    def _verify_signature(self, request) -> bool:
        """Verify GitHub webhook signature"""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True  # Allow if no secret configured (dev mode)
        
        signature_header = request.headers.get('X-Hub-Signature-256')
        if not signature_header:
            return False
        
        # Compute expected signature
        sha_name, signature = signature_header.split('=')
        if sha_name != 'sha256':
            return False
        
        mac = hmac.new(
            self.webhook_secret.encode(),
            msg=request.data,
            digestmod=hashlib.sha256
        )
        expected_signature = mac.hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def run(self):
        """Start the Flask server"""
        logger.info(f"Starting webhook server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)
