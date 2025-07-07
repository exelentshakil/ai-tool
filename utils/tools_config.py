import json
import os
from config.settings import TOOLS_CONFIG_FILE, MAIN_CATEGORIES

# Global tools storage
ALL_TOOLS = {}


def load_all_tools():
    """Load all tools from tools_config.json"""
    global ALL_TOOLS
    try:
        if not os.path.exists(TOOLS_CONFIG_FILE):
            print(f"❌ {TOOLS_CONFIG_FILE} not found!")
            create_default_tools_config()
            return False

        with open(TOOLS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            ALL_TOOLS = json.load(f)

        # Ensure each tool has a slug
        for tool_slug, tool_config in ALL_TOOLS.items():
            if 'slug' not in tool_config:
                tool_config['slug'] = tool_slug

        print(f"✅ Loaded {len(ALL_TOOLS)} tools from {TOOLS_CONFIG_FILE}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {TOOLS_CONFIG_FILE}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading tools: {e}")
        return False


def create_default_tools_config():
    """Create a default tools configuration file"""
    default_tools = {
        "sample-calculator": {
            "slug": "sample-calculator",
            "category": "finance",
            "base_name": "Sample Calculator",
            "variation": "calculator",
            "rpm": 25,
            "seo_data": {
                "title": "Sample Calculator - Free Online Tool",
                "description": "Free sample calculator with AI-powered insights.",
                "keywords": "sample calculator, free calculator, online tool",
                "h1": "AI-Powered Sample Calculator",
                "focus_keyword": "sample calculator"
            }
        }
    }

    try:
        with open(TOOLS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_tools, f, indent=2)
        print(f"✅ Created default {TOOLS_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error creating default tools config: {e}")
        return False


def get_tool_by_slug(slug):
    """Get tool configuration by slug"""
    return ALL_TOOLS.get(slug)


def get_tools_by_category(category):
    """Get all tools in a specific category"""
    return {slug: config for slug, config in ALL_TOOLS.items()
            if config.get('category', '').lower() == category.lower()}


def get_core_tools():
    """Get one main tool from each major category"""
    core_tools = {}

    for category in MAIN_CATEGORIES:
        # Find first tool in this category
        for slug, tool_data in ALL_TOOLS.items():
            if tool_data.get('category') == category:
                core_tools[slug] = tool_data
                break  # Only take the first one found

    return core_tools


def search_tools(query, category=None):
    """Search tools by query and optionally filter by category"""
    query = query.lower()
    results = []

    for slug, tool_data in ALL_TOOLS.items():
        # Filter by category if specified
        if category and tool_data.get('category', '').lower() != category.lower():
            continue

        # Search in various fields
        searchable_text = ' '.join([
            slug,
            tool_data.get('base_name', ''),
            tool_data.get('seo_data', {}).get('title', ''),
            tool_data.get('seo_data', {}).get('description', ''),
            tool_data.get('seo_data', {}).get('keywords', ''),
            tool_data.get('category', '')
        ]).lower()

        if query in searchable_text:
            results.append({
                'slug': slug,
                'name': tool_data.get('seo_data', {}).get('title', slug.replace('-', ' ').title()),
                'description': tool_data.get('seo_data', {}).get('description', ''),
                'category': tool_data.get('category', 'other'),
                'relevance': searchable_text.count(query)  # Simple relevance scoring
            })

    # Sort by relevance
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results


def get_tool_statistics():
    """Get statistics about loaded tools"""
    if not ALL_TOOLS:
        return {
            "total_tools": 0,
            "categories": {},
            "variations": {},
            "avg_rpm": 0
        }

    categories = {}
    variations = {}
    rpms = []

    for tool_data in ALL_TOOLS.values():
        # Count categories
        category = tool_data.get('category', 'other')
        categories[category] = categories.get(category, 0) + 1

        # Count variations
        variation = tool_data.get('variation', 'calculator')
        variations[variation] = variations.get(variation, 0) + 1

        # Collect RPMs
        rpm = tool_data.get('rpm', 0)
        if isinstance(rpm, (int, float)) and rpm > 0:
            rpms.append(rpm)

    return {
        "total_tools": len(ALL_TOOLS),
        "categories": categories,
        "variations": variations,
        "avg_rpm": sum(rpms) / len(rpms) if rpms else 0,
        "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    }


def validate_tool_config(tool_config):
    """Validate a tool configuration"""
    required_fields = ['slug', 'category', 'base_name']
    errors = []

    for field in required_fields:
        if field not in tool_config:
            errors.append(f"Missing required field: {field}")

    # Validate category
    if tool_config.get('category') not in MAIN_CATEGORIES + ['other']:
        errors.append(f"Invalid category: {tool_config.get('category')}")

    # Validate RPM
    rpm = tool_config.get('rpm', 0)
    if not isinstance(rpm, (int, float)) or rpm < 0:
        errors.append("RPM must be a non-negative number")

    # Validate SEO data
    seo_data = tool_config.get('seo_data', {})
    seo_required = ['title', 'description']
    for field in seo_required:
        if field not in seo_data:
            errors.append(f"Missing SEO field: {field}")

    return len(errors) == 0, errors


def add_tool(slug, tool_config):
    """Add a new tool to the configuration"""
    is_valid, errors = validate_tool_config(tool_config)
    if not is_valid:
        return False, errors

    tool_config['slug'] = slug
    ALL_TOOLS[slug] = tool_config

    # Save to file
    try:
        with open(TOOLS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(ALL_TOOLS, f, indent=2)
        return True, []
    except Exception as e:
        return False, [f"Error saving tools config: {e}"]


def update_tool(slug, tool_config):
    """Update an existing tool configuration"""
    if slug not in ALL_TOOLS:
        return False, [f"Tool '{slug}' not found"]

    is_valid, errors = validate_tool_config(tool_config)
    if not is_valid:
        return False, errors

    tool_config['slug'] = slug
    ALL_TOOLS[slug] = tool_config

    # Save to file
    try:
        with open(TOOLS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(ALL_TOOLS, f, indent=2)
        return True, []
    except Exception as e:
        return False, [f"Error saving tools config: {e}"]


def delete_tool(slug):
    """Delete a tool from the configuration"""
    if slug not in ALL_TOOLS:
        return False, [f"Tool '{slug}' not found"]

    del ALL_TOOLS[slug]

    # Save to file
    try:
        with open(TOOLS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(ALL_TOOLS, f, indent=2)
        return True, []
    except Exception as e:
        return False, [f"Error saving tools config: {e}"]


def get_similar_tools(slug, limit=5):
    """Get similar tools based on category and keywords"""
    if slug not in ALL_TOOLS:
        return []

    target_tool = ALL_TOOLS[slug]
    target_category = target_tool.get('category', '')
    target_keywords = set(target_tool.get('seo_data', {}).get('keywords', '').lower().split())

    similar_tools = []

    for other_slug, other_tool in ALL_TOOLS.items():
        if other_slug == slug:
            continue

        similarity_score = 0

        # Category match
        if other_tool.get('category', '') == target_category:
            similarity_score += 10

        # Keyword overlap
        other_keywords = set(other_tool.get('seo_data', {}).get('keywords', '').lower().split())
        keyword_overlap = len(target_keywords.intersection(other_keywords))
        similarity_score += keyword_overlap * 2

        if similarity_score > 0:
            similar_tools.append({
                'slug': other_slug,
                'name': other_tool.get('seo_data', {}).get('title', other_slug.replace('-', ' ').title()),
                'category': other_tool.get('category', ''),
                'similarity_score': similarity_score
            })

    # Sort by similarity and return top results
    similar_tools.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similar_tools[:limit]