from flask import Blueprint, request, jsonify, render_template_string
from datetime import datetime, timedelta
from utils.database import (
    supabase,
    get_openai_cost_today,
    get_openai_cost_month,
    get_current_hour_users,
    get_database_stats
)
from config.settings import PREMIUM_IPS
import os

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


# ─── DASHBOARD HTML ─────────────────────────────────────────────────────────
@dashboard_bp.route('/')
def dashboard_home():
    """Serve the dashboard HTML"""
    try:
        # Read the dashboard HTML file or return the embedded HTML
        dashboard_html = open('dashboard.html', 'r').read()
        return dashboard_html
    except FileNotFoundError:
        # Return a simple redirect to the admin dashboard
        return '''
        <script>
        window.location.href = '/admin/dashboard';
        </script>
        '''


# ─── API ENDPOINTS ──────────────────────────────────────────────────────────
@dashboard_bp.route('/api/stats')
def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        stats = get_database_stats()
        today_cost = get_openai_cost_today()
        month_cost = get_openai_cost_month()

        # Get blocked IPs count
        blocked_count = 0
        if supabase:
            try:
                result = supabase.table('blocked_ips').select('*').execute()
                blocked_count = len(result.data) if result.data else 0
            except:
                blocked_count = 0

        return jsonify({
            'success': True,
            'stats': {
                'today_cost': round(today_cost, 4),
                'month_cost': round(month_cost, 4),
                'active_users': stats.get('current_hour_users', 0),
                'total_requests': stats.get('total_requests', 0),
                'blocked_ips': blocked_count,
                'total_users': stats.get('total_users', 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/costs')
def get_costs_data():
    """Get detailed costs data"""
    try:
        period = request.args.get('period', '7d')

        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        # Calculate date range
        if period == '24h':
            start_date = datetime.now().date()
        elif period == '7d':
            start_date = datetime.now().date() - timedelta(days=7)
        elif period == '30d':
            start_date = datetime.now().date() - timedelta(days=30)
        else:
            start_date = datetime.now().date() - timedelta(days=7)

        # Get costs from database
        result = supabase.table('openai_costs').select('*').gte('date', start_date.isoformat()).order('timestamp',
                                                                                                      desc=True).execute()

        costs = result.data if result.data else []

        # If no data found
        if not costs:
            return jsonify({
                'success': True,
                'costs': [],
                'aggregated': {
                    'today': 0,
                    'week': 0,
                    'month': 0,
                    'avg_per_request': 0
                },
                'message': 'No cost data found. Use populate button to add sample data.'
            })

        # Calculate aggregated stats with better error handling
        today_str = datetime.now().date().isoformat()
        week_ago = datetime.now().date() - timedelta(days=7)
        month_ago = datetime.now().date() - timedelta(days=30)

        today_cost = 0
        week_cost = 0
        month_cost = 0
        today_requests = 0

        for cost in costs:
            try:
                cost_date_str = cost.get('date', '')
                cost_amount = float(cost.get('cost', 0))

                # Parse date safely
                if cost_date_str:
                    # Handle different date formats
                    if 'T' in cost_date_str:
                        cost_date = datetime.fromisoformat(cost_date_str.split('T')[0]).date()
                    else:
                        cost_date = datetime.fromisoformat(cost_date_str).date()

                    # Today's costs
                    if cost_date_str == today_str:
                        today_cost += cost_amount
                        today_requests += 1

                    # This week's costs
                    if cost_date >= week_ago:
                        week_cost += cost_amount

                    # This month's costs
                    if cost_date >= month_ago:
                        month_cost += cost_amount

            except (ValueError, TypeError) as e:
                print(f"Error processing cost record: {e}")
                continue

        avg_cost = today_cost / max(1, today_requests)

        return jsonify({
            'success': True,
            'costs': costs[:50],  # Last 50 records
            'aggregated': {
                'today': round(today_cost, 4),
                'week': round(week_cost, 4),
                'month': round(month_cost, 4),
                'avg_per_request': round(avg_cost, 6)
            }
        })

    except Exception as e:
        print(f"Error in get_costs_data: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': str(e),
            'debug': 'Check server logs for details'
        }), 500

@dashboard_bp.route('/api/users')
def get_users_data():
    """Get user management data"""
    try:
        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        # Get user limits data
        result = supabase.table('user_limits').select('*').order('updated_at', desc=True).execute()
        user_data = result.data if result.data else []

        # Get blocked IPs
        blocked_result = supabase.table('blocked_ips').select('*').execute()
        blocked_ips = [row['ip'] for row in (blocked_result.data or [])]

        # Process user data
        users = []
        seen_ips = set()

        for row in user_data:
            ip = row['ip']
            if ip in seen_ips:
                continue
            seen_ips.add(ip)

            # Determine status
            if ip in blocked_ips:
                status = 'blocked'
            elif ip in PREMIUM_IPS:
                status = 'premium'
            else:
                status = 'guest'

            # Get today's requests
            today_requests = sum(r['count'] for r in user_data
                                 if r['ip'] == ip and r['hour_key'].startswith(datetime.now().strftime('%Y-%m-%d')))

            users.append({
                'ip': ip,
                'status': status,
                'requests_today': today_requests,
                'last_seen': row.get('updated_at', 'Unknown'),
                'total_requests': sum(r['count'] for r in user_data if r['ip'] == ip)
            })

        return jsonify({
            'success': True,
            'users': users[:100]  # Limit to 100 users
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/tools')
def get_tools_data():
    """Get tools usage statistics"""
    try:
        # This would need to be implemented based on your tools tracking
        # For now, return sample data
        tools = [
            {
                'name': 'Calculator',
                'total_uses': 1250,
                'today': 45,
                'week': 320,
                'avg_cost': 0.0034,
                'status': 'active'
            },
            {
                'name': 'Converter',
                'total_uses': 890,
                'today': 23,
                'week': 180,
                'avg_cost': 0.0028,
                'status': 'active'
            }
        ]

        return jsonify({
            'success': True,
            'tools': tools
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/users/block', methods=['POST'])
def block_user():
    """Block a user IP"""
    try:
        data = request.json
        ip = data.get('ip')

        if not ip:
            return jsonify({'success': False, 'error': 'IP address required'}), 400

        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        # Add to blocked IPs table
        result = supabase.table('blocked_ips').upsert({
            'ip': ip,
            'blocked_at': datetime.now().isoformat(),
            'reason': data.get('reason', 'Manual block')
        }).execute()

        return jsonify({'success': True, 'message': f'IP {ip} blocked successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/users/unblock', methods=['POST'])
def unblock_user():
    """Unblock a user IP"""
    try:
        data = request.json
        ip = data.get('ip')

        if not ip:
            return jsonify({'success': False, 'error': 'IP address required'}), 400

        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        # Remove from blocked IPs table
        result = supabase.table('blocked_ips').delete().eq('ip', ip).execute()

        return jsonify({'success': True, 'message': f'IP {ip} unblocked successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/users/premium', methods=['POST'])
def set_premium_user():
    """Set user as premium"""
    try:
        data = request.json
        ip = data.get('ip')
        action = data.get('action')  # 'add' or 'remove'

        if not ip:
            return jsonify({'success': False, 'error': 'IP address required'}), 400

        # This would need to update your premium IPs configuration
        # For now, just return success
        message = f'IP {ip} {"added to" if action == "add" else "removed from"} premium list'

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/settings')
def get_settings():
    """Get current settings"""
    try:
        settings = {
            'daily_budget': float(os.getenv('DAILY_OPENAI_BUDGET', '10.0')),
            'hourly_limit': int(os.getenv('HOURLY_FREE_LIMIT', '50')),
            'premium_ips': PREMIUM_IPS,
            'supabase_connected': supabase is not None,
            'openai_key_configured': bool(os.getenv('OPENAI_API_KEY'))
        }

        return jsonify({'success': True, 'settings': settings})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    try:
        data = request.json

        # In a real implementation, you'd update your configuration
        # For now, just return success

        return jsonify({'success': True, 'message': 'Settings updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/health')
def health_check():
    """Dashboard health check"""
    try:
        health = {
            'database': {
                'supabase': supabase is not None,
                'status': 'connected' if supabase else 'disconnected'
            },
            'apis': {
                'openai': bool(os.getenv('OPENAI_API_KEY')),
            },
            'system': {
                'uptime': 'Running',
                'last_check': datetime.now().isoformat()
            }
        }

        return jsonify({'success': True, 'health': health})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── UTILS ──────────────────────────────────────────────────────────────────
def is_admin_authenticated():
    """Check if user is authenticated as admin"""
    # Implement your admin authentication logic here
    # For now, return True (insecure - implement proper auth)
    return True


# Add authentication middleware if needed
@dashboard_bp.before_request
def require_admin():
    """Require admin authentication for all dashboard routes"""
    if request.endpoint and 'dashboard' in request.endpoint:
        if not is_admin_authenticated():
            return jsonify({'error': 'Admin authentication required'}), 401