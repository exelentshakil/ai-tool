from flask import Blueprint, request, jsonify
from utils.tools_config import (
    ALL_TOOLS, get_tools_by_category, get_core_tools,
    search_tools, get_tool_statistics, get_similar_tools
)
tools_bp = Blueprint('tools', __name__)

# Fix the /tools endpoint to always return tools_array
@tools_bp.route('/tools', methods=['GET'])
def tools_endpoint():
    """Get core tools or filtered tools"""
    try:
        category = request.args.get('category', '').lower()
        search = request.args.get('search', '').lower()
        sort_by = request.args.get('sort', 'name')
        core_only = request.args.get('core_only', 'false').lower() == 'true'

        # Get all tools by default, not just core tools
        if core_only:
            tools_source = get_core_tools()
        else:
            tools_source = ALL_TOOLS

        # Always transform to array format for frontend
        tools = []
        for slug, tool_data in tools_source.items():
            title = tool_data.get('seo_data', {}).get('title', '')
            if not title:
                title = slug.replace('-', ' ').title()

            tool = {
                'slug': slug,
                'name': title,
                'description': tool_data.get('seo_data', {}).get('description', 'AI-powered calculator'),
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
            'success': True,
            'tools_array': tools,  # Frontend expects this key
            'total_count': len(tools),
            'categories': list(set(tool['category'] for tool in tools_source.values())),
            'filters': {
                'category': category,
                'search': search,
                'sort': sort_by,
                'core_only': core_only
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Add a simple endpoint that always returns all tools
@tools_bp.route('/all-tools', methods=['GET'])
def get_all_tools():
    """Get all tools without any filtering - for debugging"""
    try:
        tools = []
        for slug, tool_data in ALL_TOOLS.items():
            title = tool_data.get('seo_data', {}).get('title', slug.replace('-', ' ').title())

            tool = {
                'slug': slug,
                'name': title,
                'description': tool_data.get('seo_data', {}).get('description', 'AI-powered tool'),
                'category': tool_data.get('category', 'other'),
                'url': f'/{slug}'
            }
            tools.append(tool)

        return jsonify({
            'success': True,
            'tools': tools,
            'count': len(tools)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500