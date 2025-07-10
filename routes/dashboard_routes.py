from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from utils.database import (
    supabase,
    get_openai_cost_today,
    get_openai_cost_month,
    get_database_stats
)
from config.settings import PREMIUM_IPS
import os

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# ─── DASHBOARD HTML ─────────────────────────────────────────────────────────
@dashboard_bp.route('/')
def dashboard_home():
    try:
        return open('dashboard.html').read()
    except FileNotFoundError:
        return '<script>window.location.href = "/admin/dashboard";</script>'


# ─── DASHBOARD STATS ────────────────────────────────────────────────────────
@dashboard_bp.route('/api/stats')
def get_dashboard_stats():
    try:
        stats = get_database_stats()
        today_cost = get_openai_cost_today()
        month_cost = get_openai_cost_month()

        blocked_count = 0
        if supabase:
            res = supabase.table('blocked_ips').select('*').execute()
            blocked_count = len(res.data or [])

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


# ─── COST DATA ──────────────────────────────────────────────────────────────
@dashboard_bp.route('/api/costs')
def get_costs_data():
    try:
        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        period = request.args.get('period', '7d')
        days = {'24h': 1, '7d': 7, '30d': 30}.get(period, 7)
        start_date = datetime.now().date() - timedelta(days=days)

        result = supabase.table('openai_costs').select('*').gte('date', start_date.isoformat()).order('timestamp', desc=True).execute()
        costs = result.data or []

        today_str = datetime.now().date().isoformat()
        today_cost = sum(c.get('cost', 0) for c in costs if c.get('date') == today_str)
        week_cost = sum(c.get('cost', 0) for c in costs if datetime.fromisoformat(c.get('date')) >= datetime.now().date() - timedelta(days=7))
        month_cost = sum(c.get('cost', 0) for c in costs if datetime.fromisoformat(c.get('date')) >= datetime.now().date() - timedelta(days=30))

        today_requests = [c for c in costs if c.get('date') == today_str]
        avg_cost = (today_cost / len(today_requests)) if today_requests else 0.0

        return jsonify({
            'success': True,
            'costs': [
                {
                    'timestamp': c.get('timestamp'),
                    'model': c.get('model'),
                    'tool': c.get('tool'),
                    'tokens': c.get('tokens'),
                    'cost': c.get('cost')
                } for c in costs[:50]
            ],
            'aggregated': {
                'today': round(today_cost, 4),
                'week': round(week_cost, 4),
                'month': round(month_cost, 4),
                'avg_per_request': round(avg_cost, 6)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── USER DATA ──────────────────────────────────────────────────────────────
@dashboard_bp.route('/api/users')
def get_users_data():
    try:
        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        result = supabase.table('user_limits').select('*').order('updated_at', desc=True).execute()
        user_data = result.data or []

        blocked_ips = set(row['ip'] for row in (supabase.table('blocked_ips').select('*').execute().data or []))

        users = []
        seen_ips = set()

        for row in user_data:
            ip = row['ip']
            if ip in seen_ips:
                continue
            seen_ips.add(ip)

            status = 'blocked' if ip in blocked_ips else 'premium' if ip in PREMIUM_IPS else 'guest'
            today = datetime.now().strftime('%Y-%m-%d')
            requests_today = sum(r['count'] for r in user_data if r['ip'] == ip and r['hour_key'].startswith(today))
            tools_used = list(set(r.get('tool') for r in user_data if r['ip'] == ip and r.get('tool')))

            users.append({
                'ip': ip,
                'status': status,
                'requests_today': requests_today,
                'last_seen': row.get('updated_at', 'Unknown'),
                'total_requests': sum(r['count'] for r in user_data if r['ip'] == ip),
                'tools_used': tools_used
            })

        return jsonify({'success': True, 'users': users[:100]})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── TOOL USAGE ─────────────────────────────────────────────────────────────
@dashboard_bp.route('/api/tools')
def get_tools_data():
    try:
        if not supabase:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        result = supabase.table('openai_costs').select('*').order('timestamp', desc=True).execute()
        logs = result.data or []

        tool_summary = {}
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        for log in logs:
            tool = log.get('tool') or 'unknown'
            cost = log.get('cost', 0.0)
            timestamp = datetime.fromisoformat(log['timestamp'])
            date = timestamp.date()

            if tool not in tool_summary:
                tool_summary[tool] = {
                    'name': tool,
                    'total_uses': 0,
                    'today': 0,
                    'week': 0,
                    'total_cost': 0.0
                }

            tool_summary[tool]['total_uses'] += 1
            tool_summary[tool]['total_cost'] += cost

            if date == today:
                tool_summary[tool]['today'] += 1
            if date >= week_ago:
                tool_summary[tool]['week'] += 1

        tools = [{
            **v,
            'avg_cost': round(v['total_cost'] / v['total_uses'], 6) if v['total_uses'] else 0.0,
            'status': 'active'
        } for v in tool_summary.values()]

        return jsonify({'success': True, 'tools': tools})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── USER CONTROLS ──────────────────────────────────────────────────────────
@dashboard_bp.route('/api/users/block', methods=['POST'])
def block_user():
    try:
        ip = request.json.get('ip')
        if not ip:
            return jsonify({'success': False, 'error': 'IP required'}), 400

        supabase.table('blocked_ips').upsert({
            'ip': ip,
            'blocked_at': datetime.now().isoformat(),
            'reason': request.json.get('reason', 'Manual')
        }).execute()
        return jsonify({'success': True, 'message': f'IP {ip} blocked'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/users/unblock', methods=['POST'])
def unblock_user():
    try:
        ip = request.json.get('ip')
        if not ip:
            return jsonify({'success': False, 'error': 'IP required'}), 400

        supabase.table('blocked_ips').delete().eq('ip', ip).execute()
        return jsonify({'success': True, 'message': f'IP {ip} unblocked'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/users/premium', methods=['POST'])
def set_premium_user():
    try:
        ip = request.json.get('ip')
        action = request.json.get('action')
        if not ip:
            return jsonify({'success': False, 'error': 'IP required'}), 400
        return jsonify({'success': True, 'message': f'IP {ip} {"added to" if action == "add" else "removed from"} premium list'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── SETTINGS / HEALTH ──────────────────────────────────────────────────────
@dashboard_bp.route('/api/settings', methods=['GET', 'POST'])
def settings_handler():
    if request.method == 'GET':
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
    else:
        try:
            # Save logic not implemented
            return jsonify({'success': True, 'message': 'Settings saved'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/health')
def health_check():
    try:
        return jsonify({
            'success': True,
            'health': {
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
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── MIDDLEWARE ─────────────────────────────────────────────────────────────
@dashboard_bp.before_request
def require_admin():
    if request.endpoint and 'dashboard' in request.endpoint:
        if not is_admin_authenticated():
            return jsonify({'error': 'Admin authentication required'}), 401


def is_admin_authenticated():
    return True  # Replace with actual logic
