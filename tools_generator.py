import openai
from openai import OpenAI
import csv
import json
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")


class OpenAIToolGenerator:
    """
    Uses OpenAI API to generate unique, valuable form fields and content for each URL slug
    Streamlined version with only concurrent processing
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

    def extract_tool_type_from_slug(self, slug: str) -> str:
        """Extract the main tool type from slug for better titles"""
        slug_lower = slug.lower()

        if any(word in slug_lower for word in ['motorcycle', 'bike']):
            return "Motorcycle Insurance"
        elif any(word in slug_lower for word in ['boat', 'marine', 'yacht']):
            return "Boat Insurance"
        elif any(word in slug_lower for word in ['rv', 'motorhome', 'camper']):
            return "RV Insurance"
        elif any(word in slug_lower for word in ['pet', 'dog', 'cat']):
            return "Pet Insurance"
        elif any(word in slug_lower for word in ['renters', 'rental']):
            return "Renters Insurance"
        elif any(word in slug_lower for word in ['umbrella']):
            return "Umbrella Insurance"
        elif any(word in slug_lower for word in ['disability']):
            return "Disability Insurance"
        elif any(word in slug_lower for word in ['life']):
            return "Life Insurance"
        elif any(word in slug_lower for word in ['health']):
            return "Health Insurance"
        elif any(word in slug_lower for word in ['business']):
            return "Business Insurance"
        elif any(word in slug_lower for word in ['auto', 'car', 'vehicle']):
            return "Auto Insurance"
        elif any(word in slug_lower for word in ['home', 'homeowners', 'property']):
            return "Home Insurance"
        elif any(word in slug_lower for word in ['mortgage', 'loan']):
            return "Mortgage Calculator"
        elif any(word in slug_lower for word in ['bmi', 'calorie', 'fitness']):
            return "Health Calculator"
        elif any(word in slug_lower for word in ['legal', 'injury', 'divorce']):
            return "Legal Calculator"
        else:
            return "Insurance Calculator"

    def generate_unique_tool_config(self, slug: str, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to generate unique form fields and configuration"""

        tool_type = self.extract_tool_type_from_slug(slug)

        prompt = f"""
You are an expert tool designer. Analyze this URL slug and create a UNIQUE tool configuration.

URL SLUG: {slug}
DETECTED TOOL TYPE: {tool_type}
TARGET COUNTRY: {country_data['name']} (Language: {country_data['language']}, Currency: {country_data['currency']})

REQUIREMENTS:
1. Create EXACTLY 5-6 form fields (minimum 5 fields)
2. Always include location as first field (using {country_data['local_term']})
3. Make this tool GENUINELY DIFFERENT from similar tools
4. Focus on SPECIFIC user needs that this exact slug suggests

OUTPUT FORMAT (STRICT JSON):
{{
    "specialty": "Specific tool name",
    "target_audience": "Specific group this serves",
    "unique_value": "What makes this tool different",
    "category": "Main category",
    "icon": "Single emoji",
    "form_fields": [
        {{
            "name": "location",
            "label": "{country_data['local_term'].title()}",
            "type": "text",
            "icon": "📍",
            "required": true,
            "placeholder": "Enter your {country_data['local_term']}"
        }},
        // ADD 4-5 MORE SPECIALIZED FIELDS HERE
    ],
    "key_insights": ["Insight 1", "Insight 2", "Insight 3", "Insight 4"],
    "target_keywords": ["{tool_type.lower()}", "{country_data['name'].lower()}", "calculator"]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "You are an expert at creating unique calculation tools. You ALWAYS create exactly 5-6 form fields per tool."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
            else:
                result = json.loads(content)

            # Ensure minimum fields
            if len(result.get('form_fields', [])) < 4:
                return self.get_enhanced_fallback_config(slug, country_data, tool_type)

            # Add metadata
            result["country_data"] = country_data
            result["slug"] = slug
            result["tool_type"] = tool_type
            result["generated_date"] = datetime.now().isoformat()

            return result

        except Exception as e:
            print(f"⚠️ OpenAI error for {slug}: {str(e)}")
            return self.get_enhanced_fallback_config(slug, country_data, tool_type)

    def get_enhanced_fallback_config(self, slug: str, country_data: Dict[str, Any], tool_type: str) -> Dict[str, Any]:
        """Enhanced fallback with 5-6 specialized fields"""

        # Auto insurance fallback
        form_fields = [
            {
                "name": "location",
                "label": country_data["local_term"].title(),
                "type": "text",
                "icon": "📍",
                "required": True,
                "placeholder": f"Enter your {country_data['local_term']}"
            },
            {
                "name": "driver_age",
                "label": "Driver Age",
                "type": "slider",
                "icon": "👤",
                "required": True,
                "min": "16",
                "max": "80",
                "default": "35"
            },
            {
                "name": "vehicle_year",
                "label": "Vehicle Year",
                "type": "select",
                "icon": "📅",
                "required": True,
                "options": ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "Older"]
            },
            {
                "name": "coverage_amount",
                "label": "Desired Coverage Amount",
                "type": "currency_slider",
                "icon": "💰",
                "required": True,
                "min": "25000",
                "max": "1000000",
                "default": "100000"
            },
            {
                "name": "driving_record",
                "label": "Driving Record",
                "type": "select",
                "icon": "🚗",
                "required": True,
                "options": ["Clean Record", "1 Minor Violation", "2+ Violations", "Accident History"]
            },
            {
                "name": "annual_mileage",
                "label": "Annual Mileage",
                "type": "slider",
                "icon": "🛣️",
                "required": True,
                "min": "5000",
                "max": "50000",
                "default": "15000"
            }
        ]

        return {
            "specialty": f"{tool_type} Specialist",
            "target_audience": f"{tool_type.lower()} seekers",
            "unique_value": f"specialized {tool_type.lower()} analysis",
            "category": "insurance",
            "icon": "🛡️",
            "country_data": country_data,
            "slug": slug,
            "tool_type": tool_type,
            "generated_date": datetime.now().isoformat(),
            "form_fields": form_fields,
            "key_insights": [
                f"Optimized for {country_data['name']} regulations",
                f"Save up to {country_data['currency']}{country_data['savings']:,} annually",
                "Instant AI-powered analysis",
                "Personalized recommendations"
            ],
            "target_keywords": [tool_type.lower(), country_data["name"].lower(), "calculator"]
        }

    def generate_html_form(self, tool_config: Dict[str, Any]) -> str:
        """Generate HTML form from tool configuration"""

        country_data = tool_config["country_data"]
        form_fields = tool_config["form_fields"]

        form_html = f'''
    <div class="enhanced-form global-{country_data["code"].lower()}">
        <div class="form-header">
            <div class="country-flag">{self.get_country_flag(country_data["code"])}</div>
            <h2>{tool_config["icon"]} {tool_config["specialty"]}</h2>
            <p>Specialized for {country_data["name"]} - {tool_config["target_audience"]}</p>
            <div class="unique-value">{tool_config["unique_value"]}</div>
            <div class="urgency-badge">Save {country_data["currency"]}{country_data["savings"]:,}/year!</div>
        </div>

        <form id="tool-form" onsubmit="calculateResults(event)">
            <div class="form-grid">'''

        # Generate each form field
        for field in form_fields:
            form_html += self.generate_field_html(field, country_data["currency"])

        form_html += f'''
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">
                    <span class="btn-icon">🚀</span>
                    Get My {country_data["currency"]}{country_data["savings"]:,} Analysis
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
            options = field.get('options', ['Option 1', 'Option 2', 'Option 3'])
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

    def generate_complete_page(self, tool_config: Dict[str, Any], form_html: str) -> str:
        """Generate complete page content"""

        country_data = tool_config["country_data"]

        return f'''
        <div class="hero-section">
            <div class="country-flag">{self.get_country_flag(country_data["code"])}</div>
            <h1>{tool_config["icon"]} {tool_config["specialty"]}</h1>
            <p>{tool_config["unique_value"]} - Specialized for {country_data["name"]} {tool_config["target_audience"]}</p>
        </div>

        <div class="tool-interface">
            {form_html}
        </div>

        <div class="results-container">
            <div id="tool-results" class="tool-results">
                <div class="results-placeholder">
                    <h3>📊 Your {country_data["name"]} Analysis Will Appear Here</h3>
                </div>
            </div>
        </div>

        <script>
        const TOOL_CONFIG = {{
            "slug": "{tool_config['slug']}",
            "category": "{tool_config['category']}",
            "specialty": "{tool_config['specialty']}",
            "target_audience": "{tool_config['target_audience']}",
            "unique_value": "{tool_config['unique_value']}",
            "rpm": {country_data['rpm']},
            "target_country": "{country_data['code']}",
            "country_data": {json.dumps(country_data)},
            "form_fields": {json.dumps(tool_config['form_fields'])},
            "key_insights": {json.dumps(tool_config['key_insights'])},
            "target_keywords": {json.dumps(tool_config['target_keywords'])},
            "generated_date": "{tool_config['generated_date']}"
        }};
        </script>
        '''

    def process_single_tool_concurrent(self, slug: str, country_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Process a single tool - for concurrent execution"""

        try:
            print(f"🔄 Processing {index}: {slug[:50]}...")

            # Generate unique tool config
            tool_config = self.generate_unique_tool_config(slug, country_data)

            print(f"   ✅ Generated: {tool_config['specialty']}")
            print(f"   📝 Fields: {[f['name'] for f in tool_config['form_fields']]}")

            # Generate HTML form and complete page
            form_html = self.generate_html_form(tool_config)
            page_content = self.generate_complete_page(tool_config, form_html)

            # Return CSV row data
            return {
                "post_title": f"{tool_config['specialty']} - {country_data['name']} 2025",
                "post_name": slug,
                "post_content": page_content,
                "post_excerpt": f"{tool_config['unique_value']} for {country_data['name']} residents.",
                "post_status": "publish",
                "post_type": "page",
                "menu_order": index,
                "rank_math_title": f"#{1} {tool_config['specialty']} - {country_data['code']} 2025",
                "rank_math_description": f"{tool_config['unique_value']} for {country_data['name']}. Save {country_data['currency']}{country_data['savings']:,}/year.",
                "rank_math_focus_keyword": f"{tool_config.get('tool_type', tool_config['category'])} {country_data['code'].lower()}",
                "rank_math_keywords": ",".join(tool_config['target_keywords'][:10]),
                "meta:tool_category": tool_config['category'],
                "meta:tool_rpm": country_data['rpm'],
                "meta:target_country": country_data['code'],
                "meta:generated_with": "openai_concurrent",
                "meta:field_count": len(tool_config['form_fields']),
                "meta:generated_date": tool_config['generated_date'],
                "categories": f"AI Tools,{country_data['name']} Tools,{tool_config['category'].title()} Calculators",
                "tags": ",".join(tool_config['target_keywords']),
                "featured_image": f"{tool_config['category']}-calculator-{country_data['code'].lower()}.jpg"
            }

        except Exception as e:
            print(f"❌ Error processing {slug}: {e}")
            # Use fallback
            tool_config = self.get_enhanced_fallback_config(slug, country_data, self.extract_tool_type_from_slug(slug))
            form_html = self.generate_html_form(tool_config)
            page_content = self.generate_complete_page(tool_config, form_html)

            return {
                "post_title": f"{tool_config['specialty']} - {country_data['name']} 2025",
                "post_name": slug,
                "post_content": page_content,
                "post_excerpt": f"{tool_config['unique_value']} for {country_data['name']} residents.",
                "post_status": "publish",
                "post_type": "page",
                "menu_order": index,
                "rank_math_title": f"#{1} {tool_config['specialty']} - {country_data['code']} 2025",
                "rank_math_description": f"{tool_config['unique_value']} for {country_data['name']}.",
                "rank_math_focus_keyword": f"{tool_config.get('tool_type', tool_config['category'])} {country_data['code'].lower()}",
                "rank_math_keywords": ",".join(tool_config['target_keywords'][:10]),
                "meta:tool_category": tool_config['category'],
                "meta:tool_rpm": country_data['rpm'],
                "meta:target_country": country_data['code'],
                "meta:generated_with": "fallback_concurrent",
                "meta:field_count": len(tool_config['form_fields']),
                "meta:generated_date": tool_config['generated_date'],
                "categories": f"AI Tools,{country_data['name']} Tools,{tool_config['category'].title()} Calculators",
                "tags": ",".join(tool_config['target_keywords']),
                "featured_image": f"{tool_config['category']}-calculator-{country_data['code'].lower()}.jpg"
            }

    def process_all_urls_concurrent(self, input_csv: str, output_csv: str, test_mode: bool = True,
                                    max_workers: int = 10):
        """Process URLs using concurrent individual API calls with built-in save"""

        print("🚀 Starting Concurrent OpenAI Tool Generation...")
        print("=" * 80)

        # Read URLs from CSV
        with open(input_csv, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            slugs = [row['post_name'] for row in reader]

        if test_mode:
            slugs = slugs[:3]
            print("🧪 TEST MODE: Processing only first 3 URLs")

        print(f"📊 Processing {len(slugs)} URLs with {max_workers} concurrent workers")
        print(f"💰 Estimated cost: ${len(slugs) * 0.0005:.3f}")

        start_time = time.time()
        csv_data = []

        # Prepare tasks
        tasks = []
        for i, slug in enumerate(slugs):
            country_data = self.high_rpm_countries[i % len(self.high_rpm_countries)]
            tasks.append((slug, country_data, i))

        # Process concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.process_single_tool_concurrent, slug, country_data, index): (slug, index)
                for slug, country_data, index in tasks
            }

            # Collect results
            for future in as_completed(future_to_task):
                slug, index = future_to_task[future]
                try:
                    result = future.result()
                    csv_data.append(result)
                    print(f"✅ Completed {index + 1}/{len(slugs)}: {slug}")
                except Exception as e:
                    print(f"❌ Failed {index + 1}/{len(slugs)}: {slug} - {e}")

        # Sort by menu_order
        csv_data.sort(key=lambda x: x['menu_order'])

        # SAVE FILES DIRECTLY HERE
        print(f"\n💾 SAVING {len(csv_data)} TOOLS...")

        # Save CSV
        fieldnames = [
            "post_title", "post_name", "post_content", "post_excerpt", "post_status",
            "post_type", "menu_order", "rank_math_title", "rank_math_description",
            "rank_math_focus_keyword", "rank_math_keywords", "meta:tool_category",
            "meta:tool_rpm", "meta:target_country", "meta:generated_with", "meta:field_count",
            "meta:generated_date", "categories", "tags", "featured_image"
        ]

        csv_path = os.path.abspath(output_csv)
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)

        print(f"✅ CSV saved: {csv_path}")
        print(f"📊 Rows: {len(csv_data)}, Size: {os.path.getsize(csv_path):,} bytes")

        # Save tools_config.json
        tools_config = {}
        for item in csv_data:
            slug = item["post_name"]

            # Extract form fields from HTML
            field_pattern = r'name="([^"]+)"'
            form_fields = [f for f in re.findall(field_pattern, item["post_content"])
                           if f not in {'tool-form', 'submit', 'reset'}]

            tools_config[slug] = {
                "category": item.get("meta:tool_category", "insurance"),
                "base_name": item["post_title"].split(" - ")[0],
                "variation": self.get_variation_from_slug(slug),
                "rpm": float(item.get("meta:tool_rpm", 25)),
                "openai_prompt_template": f"As an expert {item.get('meta:tool_category', 'insurance')} advisor specializing in {item['post_excerpt']}, provide comprehensive analysis and actionable recommendations.",
                "form_fields": form_fields,
                "seo_data": {
                    "title": item.get("rank_math_title", item["post_title"]),
                    "description": item.get("rank_math_description", item["post_excerpt"]),
                    "keywords": item.get("rank_math_keywords", ""),
                    "h1": f"🧮 AI-Powered {item['post_title'].split(' - ')[0]}",
                    "focus_keyword": item.get("rank_math_focus_keyword", slug.split('-')[0])
                }
            }

        json_path = csv_path.replace('.csv', '_tools_config.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tools_config, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON saved: {json_path}")
        print(f"🔧 Tools: {len(tools_config)}, Size: {os.path.getsize(json_path):,} bytes")

        elapsed_time = time.time() - start_time
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"⏱️ Time: {elapsed_time / 60:.1f} minutes")
        print(f"💰 Cost: ~${len(csv_data) * 0.0005:.3f}")

    def get_variation_from_slug(self, slug: str) -> str:
        """Extract variation type from slug"""
        slug_lower = slug.lower()
        variations = {
            'calculator': 'calculator', 'estimator': 'estimator', 'analyzer': 'analyzer',
            'planner': 'planner', 'advisor': 'advisor', 'simulator': 'simulator',
            'predictor': 'predictor', 'optimizer': 'optimizer', 'tracker': 'tracker',
            'manager': 'manager', 'helper': 'helper', 'comparison': 'comparison', 'quotes': 'quotes'
        }

        for keyword, variation in variations.items():
            if keyword in slug_lower:
                return variation

        return 'calculator'  # default


# Usage
def main():
    try:
        generator = OpenAIToolGenerator()
        print("✅ OpenAI API key loaded from environment variable")
    except ValueError as e:
        print(f"❌ {e}")
        return

    # FAST CONCURRENT PROCESSING (RECOMMENDED)
    print("🚀 Starting FAST concurrent processing...")
    generator.process_all_urls_concurrent("existing_tools.csv", "fast_generated_tools.csv", test_mode=False,
                                          max_workers=5)

    # For production (1000 tools):
    # generator.process_all_urls_concurrent("existing_tools.csv", "all_tools.csv", test_mode=False, max_workers=10)


if __name__ == "__main__":
    main()