# utils/security.py

from flask import request, abort, jsonify
import re
from datetime import datetime, timedelta
import os


class SecurityManager:
    def __init__(self):
        self.blocked_ips = {
            '127.0.0.1',  # Add your problematic IP here
            # Add more IPs as needed
        }

        self.suspicious_patterns = [
            r'phpinfo\.php',
            r'wp-admin',
            r'wp-login',
            r'admin\.php',
            r'config\.php',
            r'\.env',
            r'backup\.sql',
            r'database\.sql',
            r'\.git/',
            r'\.svn/',
            r'shell\.php',
            r'webshell',
            r'eval\(',
            r'base64_decode',
            r'system\(',
            r'exec\(',
            r'passthru\(',
            r'<script',
            r'javascript:',
            r'union\s+select',
            r'drop\s+table',
            r'insert\s+into',
            r'delete\s+from',
        ]

        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]

        # Rate limiting for suspicious IPs
        self.suspicious_ips = {}
        self.suspicious_threshold = 5  # Max suspicious requests per hour
        self.block_duration = 24 * 60 * 60  # Block for 24 hours

        print("🛡️ Security Manager initialized")
        print(f"🚫 Currently blocking {len(self.blocked_ips)} IPs")
        print(f"🔍 Monitoring {len(self.suspicious_patterns)} suspicious patterns")

    def get_client_ip(self):
        """Get the real client IP address"""
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        return client_ip

    def is_suspicious_request(self, request_path, user_agent=''):
        """Check if the request matches suspicious patterns"""
        full_request = f"{request_path} {user_agent}"

        for pattern in self.compiled_patterns:
            if pattern.search(full_request):
                return True
        return False

    def log_suspicious_activity(self, ip, path, user_agent):
        """Log suspicious activity"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"🚨 SUSPICIOUS ACTIVITY: {timestamp} - IP: {ip} - Path: {path} - UA: {user_agent}"
        print(log_message)

        # Log to file
        try:
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            with open(os.path.join(log_dir, 'security.log'), 'a') as f:
                f.write(f"{timestamp} - SUSPICIOUS - IP: {ip} - Path: {path} - UA: {user_agent}\n")
        except Exception as e:
            print(f"Failed to write security log: {e}")

    def block_ip(self, ip):
        """Add IP to blocked list"""
        self.blocked_ips.add(ip)
        print(f"🔒 BLOCKED IP: {ip}")

        # Log the blocking
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            with open(os.path.join(log_dir, 'blocked_ips.log'), 'a') as f:
                f.write(f"{timestamp} - BLOCKED - IP: {ip}\n")
        except:
            pass

    def unblock_ip(self, ip):
        """Remove IP from blocked list"""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            print(f"🔓 UNBLOCKED IP: {ip}")
            return True
        return False

    def check_request_security(self):
        """Main security check function"""
        client_ip = self.get_client_ip()

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            print(f"🚫 BLOCKED REQUEST from {client_ip}")
            abort(403)

        # Check for suspicious patterns
        request_path = request.path
        user_agent = request.headers.get('User-Agent', '')

        if self.is_suspicious_request(request_path, user_agent):
            self.log_suspicious_activity(client_ip, request_path, user_agent)

            # Track suspicious activity from this IP
            now = datetime.now()
            if client_ip not in self.suspicious_ips:
                self.suspicious_ips[client_ip] = []

            # Clean old entries (older than 1 hour)
            self.suspicious_ips[client_ip] = [
                timestamp for timestamp in self.suspicious_ips[client_ip]
                if now - timestamp < timedelta(hours=1)
            ]

            # Add current suspicious request
            self.suspicious_ips[client_ip].append(now)

            # Block IP if too many suspicious requests
            if len(self.suspicious_ips[client_ip]) >= self.suspicious_threshold:
                self.block_ip(client_ip)
                abort(403)

            # Return 404 for suspicious requests to confuse attackers
            abort(404)

    def check_localhost_attacks(self):
        """Block localhost attacks trying to access web files"""
        client_ip = self.get_client_ip()

        # Block 127.0.0.1 trying to access web files
        if client_ip == '127.0.0.1' and any(pattern in request.path.lower() for pattern in
                                            ['php', 'html', 'www', 'var']):
            self.log_suspicious_activity(client_ip, request.path, request.headers.get('User-Agent', ''))
            self.block_ip(client_ip)
            abort(403)

    def cleanup_suspicious_ips(self):
        """Clean up old suspicious IP records"""
        now = datetime.now()
        for ip in list(self.suspicious_ips.keys()):
            self.suspicious_ips[ip] = [
                timestamp for timestamp in self.suspicious_ips[ip]
                if now - timestamp < timedelta(hours=1)
            ]
            if not self.suspicious_ips[ip]:
                del self.suspicious_ips[ip]

    def get_security_stats(self):
        """Get security statistics"""
        return {
            'blocked_ips': list(self.blocked_ips),
            'blocked_count': len(self.blocked_ips),
            'suspicious_ips': {
                ip: len(timestamps) for ip, timestamps in self.suspicious_ips.items()
            },
            'suspicious_count': len(self.suspicious_ips),
            'patterns_monitored': len(self.suspicious_patterns)
        }


# Global security manager instance
security_manager = SecurityManager()


def init_security(app):
    """Initialize security for Flask app"""

    @app.before_request
    def security_check():
        """Security middleware"""
        security_manager.check_localhost_attacks()
        security_manager.check_request_security()

    @app.after_request
    def add_security_headers(response):
        """Add security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        """Enhanced 404 handler"""
        client_ip = security_manager.get_client_ip()
        path = request.path
        user_agent = request.headers.get('User-Agent', '')

        # Log 404s that might be suspicious
        if security_manager.is_suspicious_request(path, user_agent):
            security_manager.log_suspicious_activity(client_ip, path, user_agent)

        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """Enhanced 403 handler"""
        return jsonify({
            'error': 'Access forbidden',
            'message': 'Your IP has been blocked due to suspicious activity'
        }), 403

    # Admin endpoints for IP management
    @app.route('/admin/security/block-ip', methods=['POST'])
    def block_ip_endpoint():
        """Manually block an IP address"""
        data = request.get_json()
        ip_to_block = data.get('ip')

        if not ip_to_block:
            return jsonify({'error': 'IP address required'}), 400

        security_manager.block_ip(ip_to_block)
        return jsonify({'message': f'IP {ip_to_block} blocked successfully'})

    @app.route('/admin/security/unblock-ip', methods=['POST'])
    def unblock_ip_endpoint():
        """Unblock an IP address"""
        data = request.get_json()
        ip_to_unblock = data.get('ip')

        if not ip_to_unblock:
            return jsonify({'error': 'IP address required'}), 400

        if security_manager.unblock_ip(ip_to_unblock):
            return jsonify({'message': f'IP {ip_to_unblock} unblocked successfully'})
        else:
            return jsonify({'error': f'IP {ip_to_unblock} was not blocked'}), 400

    @app.route('/admin/security/stats', methods=['GET'])
    def security_stats():
        """Get security statistics"""
        return jsonify(security_manager.get_security_stats())

    @app.route('/admin/security/cleanup', methods=['POST'])
    def cleanup_security():
        """Clean up old security records"""
        security_manager.cleanup_suspicious_ips()
        return jsonify({'message': 'Security cleanup completed'})

    print("🛡️ Security initialized successfully")
    return security_manager