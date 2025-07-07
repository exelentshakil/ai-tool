from flask import Blueprint, request, jsonify
from utils.tools_config import (
    ALL_TOOLS, get_tools_by_category, get_core_tools,
    search_tools, get_tool_statistics, get_similar_tools
)
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/list-tools', methods=['GET'])
def list_tools():
    """List available tools with filtering and search"""
    try:
        category = request.args.get('category', '').lower()
        search_query = request.args.get('search', '').lower()
        sort_by = request.args.get('sort', 'name')
        limit = int(request.args.get('limit', 50))

        tools = []

        # Apply search if provided
        if search_query:
            search_results = search_tools(search_query, category if category != 'all' else None)
            tools = search_results[:limit]
        else:
            # Filter by category if specified
            if category and category != 'all':
                filtered_tools = get_tools_by_category(category)
            else:
                filtered_tools = ALL_TOOLS

            # Convert to list format
            for slug, tool_data in filtered_tools.items():
                tool = {
                    'slug': slug,
                    'name': tool_data.get('seo_data', {}).get('title', slug.replace('-', ' ').title()),
                    'description': tool_data.get('seo_data', {}).get('description', 'AI-powered analysis tool'),
                    'category': tool_data.get('category', 'other'),
                    'rpm': tool_data.get('rpm', 25),
                    'keywords': tool_data.get('seo_data', {}).get('keywords', ''),
                    'url': f'/{slug}',
                    'base_name': tool_data.get('base_name', ''),
                    'focus_keyword': tool_data.get('seo_data', {}).get('focus_keyword', '')
                }
                tools.append(tool)

            # Apply limit
            tools = tools[:limit]

        # Sort tools
        if sort_by == 'rpm':
            tools.sort(key=lambda x: x.get('rpm', 0), reverse=True)
        elif sort_by == 'category':
            tools.sort(key=lambda x: (x['category'], x['name']))
        else:  # default to name
            tools.sort(key=lambda x: x['name'])

        return jsonify({
            'tools': tools,
            'total_count': len(tools),
            'categories': list(set(tool['category'] for tool in ALL_TOOLS.values())),
            'filters': {
                'category': category,
                'search': search_query,
                'sort': sort_by,
                'limit': limit
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tools_bp.route('/tools', methods=['GET'])
def tools_endpoint():
    """Get core tools or filtered tools"""
    try:
        category = request.args.get('category', '').lower()
        search = request.args.get('search', '').lower()
        sort_by = request.args.get('sort', 'name')
        core_only = request.args.get('core_only', 'true').lower() == 'true'

        if core_only:
            # Get one main tool per category
            tools_source = get_core_tools()
        else:
            # Get all tools
            tools_source = ALL_TOOLS

        # Transform to array format for frontend
        tools = []
        for slug, tool_data in tools_source.items():
            # Create clean title
            title = tool_data.get('seo_data', {}).get('title', '')
            if not title:
                title = slug.replace('-', ' ').title()

            tool = {
                'slug': slug,
                'name': title,
                'description': tool_data.get('seo_data', {}).get('description',
                                                                 'AI-powered calculator with instant results'),
                'category': tool_data.get('category', 'other'),
                'rpm': tool_data.get('rpm', 25),
                'keywords': tool_data.get('seo_data', {}).get('keywords', ''),
                'url': f'/{slug}',
                'base_name': tool_data.get('base_name', ''),
                'focus_keyword': tool_data.get('seo_data', {}).get('focus_keyword', ''),
                'is_core_tool': core_only
            }
            tools.append(tool)

        # Filter by category if specified
        if category and category != 'all':
            tools = [t for t in tools if t['category'] == category]

        # Filter by search if specified
        if search:
            tools = [t for t in tools if
                     search in t['name'].lower() or
                     search in t['description'].lower() or
                     search in t['keywords'].lower() or
                     search in t['category'].lower()]

        # Sort tools
        if sort_by == 'rpm':
            tools.sort(key=lambda x: x['rpm'], reverse=True)
        elif sort_by == 'category':
            tools.sort(key=lambda x: (x['category'], x['name']))
        else:  # default to name
            tools.sort(key=lambda x: x['name'])

        return jsonify({
            'all_tools': tools_source,
            'tools_array': tools,
            'total_count': len(tools_source),
            'core_tools_count': len(get_core_tools()) if not core_only else len(tools_source),
            'total_variants': len(ALL_TOOLS),
            'categories': list(set(tool['category'] for tool in tools_source.values())),
            'is_core_only': core_only,
            'filters': {
                'category': category,
                'search': search,
                'sort': sort_by,
                'core_only': core_only
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tools_bp.route('/tool/<slug>', methods=['GET'])
def get_tool_details(slug):
    """Get detailed information about a specific tool"""
    try:
        tool_config = ALL_TOOLS.get(slug)
        if not tool_config:
            return jsonify({'error': f'Tool "{slug}" not found'}), 404

        # Get similar tools
        similar_tools = get_similar_tools(slug, limit=5)

        return jsonify({
            'tool': tool_config,
            'similar_tools': similar_tools,
            'stats': {
                'category_count': len(get_tools_by_category(tool_config.get('category', ''))),
                'total_tools': len(ALL_TOOLS)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tools_bp.route('/tools/stats', methods=['GET'])
def get_tools_stats():
    """Get comprehensive statistics about tools"""
    try:
        stats = get_tool_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tools_bp.route('/tools/categories', methods=['GET'])
def get_categories():
    """Get all available categories with tool counts"""
    try:
        categories = {}
        for tool_data in ALL_TOOLS.values():
            category = tool_data.get('category', 'other')
            categories[category] = categories.get(category, 0) + 1

        return jsonify({
            'categories': categories,
            'total_categories': len(categories),
            'total_tools': len(ALL_TOOLS)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tools_bp.route('/tools/search', methods=['GET'])
def search_tools_endpoint():
    """Advanced search endpoint for tools"""
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '')
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        results = search_tools(query, category if category else None)

        return jsonify({
            'query': query,
            'category': category,
            'results': results[:limit],
            'total_results': len(results),
            'suggestions': get_search_suggestions(query)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tools_bp.route('/check-limits', methods=['GET'])
def check_limits():
    """Check user rate limits"""
    try:
        ip = get_remote_address()
        limit_check = check_user_limit(ip, is_premium_user(ip))

        return jsonify({
            "ip_address": ip,
            "current_hour_usage": limit_check.get("usage_count", 0),
            "hourly_limit": limit_check.get("limit", 0),
            "remaining_requests": limit_check.get("remaining", 0),
            "is_premium": is_premium_user(ip),
            "rate_limit_message": limit_check.get("message") if limit_check.get("blocked") else None,
            "limit_info": limit_check
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_search_suggestions(query):
    """Get search suggestions based on query"""
    suggestions = []
    query_lower = query.lower()

    # Get suggestions from tool names and keywords
    for tool_data in ALL_TOOLS.values():
        title = tool_data.get('seo_data', {}).get('title', '')
        keywords = tool_data.get('seo_data', {}).get('keywords', '')

        # Split and check keywords
        for keyword in keywords.split(','):
            keyword = keyword.strip().lower()
            if keyword and query_lower in keyword and keyword not in suggestions:
                suggestions.append(keyword)
                if len(suggestions) >= 5:
                    break

        if len(suggestions) >= 5:
            break

    return suggestions