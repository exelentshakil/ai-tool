# routes/tools_api_routes.py
from flask import Blueprint, request, jsonify, current_app
from utils.tools_config import ALL_TOOLS
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user
import math

tools_api_bp = Blueprint('tools_api', __name__, url_prefix='/api/tools')


@tools_api_bp.route('/all', methods=['GET'])
def get_all_tools():
    """Get all tools with pagination and filtering"""
    try:
        # Debug: Print ALL_TOOLS info
        current_app.logger.info(f"ALL_TOOLS type: {type(ALL_TOOLS)}")
        current_app.logger.info(f"ALL_TOOLS keys count: {len(ALL_TOOLS) if ALL_TOOLS else 0}")
        current_app.logger.info(f"First few keys: {list(ALL_TOOLS.keys())[:5] if ALL_TOOLS else 'None'}")

        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        category = request.args.get('category', '').lower()
        search = request.args.get('search', '').lower()
        sort_by = request.args.get('sort', 'name')

        # Ensure ALL_TOOLS exists and is not empty
        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found',
                'debug_info': {
                    'ALL_TOOLS_type': str(type(ALL_TOOLS)),
                    'ALL_TOOLS_length': len(ALL_TOOLS) if ALL_TOOLS else 0
                }
            }), 500

        # Convert ALL_TOOLS dict to list
        tools_list = []
        for slug, tool_data in ALL_TOOLS.items():
            try:
                # Extract tool information safely
                seo_data = tool_data.get('seo_data', {}) if isinstance(tool_data, dict) else {}
                title = seo_data.get('title', slug.replace('-', ' ').title())
                description = seo_data.get('description', 'AI-powered calculator and analysis tool')
                keywords = seo_data.get('keywords', '')
                category_name = tool_data.get('category', 'other') if isinstance(tool_data, dict) else 'other'

                tool = {
                    'slug': slug,
                    'name': title,
                    'description': description,
                    'category': category_name,
                    'keywords': keywords,
                    'url': f'/{slug}',
                    'rpm': tool_data.get('rpm', 25) if isinstance(tool_data, dict) else 25,
                    'base_name': tool_data.get('base_name', '') if isinstance(tool_data, dict) else '',
                    'focus_keyword': seo_data.get('focus_keyword', ''),
                    'icon': get_category_icon(category_name)
                }
                tools_list.append(tool)

            except Exception as e:
                current_app.logger.error(f"Error processing tool {slug}: {str(e)}")
                # Continue with next tool instead of failing completely
                continue

        current_app.logger.info(f"Processed {len(tools_list)} tools successfully")

        # Apply filters
        filtered_tools = tools_list

        # Category filter
        if category and category != 'all':
            filtered_tools = [t for t in filtered_tools if t['category'].lower() == category]

        # Search filter
        if search:
            filtered_tools = [t for t in filtered_tools if
                              search in t['name'].lower() or
                              search in t['description'].lower() or
                              search in t['keywords'].lower() or
                              search in t['category'].lower()]

        # Sort tools
        if sort_by == 'name':
            filtered_tools.sort(key=lambda x: x['name'].lower())
        elif sort_by == 'category':
            filtered_tools.sort(key=lambda x: (x['category'], x['name']))
        elif sort_by == 'popularity':
            filtered_tools.sort(key=lambda x: x['rpm'], reverse=True)

        # Pagination
        total_tools = len(filtered_tools)
        total_pages = math.ceil(total_tools / per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tools = filtered_tools[start_idx:end_idx]

        return jsonify({
            'success': True,
            'tools': paginated_tools,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_tools': total_tools,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'filters': {
                'category': category,
                'search': search,
                'sort': sort_by
            },
            'debug_info': {
                'total_tools_in_config': len(ALL_TOOLS),
                'tools_after_processing': len(tools_list),
                'tools_after_filtering': len(filtered_tools)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error getting all tools: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug_info': {
                'ALL_TOOLS_available': ALL_TOOLS is not None,
                'ALL_TOOLS_type': str(type(ALL_TOOLS)),
                'ALL_TOOLS_length': len(ALL_TOOLS) if ALL_TOOLS else 0
            }
        }), 500


@tools_api_bp.route('/debug', methods=['GET'])
def debug_tools():
    """Debug endpoint to check tools configuration"""
    try:
        return jsonify({
            'success': True,
            'debug_info': {
                'ALL_TOOLS_available': ALL_TOOLS is not None,
                'ALL_TOOLS_type': str(type(ALL_TOOLS)),
                'ALL_TOOLS_length': len(ALL_TOOLS) if ALL_TOOLS else 0,
                'first_5_keys': list(ALL_TOOLS.keys())[:5] if ALL_TOOLS else [],
                'sample_tool': {
                    'key': list(ALL_TOOLS.keys())[0] if ALL_TOOLS else None,
                    'data': list(ALL_TOOLS.values())[0] if ALL_TOOLS else None
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with tool counts"""
    try:
        categories = {}

        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        for tool_data in ALL_TOOLS.values():
            if not isinstance(tool_data, dict):
                continue

            category = tool_data.get('category', 'other')
            if category not in categories:
                categories[category] = {
                    'name': format_category_name(category),
                    'slug': category,
                    'count': 0,
                    'icon': get_category_icon(category),
                    'description': get_category_description(category)
                }
            categories[category]['count'] += 1

        # Sort by count descending
        sorted_categories = sorted(categories.values(), key=lambda x: x['count'], reverse=True)

        return jsonify({
            'success': True,
            'categories': sorted_categories,
            'total_categories': len(categories)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting categories: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/featured', methods=['GET'])
def get_featured_tools():
    """Get featured tools (highest RPM)"""
    try:
        limit = int(request.args.get('limit', 6))

        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        tools_list = []
        for slug, tool_data in ALL_TOOLS.items():
            if not isinstance(tool_data, dict):
                continue

            seo_data = tool_data.get('seo_data', {})
            tool = {
                'slug': slug,
                'name': seo_data.get('title', slug.replace('-', ' ').title()),
                'description': seo_data.get('description', 'AI-powered tool'),
                'category': tool_data.get('category', 'other'),
                'url': f'/{slug}',
                'rpm': tool_data.get('rpm', 25),
                'icon': get_category_icon(tool_data.get('category', 'other'))
            }
            tools_list.append(tool)

        # Sort by RPM and get top tools
        featured_tools = sorted(tools_list, key=lambda x: x['rpm'], reverse=True)[:limit]

        return jsonify({
            'success': True,
            'featured_tools': featured_tools
        })

    except Exception as e:
        current_app.logger.error(f"Error getting featured tools: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/search', methods=['GET'])
def search_tools():
    """Advanced search with suggestions"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400

        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        results = []
        suggestions = set()

        for slug, tool_data in ALL_TOOLS.items():
            if not isinstance(tool_data, dict):
                continue

            seo_data = tool_data.get('seo_data', {})
            title = seo_data.get('title', slug.replace('-', ' ').title())
            description = seo_data.get('description', '')
            keywords = seo_data.get('keywords', '')
            category = tool_data.get('category', 'other')

            # Calculate relevance score
            relevance = 0
            query_lower = query.lower()

            if query_lower in title.lower():
                relevance += 10
            if query_lower in description.lower():
                relevance += 5
            if query_lower in keywords.lower():
                relevance += 3
            if query_lower in category.lower():
                relevance += 2

            if relevance > 0:
                tool = {
                    'slug': slug,
                    'name': title,
                    'description': description,
                    'category': category,
                    'url': f'/{slug}',
                    'relevance': relevance,
                    'icon': get_category_icon(category)
                }
                results.append(tool)

            # Collect suggestions from keywords
            for keyword in keywords.split(','):
                keyword = keyword.strip().lower()
                if keyword and query_lower in keyword:
                    suggestions.add(keyword)

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)

        return jsonify({
            'success': True,
            'query': query,
            'results': results[:limit],
            'total_results': len(results),
            'suggestions': list(suggestions)[:5]
        })

    except Exception as e:
        current_app.logger.error(f"Error searching tools: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        categories = {}
        total_tools = len(ALL_TOOLS)

        for tool_data in ALL_TOOLS.values():
            if not isinstance(tool_data, dict):
                continue

            category = tool_data.get('category', 'other')
            categories[category] = categories.get(category, 0) + 1

        return jsonify({
            'success': True,
            'stats': {
                'total_tools': total_tools,
                'total_categories': len(categories),
                'categories': categories,
                'most_popular_category': max(categories.items(), key=lambda x: x[1])[0] if categories else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/<slug>', methods=['GET'])
def get_tool_details(slug):
    """Get detailed information about a specific tool"""
    try:
        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        tool_data = ALL_TOOLS.get(slug)
        if not tool_data or not isinstance(tool_data, dict):
            return jsonify({'success': False, 'error': f'Tool "{slug}" not found'}), 404

        seo_data = tool_data.get('seo_data', {})

        # Get similar tools (same category)
        similar_tools = []
        category = tool_data.get('category', 'other')

        for other_slug, other_data in ALL_TOOLS.items():
            if not isinstance(other_data, dict):
                continue
            if other_slug != slug and other_data.get('category') == category:
                similar_tool = {
                    'slug': other_slug,
                    'name': other_data.get('seo_data', {}).get('title', other_slug.replace('-', ' ').title()),
                    'description': other_data.get('seo_data', {}).get('description', 'AI-powered tool'),
                    'url': f'/{other_slug}'
                }
                similar_tools.append(similar_tool)
                if len(similar_tools) >= 3:
                    break

        tool_details = {
            'slug': slug,
            'name': seo_data.get('title', slug.replace('-', ' ').title()),
            'description': seo_data.get('description', 'AI-powered tool'),
            'category': category,
            'keywords': seo_data.get('keywords', ''),
            'url': f'/{slug}',
            'rpm': tool_data.get('rpm', 25),
            'base_name': tool_data.get('base_name', ''),
            'focus_keyword': seo_data.get('focus_keyword', ''),
            'icon': get_category_icon(category),
            'similar_tools': similar_tools
        }

        return jsonify({
            'success': True,
            'tool': tool_details
        })

    except Exception as e:
        current_app.logger.error(f"Error getting tool details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Helper functions
def get_category_icon(category):
    """Get icon for category"""
    icons = {
        'finance': '💰',
        'insurance': '🛡️',
        'health': '🏥',
        'business': '📊',
        'legal': '⚖️',
        'real_estate': '🏠',
        'tax': '📋',
        'retirement': '👴',
        'fitness': '💪',
        'nutrition': '🥗',
        'pregnancy': '🤱',
        'automotive': '🚗',
        'education': '🎓',
        'technology': '💻',
        'travel': '✈️',
        'other': '🔧'
    }
    return icons.get(category, '📊')


def format_category_name(category):
    """Format category name for display"""
    names = {
        'finance': 'Finance & Loans',
        'insurance': 'Insurance',
        'health': 'Health & Medical',
        'business': 'Business Analytics',
        'legal': 'Legal & Law',
        'real_estate': 'Real Estate',
        'tax': 'Tax & IRS',
        'retirement': 'Retirement Planning',
        'fitness': 'Fitness & Exercise',
        'nutrition': 'Nutrition & Diet',
        'pregnancy': 'Pregnancy & Fertility',
        'automotive': 'Automotive',
        'education': 'Education',
        'technology': 'Technology',
        'travel': 'Travel & Tourism',
        'other': 'Other Tools'
    }
    return names.get(category, category.replace('_', ' ').title())


def get_category_description(category):
    """Get description for category"""
    descriptions = {
        'finance': 'Professional financial calculators and analysis tools',
        'insurance': 'Insurance premium calculators and coverage analysis',
        'health': 'Medical calculators and health assessment tools',
        'business': 'Business analytics and calculation tools',
        'legal': 'Legal cost estimators and analysis tools',
        'real_estate': 'Property valuation and real estate calculators',
        'tax': 'Tax calculators and planning tools',
        'retirement': 'Retirement planning and pension calculators',
        'fitness': 'Fitness tracking and workout planning tools',
        'nutrition': 'Nutrition analysis and diet planning tools',
        'pregnancy': 'Pregnancy and fertility tracking tools',
        'automotive': 'Car-related calculators and analysis tools',
        'education': 'Educational calculators and planning tools',
        'technology': 'Tech calculators and analysis tools',
        'travel': 'Travel planning and cost calculation tools',
        'other': 'Miscellaneous calculators and tools'
    }
    return descriptions.get(category, 'Professional calculators and analysis tools')


# Helper functions
def get_category_icon(category):
    """Get icon for category"""
    icons = {
        'finance': '💰',
        'insurance': '🛡️',
        'health': '🏥',
        'business': '📊',
        'legal': '⚖️',
        'real_estate': '🏠',
        'tax': '📋',
        'retirement': '👴',
        'fitness': '💪',
        'nutrition': '🥗',
        'pregnancy': '🤱',
        'automotive': '🚗',
        'education': '🎓',
        'technology': '💻',
        'travel': '✈️',
        'other': '🔧',
        # Handle your specific categories
        'health & insurance': '🏥',
        'verzekeringen': '🛡️',
        'Health & Insurance': '🏥',
        'Verzekeringen': '🛡️'
    }
    return icons.get(category.lower(), '📊')


def format_category_name(category):
    """Format category name for display"""
    names = {
        'finance': 'Finance & Loans',
        'insurance': 'Insurance',
        'health': 'Health & Medical',
        'business': 'Business Analytics',
        'legal': 'Legal & Law',
        'real_estate': 'Real Estate',
        'tax': 'Tax & IRS',
        'retirement': 'Retirement Planning',
        'fitness': 'Fitness & Exercise',
        'nutrition': 'Nutrition & Diet',
        'pregnancy': 'Pregnancy & Fertility',
        'automotive': 'Automotive',
        'education': 'Education',
        'technology': 'Technology',
        'travel': 'Travel & Tourism',
        'other': 'Other Tools',
        # Handle your specific categories
        'health & insurance': 'Health & Insurance',
        'verzekeringen': 'Verzekeringen (Insurance)',
        'Health & Insurance': 'Health & Insurance',
        'Verzekeringen': 'Verzekeringen (Insurance)'
    }
    return names.get(category.lower(), category.replace('_', ' ').title())


def get_category_description(category):
    """Get description for category"""
    descriptions = {
        'finance': 'Professional financial calculators and analysis tools',
        'insurance': '# routes/tools_api_routes.py
    from flask import Blueprint, request, jsonify, current_app
    from utils.tools_config import ALL_TOOLS
    from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user
    import math

    tools_api_bp = Blueprint('tools_api', __name__, url_prefix='/api/tools') \
 \
                   @ tools_api_bp.route('/all', methods=['GET'])


def get_all_tools():
    """Get all tools with pagination and filtering"""
    try:
        # Debug: Print ALL_TOOLS info
        current_app.logger.info(f"ALL_TOOLS type: {type(ALL_TOOLS)}")
        current_app.logger.info(f"ALL_TOOLS keys count: {len(ALL_TOOLS) if ALL_TOOLS else 0}")
        current_app.logger.info(f"First few keys: {list(ALL_TOOLS.keys())[:5] if ALL_TOOLS else 'None'}")

        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        category = request.args.get('category', '').lower()
        search = request.args.get('search', '').lower()
        sort_by = request.args.get('sort', 'name')

        # Ensure ALL_TOOLS exists and is not empty
        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found',
                'debug_info': {
                    'ALL_TOOLS_type': str(type(ALL_TOOLS)),
                    'ALL_TOOLS_length': len(ALL_TOOLS) if ALL_TOOLS else 0
                }
            }), 500

        # Convert ALL_TOOLS dict to list
        tools_list = []
        for slug, tool_data in ALL_TOOLS.items():
            try:
                # Extract tool information safely
                seo_data = tool_data.get('seo_data', {}) if isinstance(tool_data, dict) else {}
                title = seo_data.get('title', slug.replace('-', ' ').title())
                description = seo_data.get('description', 'AI-powered calculator and analysis tool')
                keywords = seo_data.get('keywords', '')
                category_name = tool_data.get('category', 'other') if isinstance(tool_data, dict) else 'other'

                tool = {
                    'slug': slug,
                    'name': title,
                    'description': description,
                    'category': category_name,
                    'keywords': keywords,
                    'url': f'/{slug}',
                    'rpm': tool_data.get('rpm', 25) if isinstance(tool_data, dict) else 25,
                    'base_name': tool_data.get('base_name', '') if isinstance(tool_data, dict) else '',
                    'focus_keyword': seo_data.get('focus_keyword', ''),
                    'icon': get_category_icon(category_name)
                }
                tools_list.append(tool)

            except Exception as e:
                current_app.logger.error(f"Error processing tool {slug}: {str(e)}")
                # Continue with next tool instead of failing completely
                continue

        current_app.logger.info(f"Processed {len(tools_list)} tools successfully")

        # Apply filters
        filtered_tools = tools_list

        # Category filter
        if category and category != 'all':
            filtered_tools = [t for t in filtered_tools if t['category'].lower() == category]

        # Search filter
        if search:
            filtered_tools = [t for t in filtered_tools if
                              search in t['name'].lower() or
                              search in t['description'].lower() or
                              search in t['keywords'].lower() or
                              search in t['category'].lower()]

        # Sort tools
        if sort_by == 'name':
            filtered_tools.sort(key=lambda x: x['name'].lower())
        elif sort_by == 'category':
            filtered_tools.sort(key=lambda x: (x['category'], x['name']))
        elif sort_by == 'popularity':
            filtered_tools.sort(key=lambda x: x['rpm'], reverse=True)

        # Pagination
        total_tools = len(filtered_tools)
        total_pages = math.ceil(total_tools / per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tools = filtered_tools[start_idx:end_idx]

        return jsonify({
            'success': True,
            'tools': paginated_tools,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_tools': total_tools,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'filters': {
                'category': category,
                'search': search,
                'sort': sort_by
            },
            'debug_info': {
                'total_tools_in_config': len(ALL_TOOLS),
                'tools_after_processing': len(tools_list),
                'tools_after_filtering': len(filtered_tools)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error getting all tools: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug_info': {
                'ALL_TOOLS_available': ALL_TOOLS is not None,
                'ALL_TOOLS_type': str(type(ALL_TOOLS)),
                'ALL_TOOLS_length': len(ALL_TOOLS) if ALL_TOOLS else 0
            }
        }), 500


@tools_api_bp.route('/debug', methods=['GET'])
def debug_tools():
    """Debug endpoint to check tools configuration"""
    try:
        return jsonify({
            'success': True,
            'debug_info': {
                'ALL_TOOLS_available': ALL_TOOLS is not None,
                'ALL_TOOLS_type': str(type(ALL_TOOLS)),
                'ALL_TOOLS_length': len(ALL_TOOLS) if ALL_TOOLS else 0,
                'first_5_keys': list(ALL_TOOLS.keys())[:5] if ALL_TOOLS else [],
                'sample_tool': {
                    'key': list(ALL_TOOLS.keys())[0] if ALL_TOOLS else None,
                    'data': list(ALL_TOOLS.values())[0] if ALL_TOOLS else None
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tools_api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with tool counts"""
    try:
        categories = {}

        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        for tool_data in ALL_TOOLS.values():
            if not isinstance(tool_data, dict):
                continue

            category = tool_data.get('category', 'other')
            if category not in categories:
                categories[category] = {
                    'name': format_category_name(category),
                    'slug': category,
                    'count': 0,
                    'icon': get_category_icon(category),
                    'description': get_category_description(category)
                }
            categories[category]['count'] += 1

        # Sort by count descending
        sorted_categories = sorted(categories.values(), key=lambda x: x['count'], reverse=True)

        return jsonify({
            'success': True,
            'categories': sorted_categories,
            'total_categories': len(categories)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting categories: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/featured', methods=['GET'])
def get_featured_tools():
    """Get featured tools (highest RPM)"""
    try:
        limit = int(request.args.get('limit', 6))

        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        tools_list = []
        for slug, tool_data in ALL_TOOLS.items():
            if not isinstance(tool_data, dict):
                continue

            seo_data = tool_data.get('seo_data', {})
            tool = {
                'slug': slug,
                'name': seo_data.get('title', slug.replace('-', ' ').title()),
                'description': seo_data.get('description', 'AI-powered tool'),
                'category': tool_data.get('category', 'other'),
                'url': f'/{slug}',
                'rpm': tool_data.get('rpm', 25),
                'icon': get_category_icon(tool_data.get('category', 'other'))
            }
            tools_list.append(tool)

        # Sort by RPM and get top tools
        featured_tools = sorted(tools_list, key=lambda x: x['rpm'], reverse=True)[:limit]

        return jsonify({
            'success': True,
            'featured_tools': featured_tools
        })

    except Exception as e:
        current_app.logger.error(f"Error getting featured tools: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/search', methods=['GET'])
def search_tools():
    """Advanced search with suggestions"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400

        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        results = []
        suggestions = set()

        for slug, tool_data in ALL_TOOLS.items():
            if not isinstance(tool_data, dict):
                continue

            seo_data = tool_data.get('seo_data', {})
            title = seo_data.get('title', slug.replace('-', ' ').title())
            description = seo_data.get('description', '')
            keywords = seo_data.get('keywords', '')
            category = tool_data.get('category', 'other')

            # Calculate relevance score
            relevance = 0
            query_lower = query.lower()

            if query_lower in title.lower():
                relevance += 10
            if query_lower in description.lower():
                relevance += 5
            if query_lower in keywords.lower():
                relevance += 3
            if query_lower in category.lower():
                relevance += 2

            if relevance > 0:
                tool = {
                    'slug': slug,
                    'name': title,
                    'description': description,
                    'category': category,
                    'url': f'/{slug}',
                    'relevance': relevance,
                    'icon': get_category_icon(category)
                }
                results.append(tool)

            # Collect suggestions from keywords
            for keyword in keywords.split(','):
                keyword = keyword.strip().lower()
                if keyword and query_lower in keyword:
                    suggestions.add(keyword)

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)

        return jsonify({
            'success': True,
            'query': query,
            'results': results[:limit],
            'total_results': len(results),
            'suggestions': list(suggestions)[:5]
        })

    except Exception as e:
        current_app.logger.error(f"Error searching tools: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        categories = {}
        total_tools = len(ALL_TOOLS)

        for tool_data in ALL_TOOLS.values():
            if not isinstance(tool_data, dict):
                continue

            category = tool_data.get('category', 'other')
            categories[category] = categories.get(category, 0) + 1

        return jsonify({
            'success': True,
            'stats': {
                'total_tools': total_tools,
                'total_categories': len(categories),
                'categories': categories,
                'most_popular_category': max(categories.items(), key=lambda x: x[1])[0] if categories else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_api_bp.route('/<slug>', methods=['GET'])
def get_tool_details(slug):
    """Get detailed information about a specific tool"""
    try:
        if not ALL_TOOLS:
            return jsonify({
                'success': False,
                'error': 'No tools configuration found'
            }), 500

        tool_data = ALL_TOOLS.get(slug)
        if not tool_data or not isinstance(tool_data, dict):
            return jsonify({'success': False, 'error': f'Tool "{slug}" not found'}), 404

        seo_data = tool_data.get('seo_data', {})

        # Get similar tools (same category)
        similar_tools = []
        category = tool_data.get('category', 'other')

        for other_slug, other_data in ALL_TOOLS.items():
            if not isinstance(other_data, dict):
                continue
            if other_slug != slug and other_data.get('category') == category:
                similar_tool = {
                    'slug': other_slug,
                    'name': other_data.get('seo_data', {}).get('title', other_slug.replace('-', ' ').title()),
                    'description': other_data.get('seo_data', {}).get('description', 'AI-powered tool'),
                    'url': f'/{other_slug}'
                }
                similar_tools.append(similar_tool)
                if len(similar_tools) >= 3:
                    break

        tool_details = {
            'slug': slug,
            'name': seo_data.get('title', slug.replace('-', ' ').title()),
            'description': seo_data.get('description', 'AI-powered tool'),
            'category': category,
            'keywords': seo_data.get('keywords', ''),
            'url': f'/{slug}',
            'rpm': tool_data.get('rpm', 25),
            'base_name': tool_data.get('base_name', ''),
            'focus_keyword': seo_data.get('focus_keyword', ''),
            'icon': get_category_icon(category),
            'similar_tools': similar_tools
        }

        return jsonify({
            'success': True,
            'tool': tool_details
        })

    except Exception as e:
        current_app.logger.error(f"Error getting tool details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Helper functions
def get_category_icon(category):
    """Get icon for category"""
    icons = {
        'finance': '💰',
        'insurance': '🛡️',
        'health': '🏥',
        'business': '📊',
        'legal': '⚖️',
        'real_estate': '🏠',
        'tax': '📋',
        'retirement': '👴',
        'fitness': '💪',
        'nutrition': '🥗',
        'pregnancy': '🤱',
        'automotive': '🚗',
        'education': '🎓',
        'technology': '💻',
        'travel': '✈️',
        'other': '🔧'
    }
    return icons.get(category, '📊')


def format_category_name(category):
    """Format category name for display"""
    names = {
        'finance': 'Finance & Loans',
        'insurance': 'Insurance',
        'health': 'Health & Medical',
        'business': 'Business Analytics',
        'legal': 'Legal & Law',
        'real_estate': 'Real Estate',
        'tax': 'Tax & IRS',
        'retirement': 'Retirement Planning',
        'fitness': 'Fitness & Exercise',
        'nutrition': 'Nutrition & Diet',
        'pregnancy': 'Pregnancy & Fertility',
        'automotive': 'Automotive',
        'education': 'Education',
        'technology': 'Technology',
        'travel': 'Travel & Tourism',
        'other': 'Other Tools'
    }
    return names.get(category, category.replace('_', ' ').title())


def get_category_description(category):
    """Get description for category"""
    descriptions = {
        'finance': 'Professional financial calculators and analysis tools',
        'insurance': 'Insurance premium calculators and coverage analysis',
        'health': 'Medical calculators and health assessment tools',
        'business': 'Business analytics and calculation tools',
        'legal': 'Legal cost estimators and analysis tools',
        'real_estate': 'Property valuation and real estate calculators',
        'tax': 'Tax calculators and planning tools',
        'retirement': 'Retirement planning and pension calculators',
        'fitness': 'Fitness tracking and workout planning tools',
        'nutrition': 'Nutrition analysis and diet planning tools',
        'pregnancy': 'Pregnancy and fertility tracking tools',
        'automotive': 'Car-related calculators and analysis tools',
        'education': 'Educational calculators and planning tools',
        'technology': 'Tech calculators and analysis tools',
        'travel': 'Travel planning and cost calculation tools',
        'other': 'Miscellaneous calculators and tools'
    }
    return descriptions.get(category, 'Professional calculators and analysis tools')