import openai
from openai import OpenAI
import csv
import json
import re
import os
import time
import argparse
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Set
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")


class UltimateInfiniteToolGenerator:
    """
    ONE Generator for INFINITE scaling - generates 1000 unique tools per batch
    Tracks all previous generations to ensure 100% uniqueness across all batches
    """

    def __init__(self, openai_api_key: str = None):
        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key)
        elif os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        else:
            raise ValueError("OpenAI API key must be provided")

        # TOP 15 HIGH RPM COUNTRIES
        self.high_rpm_countries = [
            {"code": "NO", "name": "Norway", "rpm": 43.15, "currency": "NOK", "savings": 2100,
             "local_term": "postnummer", "language": "Norwegian"},
            {"code": "US", "name": "United States", "rpm": 35.00, "currency": "$", "savings": 2100,
             "local_term": "ZIP code", "language": "English"},
            {"code": "AU", "name": "Australia", "rpm": 36.21, "currency": "AUD $", "savings": 2400,
             "local_term": "postcode", "language": "English"},
            {"code": "DK", "name": "Denmark", "rpm": 24.65, "currency": "DKK", "savings": 2200,
             "local_term": "postnummer", "language": "Danish"},
            {"code": "CA", "name": "Canada", "rpm": 29.15, "currency": "CAD $", "savings": 2200,
             "local_term": "postal code", "language": "English"},
            {"code": "SE", "name": "Sweden", "rpm": 22.30, "currency": "SEK", "savings": 2000,
             "local_term": "postnummer", "language": "Swedish"},
            {"code": "CH", "name": "Switzerland", "rpm": 20.00, "currency": "CHF", "savings": 2800, "local_term": "PLZ",
             "language": "German"},
            {"code": "BE", "name": "Belgium", "rpm": 20.50, "currency": "€", "savings": 2000, "local_term": "postcode",
             "language": "Dutch"},
            {"code": "UK", "name": "United Kingdom", "rpm": 19.47, "currency": "£", "savings": 1800,
             "local_term": "postcode", "language": "English"},
            {"code": "NL", "name": "Netherlands", "rpm": 18.40, "currency": "€", "savings": 2000,
             "local_term": "postcode", "language": "Dutch"},
            {"code": "FI", "name": "Finland", "rpm": 18.90, "currency": "€", "savings": 2100,
             "local_term": "postinumero", "language": "Finnish"},
            {"code": "IE", "name": "Ireland", "rpm": 17.80, "currency": "€", "savings": 1900, "local_term": "Eircode",
             "language": "English"},
            {"code": "NZ", "name": "New Zealand", "rpm": 16.20, "currency": "NZD $", "savings": 1800,
             "local_term": "postcode", "language": "English"},
            {"code": "DE", "name": "Germany", "rpm": 15.00, "currency": "€", "savings": 1900, "local_term": "PLZ",
             "language": "German"},
            {"code": "AT", "name": "Austria", "rpm": 14.20, "currency": "€", "savings": 1800, "local_term": "PLZ",
             "language": "German"}
        ]

        # Category progression system for infinite scaling
        self.category_progression = {
            1: {  # Batch 1: Core Life Categories
                "categories": [
                    "salary_and_income", "tax_planning", "mortgage_and_real_estate", "loan_and_credit",
                    "health_and_fitness", "family_planning", "education_costs", "vehicle_and_transport",
                    "home_improvement", "investment_and_savings"
                ],
                "complexity": "basic",
                "target_searches": "1M+"
            },
            2: {  # Batch 2: Business & Professional
                "categories": [
                    "freelance_and_gig", "small_business_finance", "professional_services", "career_development",
                    "startup_costs", "business_operations", "marketing_and_sales", "employee_benefits",
                    "professional_licensing", "industry_specific_tools"
                ],
                "complexity": "intermediate",
                "target_searches": "500K+"
            },
            3: {  # Batch 3: Specialized & Niche
                "categories": [
                    "hobby_and_recreation", "travel_and_adventure", "environmental_and_sustainability",
                    "technology_and_digital", "arts_and_creativity", "sports_and_fitness_specialized",
                    "pet_and_animal_care", "senior_and_retirement", "disability_and_accessibility", "legal_specialized"
                ],
                "complexity": "advanced",
                "target_searches": "100K+"
            },
            4: {  # Batch 4: Professional & Technical
                "categories": [
                    "medical_and_healthcare_professional", "engineering_and_technical", "scientific_research",
                    "academic_and_research", "government_and_public_sector", "nonprofit_and_charity",
                    "international_and_cross_border", "compliance_and_regulatory", "risk_management",
                    "specialized_industries"
                ],
                "complexity": "expert",
                "target_searches": "50K+"
            },
            5: {  # Batch 5+: Micro-niches and Ultra-specific
                "categories": [
                    "ultra_niche_professions", "micro_hobbies", "specialized_medical_conditions",
                    "rare_financial_situations", "unique_geographic_locations", "specialized_equipment",
                    "cultural_and_religious_specific", "age_specific_ultra_niche", "disability_specific",
                    "emergency_and_crisis_specific"
                ],
                "complexity": "ultra_specialized",
                "target_searches": "10K+"
            }
        }

        # Track all existing tools
        self.existing_tools = set()
        self.existing_slugs = set()
        self.existing_categories = set()
        self.existing_purposes = set()

    def load_existing_tools(self) -> None:
        """Load all existing tools from previous batches to avoid duplicates"""

        print("🔍 Loading existing tools to avoid duplicates...")

        # Find all tools_config.json files
        config_files = glob.glob("*tools_config.json") + glob.glob("*_tools_config.json")

        total_existing = 0

        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                for slug, tool_data in config_data.items():
                    self.existing_slugs.add(slug)
                    self.existing_categories.add(tool_data.get('category', ''))
                    self.existing_purposes.add(tool_data.get('base_name', ''))

                    # Create compound identifier
                    compound_id = f"{tool_data.get('category', '')}_{tool_data.get('base_name', '')}".lower()
                    self.existing_tools.add(compound_id)

                total_existing += len(config_data)
                print(f"   📄 Loaded {len(config_data)} tools from {config_file}")

            except Exception as e:
                print(f"   ⚠️ Error loading {config_file}: {e}")

        print(f"✅ Total existing tools: {total_existing}")
        print(f"📊 Unique slugs: {len(self.existing_slugs)}")
        print(f"📂 Unique categories: {len(self.existing_categories)}")
        print(f"🎯 Unique purposes: {len(self.existing_purposes)}")

    def get_batch_categories(self, batch_number: int) -> Dict[str, Any]:
        """Get category configuration for specific batch"""

        if batch_number <= 5:
            return self.category_progression[batch_number]
        else:
            # For batch 6+, use ultra-specialized with expanding micro-niches
            return {
                "categories": [f"ultra_micro_niche_batch_{batch_number}"],
                "complexity": "ultra_micro_specialized",
                "target_searches": "5K+"
            }

    def generate_unique_tool_idea(self, batch_number: int, country_data: Dict[str, Any], attempt: int = 0) -> Dict[
        str, Any]:
        """Generate completely unique tool idea using AI"""

        batch_config = self.get_batch_categories(batch_number)
        categories_list = ", ".join(batch_config["categories"])

        # Progressive prompting based on batch number
        if batch_number == 1:
            focus_instruction = "Focus on ESSENTIAL daily life tools that millions of people need regularly."
        elif batch_number == 2:
            focus_instruction = "Focus on BUSINESS and PROFESSIONAL tools for entrepreneurs, freelancers, and working professionals."
        elif batch_number == 3:
            focus_instruction = "Focus on SPECIALIZED HOBBIES, LIFESTYLE, and NICHE INTERESTS that people are passionate about."
        elif batch_number == 4:
            focus_instruction = "Focus on PROFESSIONAL and TECHNICAL tools for experts, specialists, and advanced users."
        else:
            focus_instruction = f"Focus on ULTRA-SPECIALIZED micro-niches for batch {batch_number}. Find very specific, unique use cases."

        existing_sample = list(self.existing_purposes)[:50] if self.existing_purposes else ["No existing tools"]

        prompt = f"""
You are an expert tool discovery specialist. Generate a COMPLETELY UNIQUE calculator/tool idea for batch {batch_number}.

BATCH {batch_number} FOCUS: {categories_list}
TARGET COUNTRY: {country_data['name']} 
COMPLEXITY LEVEL: {batch_config['complexity']}
TARGET SEARCH VOLUME: {batch_config['target_searches']}

{focus_instruction}

CRITICAL REQUIREMENTS:
1. Must be 100% UNIQUE - not similar to any existing tool
2. Must serve a REAL need that people have
3. Must be calculable/processable with form inputs
4. Must have decent search volume potential
5. Must be valuable for {country_data['name']} residents

EXISTING TOOLS TO AVOID (sample): {existing_sample[:10]}

TOOL CATEGORIES FOR BATCH {batch_number}: {categories_list}

Generate ONE unique tool idea in this JSON format:
{{
    "tool_name": "Specific descriptive name",
    "category": "Main category from the batch categories",
    "target_audience": "Who this serves",
    "unique_value": "What makes this tool special and needed",
    "search_keywords": ["keyword1", "keyword2", "keyword3"],
    "form_fields": [
        {{
            "name": "field_name",
            "label": "Field Label",
            "type": "text|select|slider|currency_slider|checkbox",
            "icon": "emoji",
            "required": true,
            "options": ["option1", "option2"] // for select only
            "min": "0", "max": "100", "default": "50" // for sliders only
            "placeholder": "Enter..." // for text only
        }}
        // 4-6 fields total, always include location first
    ],
    "why_unique": "Explanation of why this tool doesn't exist yet",
    "real_world_use": "Specific scenarios where people would use this"
}}

Make it genuinely useful and unique!
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": f"You are an expert at discovering unique, valuable tool ideas for batch {batch_number}. You ensure 100% uniqueness and real-world value."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.8  # Higher creativity for uniqueness
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                tool_idea = json.loads(json_content)
            else:
                tool_idea = json.loads(content)

            # Check for uniqueness
            compound_id = f"{tool_idea.get('category', '')}_{tool_idea.get('tool_name', '')}".lower()
            if compound_id in self.existing_tools and attempt < 3:
                print(f"   🔄 Duplicate detected, retrying... (attempt {attempt + 1})")
                return self.generate_unique_tool_idea(batch_number, country_data, attempt + 1)

            # Add to existing tools to avoid future duplicates
            self.existing_tools.add(compound_id)

            return tool_idea

        except Exception as e:
            print(f"   ⚠️ Error generating tool idea: {e}")
            return self.get_fallback_tool_idea(batch_number, country_data)

    def get_fallback_tool_idea(self, batch_number: int, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback tool idea if AI generation fails"""

        fallback_ideas = {
            1: {
                "tool_name": f"Local Cost of Living Calculator",
                "category": "lifestyle_planning",
                "target_audience": f"people considering moving to {country_data['name']}",
                "unique_value": f"comprehensive cost comparison for {country_data['name']} cities"
            },
            2: {
                "tool_name": f"Freelance Rate Calculator",
                "category": "business_finance",
                "target_audience": f"freelancers in {country_data['name']}",
                "unique_value": f"market-rate pricing for {country_data['name']} freelancers"
            }
        }

        batch_config = fallback_ideas.get(batch_number, fallback_ideas[1])

        return {
            **batch_config,
            "search_keywords": [batch_config["tool_name"].lower(), country_data["name"].lower(), "calculator"],
            "form_fields": [
                {
                    "name": "location",
                    "label": country_data["local_term"].title(),
                    "type": "text",
                    "icon": "📍",
                    "required": True,
                    "placeholder": f"Enter your {country_data['local_term']}"
                },
                {
                    "name": "experience_level",
                    "label": "Experience Level",
                    "type": "select",
                    "icon": "📊",
                    "required": True,
                    "options": ["Beginner", "Intermediate", "Advanced", "Expert"]
                },
                {
                    "name": "budget",
                    "label": "Budget Range",
                    "type": "currency_slider",
                    "icon": "💰",
                    "required": True,
                    "min": "100",
                    "max": "10000",
                    "default": "1000"
                }
            ],
            "why_unique": "Fallback tool with basic functionality",
            "real_world_use": "General purpose calculation"
        }

    def create_slug_from_tool_idea(self, tool_idea: Dict[str, Any]) -> str:
        """Create SEO-friendly slug from tool idea"""

        name = tool_idea.get("tool_name", "calculator")
        category = tool_idea.get("category", "")

        # Create base slug
        slug_parts = []

        # Add category prefix for SEO
        if category:
            slug_parts.append(category.replace("_", "-"))

        # Add tool name
        name_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        name_slug = re.sub(r'\s+', '-', name_slug)
        slug_parts.append(name_slug)

        base_slug = "-".join(slug_parts)

        # Ensure uniqueness
        counter = 1
        final_slug = base_slug

        while final_slug in self.existing_slugs:
            final_slug = f"{base_slug}-{counter}"
            counter += 1

        self.existing_slugs.add(final_slug)
        return final_slug

    def generate_html_form(self, tool_idea: Dict[str, Any], country_data: Dict[str, Any]) -> str:
        """Generate HTML form from tool idea"""

        form_html = f'''
    <div class="enhanced-form global-{country_data["code"].lower()}">
        <div class="form-header">
            <div class="country-flag">{self.get_country_flag(country_data["code"])}</div>
            <h2>🧮 {tool_idea["tool_name"]}</h2>
            <p>Specialized for {country_data["name"]} - {tool_idea["target_audience"]}</p>
            <div class="unique-value">{tool_idea["unique_value"]}</div>
            <div class="urgency-badge">Save {country_data["currency"]}{country_data["savings"]:,}/year!</div>
        </div>

        <form id="tool-form" onsubmit="calculateResults(event)">
            <div class="form-grid">'''

        # Generate form fields
        for field in tool_idea.get("form_fields", []):
            form_html += self.generate_field_html(field, country_data["currency"])

        form_html += f'''
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">
                    <span class="btn-icon">🚀</span>
                    Calculate Now
                </button>
            </div>
        </form>
    </div>'''

        return form_html

    def generate_field_html(self, field: Dict[str, Any], currency: str) -> str:
        """Generate HTML for individual form field"""

        field_html = f'''
                <div class="form-group">
                    <label class="form-label" for="{field['name']}">
                        <span class="label-icon">{field.get('icon', '📝')}</span>
                        {field.get('label', field['name'].replace('_', ' ').title())}
                    </label>'''

        field_type = field.get('type', 'text')

        if field_type == 'slider':
            default_val = field.get('default', field.get('min', '0'))
            field_html += f'''
                    <div class="slider-group">
                        <div class="slider-container">
                            <input type="range" id="{field['name']}" name="{field['name']}"
                                   class="slider-input" data-format="number"
                                   min="{field.get('min', '0')}" max="{field.get('max', '100')}" 
                                   value="{default_val}" oninput="updateSliderValue(this)">
                            <div class="slider-value" id="{field['name']}-value">{default_val}</div>
                        </div>
                    </div>'''
        elif field_type == 'currency_slider':
            default_val = field.get('default', field.get('min', '1000'))
            field_html += f'''
                    <div class="slider-group">
                        <div class="slider-container">
                            <input type="range" id="{field['name']}" name="{field['name']}"
                                   class="slider-input" data-format="currency"
                                   min="{field.get('min', '1000')}" max="{field.get('max', '100000')}" 
                                   value="{default_val}" oninput="updateSliderValue(this)">
                            <div class="slider-value" id="{field['name']}-value">{currency}{int(default_val):,}</div>
                        </div>
                    </div>'''
        elif field_type == 'select':
            field_html += f'''
                    <select id="{field['name']}" name="{field['name']}" class="form-select">'''
            options = field.get('options', ['Option 1', 'Option 2'])
            for option in options:
                field_html += f'<option value="{option}">{option}</option>'
            field_html += '</select>'
        elif field_type == 'checkbox':
            field_html += f'''
                    <div class="checkbox-group">
                        <input type="checkbox" id="{field['name']}" name="{field['name']}" class="form-checkbox">
                        <label for="{field['name']}" class="checkbox-label">Yes</label>
                    </div>'''
        else:  # text
            placeholder = field.get('placeholder', f'Enter {field.get("label", field["name"].replace("_", " "))}')
            field_html += f'''
                    <input type="text" id="{field['name']}" name="{field['name']}" class="form-input"
                           placeholder="{placeholder}" autocomplete="on">'''

        field_html += '''
                </div>'''

        return field_html

    def get_country_flag(self, country_code: str) -> str:
        """Get country flag emoji"""
        flags = {
            "NO": "🇳🇴", "US": "🇺🇸", "AU": "🇦🇺", "DK": "🇩🇰", "CA": "🇨🇦",
            "SE": "🇸🇪", "CH": "🇨🇭", "BE": "🇧🇪", "UK": "🇬🇧", "NL": "🇳🇱",
            "FI": "🇫🇮", "IE": "🇮🇪", "NZ": "🇳🇿", "DE": "🇩🇪", "AT": "🇦🇹"
        }
        return flags.get(country_code, "🌍")

    def generate_complete_page(self, tool_idea: Dict[str, Any], form_html: str, country_data: Dict[str, Any],
                               slug: str) -> str:
        """Generate complete page content"""

        return f'''
        <div class="hero-section">
            <div class="country-flag">{self.get_country_flag(country_data["code"])}</div>
            <h1>🧮 {tool_idea["tool_name"]}</h1>
            <p>{tool_idea["unique_value"]} - Specialized for {country_data["name"]} {tool_idea["target_audience"]}</p>
        </div>

        <div class="tool-interface">
            {form_html}
        </div>

        <div class="results-container">
            <div id="tool-results" class="tool-results">
                <div class="results-placeholder">
                    <h3>📊 Your {country_data["name"]} Results Will Appear Here</h3>
                </div>
            </div>
        </div>

        <div class="educational-content">
            <h3>💡 Why Use This {tool_idea["tool_name"]}?</h3>
            <p><strong>Real-world use:</strong> {tool_idea.get("real_world_use", "Calculate important values for better decisions.")}</p>
            <p><strong>Why unique:</strong> {tool_idea.get("why_unique", "This tool provides specialized calculations you won't find elsewhere.")}</p>
        </div>

        <script>
        const TOOL_CONFIG = {{
            "slug": "{slug}",
            "category": "{tool_idea['category']}",
            "tool_name": "{tool_idea['tool_name']}",
            "target_audience": "{tool_idea['target_audience']}",
            "unique_value": "{tool_idea['unique_value']}",
            "rpm": {country_data['rpm']},
            "target_country": "{country_data['code']}",
            "country_data": {json.dumps(country_data)},
            "form_fields": {json.dumps(tool_idea.get('form_fields', []))},
            "search_keywords": {json.dumps(tool_idea.get('search_keywords', []))},
            "generated_date": "{datetime.now().isoformat()}"
        }};
        </script>
        '''

    def process_single_tool(self, batch_number: int, country_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Process a single tool generation"""

        try:
            print(f"🔄 Generating tool {index + 1}: Batch {batch_number}, {country_data['name']}")

            # Generate unique tool idea
            tool_idea = self.generate_unique_tool_idea(batch_number, country_data)

            # Create slug
            slug = self.create_slug_from_tool_idea(tool_idea)

            print(f"   ✅ Generated: {tool_idea['tool_name']}")
            print(f"   🔗 Slug: {slug}")
            print(f"   📝 Fields: {len(tool_idea.get('form_fields', []))}")

            # Generate HTML and complete page
            form_html = self.generate_html_form(tool_idea, country_data)
            page_content = self.generate_complete_page(tool_idea, form_html, country_data, slug)

            # Return CSV row data
            return {
                "post_title": f"{tool_idea['tool_name']} - {country_data['name']} 2025",
                "post_name": slug,
                "post_content": page_content,
                "post_excerpt": f"{tool_idea['unique_value']} for {country_data['name']} residents.",
                "post_status": "publish",
                "post_type": "page",
                "menu_order": index,
                "rank_math_title": f"#{1} {tool_idea['tool_name']} - {country_data['code']} 2025",
                "rank_math_description": f"{tool_idea['unique_value']} for {country_data['name']}. Save {country_data['currency']}{country_data['savings']:,}/year.",
                "rank_math_focus_keyword": " ".join(tool_idea.get('search_keywords', [])[:3]),
                "rank_math_keywords": ",".join(tool_idea.get('search_keywords', [])),
                "meta:tool_category": tool_idea['category'],
                "meta:tool_rpm": country_data['rpm'],
                "meta:target_country": country_data['code'],
                "meta:generated_with": f"batch_{batch_number}_infinite_generator",
                "meta:field_count": len(tool_idea.get('form_fields', [])),
                "meta:batch_number": batch_number,
                "meta:generated_date": datetime.now().isoformat(),
                "categories": f"AI Tools,{country_data['name']} Tools,{tool_idea['category'].title()} Calculators",
                "tags": ",".join(tool_idea.get('search_keywords', [])),
                "featured_image": f"{tool_idea['category']}-calculator-{country_data['code'].lower()}.jpg"
            }

        except Exception as e:
            print(f"❌ Error generating tool {index + 1}: {e}")
            # Use fallback
            tool_idea = self.get_fallback_tool_idea(batch_number, country_data)
            slug = self.create_slug_from_tool_idea(tool_idea)
            form_html = self.generate_html_form(tool_idea, country_data)
            page_content = self.generate_complete_page(tool_idea, form_html, country_data, slug)

            return {
                "post_title": f"{tool_idea['tool_name']} - {country_data['name']} 2025",
                "post_name": slug,
                "post_content": page_content,
                "post_excerpt": f"{tool_idea['unique_value']} for {country_data['name']} residents.",
                "post_status": "publish",
                "post_type": "page",
                "menu_order": index,
                "rank_math_title": f"#{1} {tool_idea['tool_name']} - {country_data['code']} 2025",
                "rank_math_description": f"{tool_idea['unique_value']} for {country_data['name']}.",
                "rank_math_focus_keyword": " ".join(tool_idea.get('search_keywords', [])[:3]),
                "rank_math_keywords": ",".join(tool_idea.get('search_keywords', [])),
                "meta:tool_category": tool_idea['category'],
                "meta:tool_rpm": country_data['rpm'],
                "meta:target_country": country_data['code'],
                "meta:generated_with": f"batch_{batch_number}_fallback",
                "meta:field_count": len(tool_idea.get('form_fields', [])),
                "meta:batch_number": batch_number,
                "meta:generated_date": datetime.now().isoformat(),
                "categories": f"AI Tools,{country_data['name']} Tools,{tool_idea['category'].title()} Calculators",
                "tags": ",".join(tool_idea.get('search_keywords', [])),
                "featured_image": f"{tool_idea['category']}-calculator-{country_data['code'].lower()}.jpg"
            }

    def generate_infinite_batch(self, batch_number: int, count: int = 1000, max_workers: int = 10):
        """Generate infinite batch of unique tools"""

        print(f"🚀 INFINITE GENERATOR - BATCH {batch_number}")
        print("=" * 80)

        # Load existing tools to avoid duplicates
        self.load_existing_tools()

        batch_config = self.get_batch_categories(batch_number)

        print(f"📊 Generating {count} tools for Batch {batch_number}")