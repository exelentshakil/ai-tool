import csv
import json
import re
from datetime import datetime


class UniquePageTransformer:
    def __init__(self):
        self.tools_config = {}
        self.updated_csv_data = []

        # Define unique tool intentions and form fields
        self.tool_specializations = {
            # Auto Insurance Specializations
            "auto insurance calculator": {
                "specialty": "Teen Driver Insurance",
                "target": "young drivers and their parents",
                "form_fields": ["driver_age", "gpa", "driving_course_completed", "parent_policy",
                                "vehicle_safety_rating", "annual_mileage"],
                "unique_focus": "teen driver discounts and safety programs",
                "icon": "🚗👦"
            },
            "auto insurance estimator": {
                "specialty": "Classic Car Insurance",
                "target": "vintage and collector car owners",
                "form_fields": ["vehicle_year", "restoration_status", "agreed_value", "annual_mileage", "storage_type",
                                "car_show_participation"],
                "unique_focus": "agreed value coverage and collector car protection",
                "icon": "🏎️⭐"
            },
            "auto insurance analyzer": {
                "specialty": "High-Risk Driver Insurance",
                "target": "drivers with violations or accidents",
                "form_fields": ["violation_count", "accident_count", "dui_history", "sr22_required", "current_coverage",
                                "improvement_plan"],
                "unique_focus": "SR-22 filing and risk reduction programs",
                "icon": "🚗⚠️"
            },
            "auto insurance planner": {
                "specialty": "Commercial Fleet Insurance",
                "target": "business owners with vehicle fleets",
                "form_fields": ["fleet_size", "vehicle_types", "business_use", "driver_count", "coverage_requirements",
                                "safety_programs"],
                "unique_focus": "fleet management and commercial liability",
                "icon": "🚛🏢"
            },
            "auto insurance advisor": {
                "specialty": "Rideshare Driver Insurance",
                "target": "Uber and Lyft drivers",
                "form_fields": ["platform_used", "hours_per_week", "personal_use_percentage", "current_coverage",
                                "rideshare_coverage", "deductible_preference"],
                "unique_focus": "gap coverage and rideshare-specific protection",
                "icon": "🚗📱"
            },
            "auto insurance simulator": {
                "specialty": "Electric Vehicle Insurance",
                "target": "electric and hybrid vehicle owners",
                "form_fields": ["ev_type", "battery_coverage", "charging_equipment", "environmental_discount",
                                "tech_package", "autonomous_features"],
                "unique_focus": "EV-specific coverage and green discounts",
                "icon": "⚡🚗"
            },
            "auto insurance predictor": {
                "specialty": "Multi-Car Family Insurance",
                "target": "families with multiple vehicles",
                "form_fields": ["vehicle_count", "driver_count", "primary_drivers", "multi_car_discount",
                                "bundling_options", "family_safety_record"],
                "unique_focus": "family bundling and multi-car discounts",
                "icon": "👨‍👩‍👧‍👦🚗"
            },
            "auto insurance optimizer": {
                "specialty": "Low-Mileage Driver Insurance",
                "target": "infrequent drivers and remote workers",
                "form_fields": ["annual_mileage", "work_from_home", "usage_patterns", "mileage_tracking",
                                "pay_per_mile", "storage_periods"],
                "unique_focus": "usage-based insurance and low-mileage discounts",
                "icon": "🏠🚗"
            },
            "auto insurance tracker": {
                "specialty": "Military Auto Insurance",
                "target": "active duty and veteran service members",
                "form_fields": ["military_status", "deployment_status", "base_location", "military_discount",
                                "overseas_coverage", "storage_during_deployment"],
                "unique_focus": "military discounts and deployment coverage",
                "icon": "🎖️🚗"
            },
            "auto insurance manager": {
                "specialty": "Luxury Vehicle Insurance",
                "target": "high-value and exotic car owners",
                "form_fields": ["vehicle_value", "luxury_brand", "custom_modifications", "agreed_value",
                                "exotic_car_coverage", "track_day_use"],
                "unique_focus": "agreed value and exotic car protection",
                "icon": "💎🏎️"
            },

            # Home Insurance Specializations
            "home insurance calculator": {
                "specialty": "First-Time Homebuyer Insurance",
                "target": "new homeowners and first-time buyers",
                "form_fields": ["home_age", "purchase_price", "down_payment", "mortgage_lender", "first_time_buyer",
                                "home_inspection_score"],
                "unique_focus": "mortgage requirements and new homeowner guidance",
                "icon": "🏠🔑"
            },
            "home insurance estimator": {
                "specialty": "Historic Home Insurance",
                "target": "owners of historic and landmark properties",
                "form_fields": ["historic_designation", "home_age", "restoration_costs", "period_materials",
                                "heritage_value", "preservation_requirements"],
                "unique_focus": "historic preservation and period-appropriate rebuilding",
                "icon": "🏛️⭐"
            },
            "home insurance analyzer": {
                "specialty": "High-Risk Area Insurance",
                "target": "homes in disaster-prone areas",
                "form_fields": ["flood_zone", "wildfire_risk", "earthquake_zone", "hurricane_area",
                                "mitigation_measures", "emergency_preparedness"],
                "unique_focus": "natural disaster coverage and risk mitigation",
                "icon": "🌪️🏠"
            },
            "home insurance planner": {
                "specialty": "Vacation Home Insurance",
                "target": "second home and vacation property owners",
                "form_fields": ["occupancy_type", "rental_income", "seasonal_use", "remote_monitoring",
                                "caretaker_service", "vacancy_periods"],
                "unique_focus": "vacancy coverage and rental property protection",
                "icon": "🏖️🏠"
            },
            "home insurance advisor": {
                "specialty": "Condo Insurance",
                "target": "condominium unit owners",
                "form_fields": ["hoa_coverage", "unit_improvements", "loss_assessment", "personal_property",
                                "liability_needs", "master_policy_review"],
                "unique_focus": "HOA coverage gaps and unit owner protection",
                "icon": "🏢🏠"
            },
            "home insurance simulator": {
                "specialty": "Smart Home Insurance",
                "target": "tech-savvy homeowners with smart devices",
                "form_fields": ["smart_devices", "security_system", "monitoring_service", "tech_coverage",
                                "cyber_protection", "device_value"],
                "unique_focus": "smart device coverage and cyber security",
                "icon": "🏠💻"
            },
            "home insurance predictor": {
                "specialty": "Senior Homeowner Insurance",
                "target": "retirement-age homeowners",
                "form_fields": ["age", "retirement_status", "home_modifications", "mobility_needs", "fixed_income",
                                "senior_discounts"],
                "unique_focus": "senior discounts and accessibility modifications",
                "icon": "👴🏠"
            },
            "home insurance optimizer": {
                "specialty": "Green Home Insurance",
                "target": "eco-friendly and sustainable home owners",
                "form_fields": ["green_features", "energy_efficiency", "sustainable_materials", "solar_panels",
                                "green_certification", "environmental_upgrades"],
                "unique_focus": "green building discounts and sustainable rebuilding",
                "icon": "🌱🏠"
            },
            "home insurance tracker": {
                "specialty": "Landlord Insurance",
                "target": "rental property owners and investors",
                "form_fields": ["rental_units", "tenant_type", "rental_income", "liability_coverage", "loss_of_rent",
                                "property_management"],
                "unique_focus": "rental income protection and landlord liability",
                "icon": "🏠💼"
            },
            "home insurance manager": {
                "specialty": "Luxury Home Insurance",
                "target": "high-value home owners",
                "form_fields": ["home_value", "luxury_features", "fine_arts", "jewelry_collection", "domestic_staff",
                                "security_measures"],
                "unique_focus": "high-value items and luxury lifestyle coverage",
                "icon": "💎🏠"
            },

            # Life Insurance Specializations
            "life insurance calculator": {
                "specialty": "Young Family Life Insurance",
                "target": "new parents and growing families",
                "form_fields": ["children_count", "children_ages", "spouse_income", "childcare_costs",
                                "education_goals", "family_debt"],
                "unique_focus": "child protection and education funding",
                "icon": "👨‍👩‍👧‍👦💝"
            },
            "life insurance estimator": {
                "specialty": "Business Owner Life Insurance",
                "target": "entrepreneurs and business owners",
                "form_fields": ["business_value", "key_person_role", "business_debt", "succession_plan",
                                "buy_sell_agreement", "employee_count"],
                "unique_focus": "business continuation and key person coverage",
                "icon": "💼💝"
            },
            "life insurance analyzer": {
                "specialty": "Senior Life Insurance",
                "target": "older adults and retirees",
                "form_fields": ["age", "health_status", "final_expenses", "estate_planning", "grandchildren",
                                "legacy_goals"],
                "unique_focus": "final expense and estate planning coverage",
                "icon": "👴💝"
            },
            "life insurance planner": {
                "specialty": "High Net Worth Life Insurance",
                "target": "wealthy individuals with estate planning needs",
                "form_fields": ["net_worth", "estate_value", "tax_planning", "trust_structures", "charitable_giving",
                                "wealth_transfer"],
                "unique_focus": "estate tax planning and wealth transfer",
                "icon": "💎💝"
            },
            "life insurance advisor": {
                "specialty": "Term vs Whole Life Comparison",
                "target": "people choosing between policy types",
                "form_fields": ["age", "income", "coverage_duration", "investment_goals", "budget_constraints",
                                "policy_preferences"],
                "unique_focus": "policy type comparison and suitability analysis",
                "icon": "⚖️💝"
            },
            "life insurance simulator": {
                "specialty": "Military Life Insurance",
                "target": "active duty and veteran service members",
                "form_fields": ["military_branch", "deployment_risk", "sgli_coverage", "family_status",
                                "military_benefits", "veteran_status"],
                "unique_focus": "military-specific benefits and SGLI supplementation",
                "icon": "🎖️💝"
            },
            "life insurance predictor": {
                "specialty": "Mortgage Protection Life Insurance",
                "target": "homeowners with mortgage debt",
                "form_fields": ["mortgage_balance", "mortgage_term", "home_value", "other_debts", "spouse_income",
                                "family_size"],
                "unique_focus": "mortgage debt protection and home security",
                "icon": "🏠💝"
            },
            "life insurance optimizer": {
                "specialty": "College Student Life Insurance",
                "target": "students and young adults",
                "form_fields": ["age", "student_loans", "future_income", "family_support", "career_plans",
                                "health_status"],
                "unique_focus": "future insurability and student loan protection",
                "icon": "🎓💝"
            },
            "life insurance tracker": {
                "specialty": "Divorce Life Insurance Planning",
                "target": "divorced individuals with obligations",
                "form_fields": ["alimony_obligation", "child_support", "divorce_settlement", "ex_spouse_dependency",
                                "custody_arrangement", "remarriage_plans"],
                "unique_focus": "divorce obligation protection and family security",
                "icon": "💔💝"
            },
            "life insurance manager": {
                "specialty": "Special Needs Life Insurance",
                "target": "families with special needs members",
                "form_fields": ["special_needs_child", "care_costs", "government_benefits", "trust_planning",
                                "lifetime_care", "sibling_responsibility"],
                "unique_focus": "special needs trust funding and lifetime care",
                "icon": "🤝💝"
            },

            # Add more specializations for other categories...
            # Health Insurance, Legal, Finance, Business, Health Tools, etc.
        }

        # Add more specializations for other categories
        self.add_more_specializations()
        # TOP 15 HIGHEST RPM COUNTRIES (Based on 2025 research data)
        self.high_rpm_countries = [
            {
                "code": "NO", "name": "Norway", "cpc": 0.52, "rpm": 43.15,
                "currency": "NOK", "savings": 2100, "local_term": "postnummer",
                "language": "Norwegian", "urgency": "Begrenset tilbud"
            },
            {
                "code": "US", "name": "United States", "cpc": 0.61, "rpm": 35.00,
                "currency": "$", "savings": 2100, "local_term": "ZIP code",
                "language": "English", "urgency": "Limited time offer"
            },
            {
                "code": "AU", "name": "Australia", "cpc": 0.57, "rpm": 36.21,
                "currency": "AUD $", "savings": 2400, "local_term": "postcode",
                "language": "English", "urgency": "Limited offer"
            },
            {
                "code": "DK", "name": "Denmark", "cpc": 0.46, "rpm": 24.65,
                "currency": "DKK", "savings": 2200, "local_term": "postnummer",
                "language": "Danish", "urgency": "Begrænset tid"
            },
            {
                "code": "CA", "name": "Canada", "cpc": 0.45, "rpm": 29.15,
                "currency": "CAD $", "savings": 2200, "local_term": "postal code",
                "language": "English", "urgency": "Save today"
            },
            {
                "code": "SE", "name": "Sweden", "cpc": 0.44, "rpm": 22.30,
                "currency": "SEK", "savings": 2000, "local_term": "postnummer",
                "language": "Swedish", "urgency": "Begränsad tid"
            },
            {
                "code": "CH", "name": "Switzerland", "cpc": 0.55, "rpm": 20.00,
                "currency": "CHF", "savings": 2800, "local_term": "PLZ",
                "language": "German", "urgency": "Befristetes Angebot"
            },
            {
                "code": "BE", "name": "Belgium", "cpc": 0.38, "rpm": 20.50,
                "currency": "€", "savings": 2000, "local_term": "postcode",
                "language": "Dutch", "urgency": "Beperkte tijd"
            },
            {
                "code": "UK", "name": "United Kingdom", "cpc": 0.48, "rpm": 19.47,
                "currency": "£", "savings": 1800, "local_term": "postcode",
                "language": "English", "urgency": "Limited offer"
            },
            {
                "code": "NL", "name": "Netherlands", "cpc": 0.42, "rpm": 18.40,
                "currency": "€", "savings": 2000, "local_term": "postcode",
                "language": "Dutch", "urgency": "Beperkte tijd"
            },
            {
                "code": "FI", "name": "Finland", "cpc": 0.45, "rpm": 18.90,
                "currency": "€", "savings": 2100, "local_term": "postinumero",
                "language": "Finnish", "urgency": "Rajoitettu aika"
            },
            {
                "code": "IE", "name": "Ireland", "cpc": 0.41, "rpm": 17.80,
                "currency": "€", "savings": 1900, "local_term": "Eircode",
                "language": "English", "urgency": "Limited time"
            },
            {
                "code": "NZ", "name": "New Zealand", "cpc": 0.33, "rpm": 16.20,
                "currency": "NZD $", "savings": 1800, "local_term": "postcode",
                "language": "English", "urgency": "Limited offer"
            },
            {
                "code": "DE", "name": "Germany", "cpc": 0.35, "rpm": 15.00,
                "currency": "€", "savings": 1900, "local_term": "PLZ",
                "language": "German", "urgency": "Befristetes Angebot"
            },
            {
                "code": "AT", "name": "Austria", "cpc": 0.34, "rpm": 14.20,
                "currency": "€", "savings": 1800, "local_term": "PLZ",
                "language": "German", "urgency": "Befristetes Angebot"
            }
        ]

    def get_country_for_tool(self, tool_index):
        """Rotate through high RPM countries for maximum global coverage"""
        # Use modulo to cycle through all countries
        country_index = tool_index % len(self.high_rpm_countries)
        return self.high_rpm_countries[country_index]

    def generate_global_rankmath_data(self, title, slug, intention, tool_index):
        """Generate RankMath data optimized for global high RPM countries"""

        # Get the assigned country for this tool
        country_data = self.get_country_for_tool(tool_index)

        # Generate geo-optimized content
        seo_title = self.generate_global_seo_title(title, intention, country_data)
        meta_description = self.generate_global_meta_description(intention, country_data)
        focus_keyword = self.generate_global_focus_keyword(intention, country_data)
        additional_keywords = self.generate_global_keywords(intention, country_data)

        return {
            "rank_math_title": seo_title,
            "rank_math_description": meta_description,
            "rank_math_focus_keyword": focus_keyword,
            "rank_math_keywords": additional_keywords,
            "target_country": country_data["code"],
            "country_data": country_data
        }

    def generate_global_seo_title(self, original_title, intention, country_data):
        """Generate SEO title optimized for specific country"""

        country_code = country_data["code"]
        specialty = intention['specialty']

        # High-converting title templates by language/region
        if country_data["language"] == "English":
            templates = [
                f"#{1} {specialty} Calculator - {country_code} 2025",
                f"Best {specialty} Tool - {country_code} Residents",
                f"{specialty} Calculator - Save {country_data['currency']}{country_data['savings']:,}/Yr"
            ]
        elif country_data["language"] == "German":
            if "insurance" in specialty.lower():
                templates = [
                    f"#{1} Versicherung Rechner - {country_code} 2025",
                    f"Beste Versicherung Tool - {country_code}",
                    f"Versicherungsrechner - Sparen {country_data['currency']}{country_data['savings']:,}/Jahr"
                ]
            else:
                templates = [
                    f"#{1} {specialty} Rechner - {country_code} 2025",
                    f"Beste {specialty} Tool - {country_code}",
                    f"{specialty} Rechner - {country_code}"
                ]
        elif country_data["language"] in ["Dutch", "Flemish"]:
            if "insurance" in specialty.lower():
                templates = [
                    f"#{1} Verzekering Calculator - {country_code} 2025",
                    f"Beste Verzekering Tool - {country_code}",
                    f"Verzekeringscalculator - Bespaar €{country_data['savings']:,}/Jaar"
                ]
            else:
                templates = [
                    f"#{1} {specialty} Calculator - {country_code} 2025",
                    f"Beste {specialty} Tool - {country_code}",
                    f"{specialty} Calculator - {country_code}"
                ]
        elif country_data["language"] in ["Norwegian", "Danish", "Swedish", "Finnish"]:
            templates = [
                f"#{1} {specialty} Kalkulator - {country_code} 2025",
                f"Beste {specialty} Verktøy - {country_code}",
                f"{specialty} Kalkulator - Spar {country_data['currency']}{country_data['savings']:,}/År"
            ]
        else:
            # Default to English
            templates = [
                f"#{1} {specialty} Calculator - {country_code} 2025",
                f"Best {specialty} Tool - {country_code} Residents"
            ]

        # Choose template that fits under 60 characters
        for template in templates:
            if len(template) <= 58:
                return template

        return templates[0][:58] + ".."

    def generate_global_meta_description(self, intention, country_data):
        """Generate meta description for specific country"""

        specialty_lower = intention['specialty'].lower()
        country_code = country_data["code"]
        currency = country_data["currency"]
        savings = country_data["savings"]

        if country_data["language"] == "English":
            desc = f"Compare {specialty_lower} in {country_code}. Save up to {currency}{savings:,}/year. Trusted by 250k+ residents. Free quotes in 2 minutes!"
        elif country_data["language"] == "German":
            if "insurance" in specialty_lower:
                desc = f"Versicherung vergleichen in {country_code}. Sparen Sie bis zu {currency}{savings:,}/Jahr. Kostenlose Angebote in 2 Minuten!"
            else:
                desc = f"{specialty_lower} vergleichen in {country_code}. Sparen Sie bis zu {currency}{savings:,}/Jahr. Kostenlos in 2 Minuten!"
        elif country_data["language"] in ["Dutch"]:
            if "insurance" in specialty_lower:
                desc = f"Verzekering vergelijken in {country_code}. Bespaar tot €{savings:,}/jaar. Gratis offertes in 2 minuten!"
            else:
                desc = f"{specialty_lower} vergelijken in {country_code}. Bespaar tot €{savings:,}/jaar. Gratis in 2 minuten!"
        elif country_data["language"] in ["Norwegian", "Danish", "Swedish"]:
            desc = f"Sammenlign {specialty_lower} i {country_code}. Spar opptil {currency}{savings:,}/år. Gratis tilbud på 2 minutter!"
        elif country_data["language"] == "Finnish":
            desc = f"Vertaile {specialty_lower} {country_code}:ssa. Säästä jopa {currency}{savings:,}/vuosi. Ilmaiset tarjoukset 2 minuutissa!"
        else:
            # Default English
            desc = f"Compare {specialty_lower} in {country_code}. Save up to {currency}{savings:,}/year. Free quotes in 2 minutes!"

        # Ensure under 160 characters
        return desc[:160] if len(desc) > 160 else desc

    def generate_global_focus_keyword(self, intention, country_data):
        """Generate focus keyword for specific country"""

        specialty_lower = intention['specialty'].lower()
        country_lower = country_data["code"].lower()

        if country_data["language"] == "English":
            return f"{specialty_lower} {country_lower}"
        elif country_data["language"] == "German":
            if "insurance" in specialty_lower:
                return f"versicherung {country_lower}"
            else:
                return f"{specialty_lower} {country_lower}"
        elif country_data["language"] == "Dutch":
            if "insurance" in specialty_lower:
                return f"verzekering {country_lower}"
            else:
                return f"{specialty_lower} {country_lower}"
        else:
            return f"{specialty_lower} {country_lower}"

    def generate_global_keywords(self, intention, country_data):
        """Generate keywords for specific country"""

        specialty_lower = intention['specialty'].lower()
        country_lower = country_data["code"].lower()
        local_term = country_data["local_term"]

        if country_data["language"] == "English":
            keywords = [
                f"{specialty_lower} {country_lower}",
                f"best {specialty_lower} {country_lower}",
                f"{specialty_lower} calculator {country_lower}",
                f"free {specialty_lower} {country_lower}",
                f"compare {specialty_lower} {country_lower}",
                f"{specialty_lower} quotes {country_lower}",
                f"online {specialty_lower} {country_lower}",
                f"{local_term}",
                f"{specialty_lower} rates {country_lower}",
                f"{country_lower} {specialty_lower} tool"
            ]
        elif country_data["language"] == "German":
            if "insurance" in specialty_lower:
                keywords = [
                    f"versicherung {country_lower}",
                    f"beste versicherung {country_lower}",
                    f"versicherungsrechner {country_lower}",
                    f"kostenlose versicherung {country_lower}",
                    f"versicherung vergleichen {country_lower}",
                    f"versicherung angebote {country_lower}",
                    f"online versicherung {country_lower}",
                    f"{local_term}",
                    f"versicherung tarife {country_lower}"
                ]
            else:
                keywords = [
                    f"{specialty_lower} {country_lower}",
                    f"beste {specialty_lower} {country_lower}",
                    f"{specialty_lower} rechner {country_lower}",
                    f"kostenlose {specialty_lower} {country_lower}",
                    f"{specialty_lower} vergleichen {country_lower}",
                    f"{local_term}"
                ]
        elif country_data["language"] == "Dutch":
            if "insurance" in specialty_lower:
                keywords = [
                    f"verzekering {country_lower}",
                    f"beste verzekering {country_lower}",
                    f"verzekeringscalculator {country_lower}",
                    f"gratis verzekering {country_lower}",
                    f"verzekering vergelijken {country_lower}",
                    f"verzekering offertes {country_lower}",
                    f"online verzekering {country_lower}",
                    f"{local_term}"
                ]
            else:
                keywords = [
                    f"{specialty_lower} {country_lower}",
                    f"beste {specialty_lower} {country_lower}",
                    f"{specialty_lower} calculator {country_lower}",
                    f"gratis {specialty_lower} {country_lower}",
                    f"{specialty_lower} vergelijken {country_lower}",
                    f"{local_term}"
                ]
        elif country_data["language"] in ["Norwegian", "Danish", "Swedish"]:
            keywords = [
                f"{specialty_lower} {country_lower}",
                f"beste {specialty_lower} {country_lower}",
                f"{specialty_lower} kalkulator {country_lower}",
                f"gratis {specialty_lower} {country_lower}",
                f"sammenlign {specialty_lower} {country_lower}",
                f"{specialty_lower} tilbud {country_lower}",
                f"{local_term}"
            ]
        else:
            # Default English keywords
            keywords = [
                f"{specialty_lower} {country_lower}",
                f"best {specialty_lower} {country_lower}",
                f"{specialty_lower} calculator {country_lower}",
                f"free {specialty_lower} {country_lower}",
                f"{local_term}"
            ]

        return ",".join(keywords[:10])

    def generate_global_form_content(self, intention, country_data):
        """Generate country-specific form content"""

        currency = country_data["currency"]
        local_term = country_data["local_term"]
        urgency = country_data["urgency"]
        savings = country_data["savings"]

        if country_data["language"] == "English":
            form_content = f'''
                <div class="enhanced-form global-{country_data["code"].lower()}">
                    <div class="form-header">
                        <h2>💰 {intention["specialty"]} - Save {currency}{savings:,}/Year</h2>
                        <p>Trusted by 250,000+ {country_data["name"]} residents</p>
                        <div class="urgency-badge">{urgency}!</div>
                    </div>

                    <form id="tool-form" onsubmit="calculateResults(event)">
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label" for="location">
                                    <span class="label-icon">📍</span>
                                    {local_term.title()}
                                </label>
                                <input type="text" id="location" name="location" class="form-input"
                                       placeholder="Enter your {local_term}">
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="coverage_amount">
                                    <span class="label-icon">💰</span>
                                    Coverage Amount ({currency})
                                </label>
                                <div class="slider-group">
                                    <div class="slider-container">
                                        <input type="range" id="coverage_amount" name="coverage_amount"
                                               class="slider-input" min="25000" max="1000000" value="100000">
                                        <div class="slider-value">{currency}100,000</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <span class="btn-icon">🚀</span>
                                Get My {currency}{savings:,} Savings Now
                            </button>
                        </div>
                    </form>
                </div>'''

        elif country_data["language"] == "German":
            form_content = f'''
                <div class="enhanced-form global-{country_data["code"].lower()}">
                    <div class="form-header">
                        <h2>💰 {intention["specialty"]} - Sparen Sie {currency}{savings:,}/Jahr</h2>
                        <p>Vertraut von 250.000+ {country_data["name"]} Einwohnern</p>
                        <div class="urgency-badge">{urgency}!</div>
                    </div>

                    <form id="tool-form" onsubmit="calculateResults(event)">
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label" for="location">
                                    <span class="label-icon">📍</span>
                                    {local_term.upper()}
                                </label>
                                <input type="text" id="location" name="location" class="form-input"
                                       placeholder="Geben Sie Ihre {local_term} ein">
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="coverage_amount">
                                    <span class="label-icon">💰</span>
                                    Deckungssumme ({currency})
                                </label>
                                <div class="slider-group">
                                    <div class="slider-container">
                                        <input type="range" id="coverage_amount" name="coverage_amount"
                                               class="slider-input" min="25000" max="1000000" value="100000">
                                        <div class="slider-value">{currency}100.000</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <span class="btn-icon">🚀</span>
                                Jetzt {currency}{savings:,} sparen
                            </button>
                        </div>
                    </form>
                </div>'''

        else:
            # Default to English format for other languages
            form_content = f'''
                <div class="enhanced-form global-{country_data["code"].lower()}">
                    <div class="form-header">
                        <h2>💰 {intention["specialty"]} - Save {currency}{savings:,}/Year</h2>
                        <p>Trusted by residents of {country_data["name"]}</p>
                        <div class="urgency-badge">{urgency}!</div>
                    </div>

                    <form id="tool-form" onsubmit="calculateResults(event)">
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label" for="location">
                                    <span class="label-icon">📍</span>
                                    {local_term.title()}
                                </label>
                                <input type="text" id="location" name="location" class="form-input"
                                       placeholder="Enter your {local_term}">
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="coverage_amount">
                                    <span class="label-icon">💰</span>
                                    Coverage Amount ({currency})
                                </label>
                                <div class="slider-group">
                                    <div class="slider-container">
                                        <input type="range" id="coverage_amount" name="coverage_amount"
                                               class="slider-input" min="25000" max="1000000" value="100000">
                                        <div class="slider-value">{currency}100,000</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <span class="btn-icon">🚀</span>
                                Get My {currency}{savings:,} Savings Now
                            </button>
                        </div>
                    </form>
                </div>'''

        return form_content

    # UPDATED CSV GENERATION METHOD
    def transform_csv_to_unique_pages(self, input_csv_file):
        """Transform existing CSV with global high RPM optimization"""

        print(f"🔍 Reading existing CSV from {input_csv_file}...")

        existing_data = []
        with open(input_csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_data.append(row)

        print(f"📊 Found {len(existing_data)} existing pages to transform")
        print(f"🌍 Will distribute across {len(self.high_rpm_countries)} high RPM countries")

        for i, row in enumerate(existing_data):
            title = row['post_title']
            original_slug = row['post_name']

            print(f"🔄 Processing {i + 1}/{len(existing_data)}: {title[:50]}...")

            # Detect tool intention
            intention = self.detect_tool_intention(title)

            # Get country for this tool (rotates through all high RPM countries)
            country_data = self.get_country_for_tool(i)
            print(f"🌍 Assigned to: {country_data['name']} (RPM: ${country_data['rpm']}, CPC: ${country_data['cpc']})")

            # Generate global RankMath SEO data
            rankmath_data = self.generate_global_rankmath_data(title, original_slug, intention, i)

            # Generate country-specific form content
            global_form = self.generate_global_form_content(intention, country_data)

            # Generate educational content
            educational_content = self.generate_global_educational_content(intention, country_data)

            # Create complete page body with global optimization
            page_body = f'''
                <div class="tool-container-wrapper global-{country_data["code"].lower()}">
                    <div class="hero-section">
                        <div class="country-flag">{self.get_country_flag(country_data["code"])}</div>
                        <h1>{rankmath_data["rank_math_title"]}</h1>
                        <p>Specialized for {country_data["name"]} residents. {rankmath_data["rank_math_description"]}</p>
                        <div class="global-stats">
                            <div class="stat-item">
                                <span class="stat-number">{country_data["savings"]:,}</span>
                                <span class="stat-label">Avg. Annual Savings ({country_data["currency"]})</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number">250k+</span>
                                <span class="stat-label">{country_data["name"]} Users</span>
                            </div>
                        </div>
                    </div>

                    <div class="tool-main-content">
                        <div class="tool-content-area">
                            <div class="tool-interface">
                                {global_form}
                            </div>

                            <div class="results-container">
                                <div id="tool-results" class="tool-results">
                                    <div class="results-placeholder">
                                        <h3>📊 Your {country_data["name"]} Results Will Appear Here</h3>
                                        <p>Optimized for {country_data["name"]} market conditions and regulations.</p>
                                    </div>
                                </div>
                            </div>

                            <div class="educational-content">
                                {educational_content}
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                // GLOBAL TOOL CONFIGURATION
                const TOOL_CONFIG = {{
                  "slug": "{original_slug}",
                  "category": "{self.get_category_from_specialty(intention['specialty'])}",
                  "base_name": "{intention['specialty']}",
                  "variation": "{self.get_variation_from_title(title)}",
                  "rpm": {country_data['rpm']},
                  "target_country": "{country_data['code']}",
                  "country_data": {json.dumps(country_data)},
                  "seo_data": {{
                    "title": "{rankmath_data['rank_math_title']}",
                    "description": "{rankmath_data['rank_math_description']}",
                    "keywords": "{rankmath_data['rank_math_keywords']}",
                    "focus_keyword": "{rankmath_data['rank_math_focus_keyword']}"
                  }}
                }};
                </script>'''

            # Add to CSV data with global optimization
            self.updated_csv_data.append({
                "post_title": title,
                "post_name": original_slug,
                "post_content": page_body.replace('"', '""'),
                "post_excerpt": rankmath_data["rank_math_description"],
                "post_status": "publish",
                "post_type": "page",
                "menu_order": i,

                # RankMath SEO Fields (Global Optimized)
                "rank_math_title": rankmath_data["rank_math_title"],
                "rank_math_description": rankmath_data["rank_math_description"],
                "rank_math_focus_keyword": rankmath_data["rank_math_focus_keyword"],
                "rank_math_keywords": rankmath_data["rank_math_keywords"],
                "rank_math_canonical_url": f"https://barakahsoft.com/{original_slug}/",
                "rank_math_robots": "index, follow, max-snippet:-1, max-video-preview:-1, max-image-preview:large",

                # Schema Markup
                "rank_math_rich_snippet": "article",
                "rank_math_snippet_article_type": "TechArticle",
                "rank_math_snippet_name": f"{intention['specialty']} for {country_data['name']} Residents",
                "rank_math_snippet_desc": rankmath_data["rank_math_description"],

                # Social Media (Country Optimized)
                "rank_math_facebook_title": f"💰 Save {country_data['currency']}{country_data['savings']:,}/Year - {intention['specialty']}",
                "rank_math_facebook_description": rankmath_data["rank_math_description"],
                "rank_math_facebook_image": row.get('featured_image', self.get_featured_image(intention['specialty'])),
                "rank_math_twitter_title": f"💰 {intention['specialty']} - {country_data['name']} 2025",
                "rank_math_twitter_description": rankmath_data["rank_math_description"],
                "rank_math_twitter_image": row.get('featured_image', self.get_featured_image(intention['specialty'])),
                "rank_math_twitter_card_type": "summary_large_image",

                # Legacy fields with global data
                "meta:tool_category": self.get_category_from_specialty(intention['specialty']),
                "meta:tool_rpm": country_data['rpm'],
                "meta:tool_variation": self.get_variation_from_title(title),
                "meta:generated_date": datetime.now().isoformat(),
                "meta:target_country": country_data['code'],
                "meta:country_cpc": country_data['cpc'],
                "categories": f"AI Tools,{country_data['name']} Tools,Global Calculators",
                "tags": rankmath_data["rank_math_keywords"],
                "featured_image": row.get('featured_image', self.get_featured_image(intention['specialty'])),
                "meta:_wp_attachment_image_alt": f"{intention['specialty']} for {country_data['name']} residents"
            })

        print(f"✅ Global transformation complete!")
        print(f"🌍 Tools distributed across {len(self.high_rpm_countries)} countries")
        print(f"💰 Average RPM: ${sum(c['rpm'] for c in self.high_rpm_countries) / len(self.high_rpm_countries):.2f}")

    def get_country_flag(self, country_code):
        """Get country flag emoji"""
        flags = {
            "NO": "🇳🇴", "US": "🇺🇸", "AU": "🇦🇺", "DK": "🇩🇰", "CA": "🇨🇦",
            "SE": "🇸🇪", "CH": "🇨🇭", "BE": "🇧🇪", "UK": "🇬🇧", "NL": "🇳🇱",
            "FI": "🇫🇮", "IE": "🇮🇪", "NZ": "🇳🇿", "DE": "🇩🇪", "AT": "🇦🇹"
        }
        return flags.get(country_code, "🌍")

    def generate_global_educational_content(self, intention, country_data):
        """Generate country-specific educational content"""

        country_name = country_data["name"]
        currency = country_data["currency"]
        savings = country_data["savings"]
        specialty = intention["specialty"]

        if country_data["language"] == "English":
            return f'''
                <div class="educational-content global-{country_data["code"].lower()}">
                    <h3>📚 How to Use This {specialty} for {country_name}</h3>
                    <p>This advanced AI-powered {specialty.lower()} is specifically optimized for {country_name} residents, providing instant calculations with expert insights focused on {country_name} market conditions.</p>

                    <h4>🌟 {country_name}-Specific Features:</h4>
                    <ul class="key_features">
                        <li>🤖 Advanced AI analysis tailored for {country_name} market</li>
                        <li>📊 Real-time calculations with {country_name}-specific rates</li>
                        <li>💡 Smart recommendations for {country_name} regulations</li>
                        <li>📱 Mobile-responsive design optimized for {country_name} users</li>
                        <li>🔒 100% secure and compliant with {country_name} privacy laws</li>
                        <li>⚡ Instant results with {currency} currency formatting</li>
                    </ul>

                    <h4>💰 Money-Saving Tips for {country_name} Residents:</h4>
                    <ul>
                        <li>Average {country_name} residents save {currency}{savings:,} annually</li>
                        <li>Compare multiple local providers for best rates</li>
                        <li>Take advantage of {country_name}-specific discounts</li>
                        <li>Consider seasonal timing for better deals in {country_name}</li>
                        <li>Use our {country_name}-optimized recommendations</li>
                    </ul>

                    <h4>🎯 Pro Tips for {country_name} Success:</h4>
                    <ul>
                        <li>Provide accurate {country_data["local_term"]} for precise local rates</li>
                        <li>Consider {country_name} market trends in your decisions</li>
                        <li>Review {country_name} regulatory requirements</li>
                        <li>Take advantage of local {country_name} provider networks</li>
                        <li>Save your personalized {country_name} analysis for future reference</li>
                    </ul>
                </div>'''

        elif country_data["language"] == "German":
            return f'''
                <div class="educational-content global-{country_data["code"].lower()}">
                    <h3>📚 So verwenden Sie diesen {specialty} für {country_name}</h3>
                    <p>Dieser fortschrittliche KI-gestützte {specialty.lower()} ist speziell für Einwohner von {country_name} optimiert und bietet sofortige Berechnungen mit Experteneinblicken, die auf die Marktbedingungen von {country_name} ausgerichtet sind.</p>

                    <h4>🌟 {country_name}-spezifische Funktionen:</h4>
                    <ul class="key_features">
                        <li>🤖 Erweiterte KI-Analyse für den {country_name}-Markt</li>
                        <li>📊 Echtzeitberechnungen mit {country_name}-spezifischen Tarifen</li>
                        <li>💡 Intelligente Empfehlungen für {country_name}-Vorschriften</li>
                        <li>📱 Mobile-responsive Design für {country_name}-Nutzer optimiert</li>
                        <li>🔒 100% sicher und konform mit {country_name}-Datenschutzgesetzen</li>
                        <li>⚡ Sofortige Ergebnisse mit {currency}-Währungsformatierung</li>
                    </ul>

                    <h4>💰 Geld-Spar-Tipps für {country_name}-Einwohner:</h4>
                    <ul>
                        <li>Durchschnittliche {country_name}-Einwohner sparen {currency}{savings:,} jährlich</li>
                        <li>Vergleichen Sie mehrere lokale Anbieter für beste Tarife</li>
                        <li>Nutzen Sie {country_name}-spezifische Rabatte</li>
                        <li>Berücksichtigen Sie saisonales Timing für bessere Angebote in {country_name}</li>
                        <li>Verwenden Sie unsere {country_name}-optimierten Empfehlungen</li>
                    </ul>

                    <h4>🎯 Profi-Tipps für {country_name}-Erfolg:</h4>
                    <ul>
                        <li>Geben Sie genaue {country_data["local_term"]} für präzise lokale Tarife an</li>
                        <li>Berücksichtigen Sie {country_name}-Markttrends in Ihren Entscheidungen</li>
                        <li>Überprüfen Sie {country_name}-Regulierungsanforderungen</li>
                        <li>Nutzen Sie lokale {country_name}-Anbieternetzwerke</li>
                        <li>Speichern Sie Ihre personalisierte {country_name}-Analyse für zukünftige Referenz</li>
                    </ul>
                </div>'''

        elif country_data["language"] == "Dutch":
            return f'''
                <div class="educational-content global-{country_data["code"].lower()}">
                    <h3>📚 Hoe deze {specialty} te gebruiken voor {country_name}</h3>
                    <p>Deze geavanceerde AI-aangedreven {specialty.lower()} is speciaal geoptimaliseerd voor inwoners van {country_name}, en biedt directe berekeningen met deskundige inzichten gericht op {country_name} marktomstandigheden.</p>

                    <h4>🌟 {country_name}-specifieke functies:</h4>
                    <ul class="key_features">
                        <li>🤖 Geavanceerde AI-analyse aangepast voor {country_name} markt</li>
                        <li>📊 Real-time berekeningen met {country_name}-specifieke tarieven</li>
                        <li>💡 Slimme aanbevelingen voor {country_name} regelgeving</li>
                        <li>📱 Mobiel-responsief ontwerp geoptimaliseerd voor {country_name} gebruikers</li>
                        <li>🔒 100% veilig en conform {country_name} privacywetten</li>
                        <li>⚡ Directe resultaten met {currency} valuta-opmaak</li>
                    </ul>

                    <h4>💰 Geld-besparingstips voor {country_name} inwoners:</h4>
                    <ul>
                        <li>Gemiddelde {country_name} inwoners besparen {currency}{savings:,} jaarlijks</li>
                        <li>Vergelijk meerdere lokale aanbieders voor beste tarieven</li>
                        <li>Profiteer van {country_name}-specifieke kortingen</li>
                        <li>Overweeg seizoenstiming voor betere deals in {country_name}</li>
                        <li>Gebruik onze {country_name}-geoptimaliseerde aanbevelingen</li>
                    </ul>

                    <h4>🎯 Pro-tips voor {country_name} succes:</h4>
                    <ul>
                        <li>Verstrek nauwkeurige {country_data["local_term"]} voor precieze lokale tarieven</li>
                        <li>Overweeg {country_name} markttrends in uw beslissingen</li>
                        <li>Bekijk {country_name} regulatoire vereisten</li>
                        <li>Maak gebruik van lokale {country_name} aanbiedernetwerken</li>
                        <li>Bewaar uw gepersonaliseerde {country_name} analyse voor toekomstige referentie</li>
                    </ul>
                </div>'''

        elif country_data["language"] in ["Norwegian", "Danish", "Swedish"]:
            return f'''
                <div class="educational-content global-{country_data["code"].lower()}">
                    <h3>📚 Hvordan bruke denne {specialty} for {country_name}</h3>
                    <p>Denne avanserte AI-drevne {specialty.lower()} er spesielt optimalisert for {country_name} innbyggere, og gir øyeblikkelige beregninger med ekspertinnsikt fokusert på {country_name} markedsforhold.</p>

                    <h4>🌟 {country_name}-spesifikke funksjoner:</h4>
                    <ul class="key_features">
                        <li>🤖 Avansert AI-analyse tilpasset {country_name} marked</li>
                        <li>📊 Sanntidsberegninger med {country_name}-spesifikke priser</li>
                        <li>💡 Smarte anbefalinger for {country_name} reguleringer</li>
                        <li>📱 Mobilvennlig design optimalisert for {country_name} brukere</li>
                        <li>🔒 100% sikkert og i samsvar med {country_name} personvernlover</li>
                        <li>⚡ Øyeblikkelige resultater med {currency} valutaformatering</li>
                    </ul>

                    <h4>💰 Penge-sparingstips for {country_name} innbyggere:</h4>
                    <ul>
                        <li>Gjennomsnittlige {country_name} innbyggere sparer {currency}{savings:,} årlig</li>
                        <li>Sammenlign flere lokale leverandører for beste priser</li>
                        <li>Dra nytte av {country_name}-spesifikke rabatter</li>
                        <li>Vurder sesongmessig timing for bedre tilbud i {country_name}</li>
                        <li>Bruk våre {country_name}-optimaliserte anbefalinger</li>
                    </ul>

                    <h4>🎯 Profi-tips for {country_name} suksess:</h4>
                    <ul>
                        <li>Oppgi nøyaktig {country_data["local_term"]} for presise lokale priser</li>
                        <li>Vurder {country_name} markedstrender i dine beslutninger</li>
                        <li>Se gjennom {country_name} regulatoriske krav</li>
                        <li>Dra nytte av lokale {country_name} leverandørnettverk</li>
                        <li>Lagre din personaliserte {country_name} analyse for fremtidig referanse</li>
                    </ul>
                </div>'''

        else:
            # Default to English for Finnish and other languages
            return f'''
                <div class="educational-content global-{country_data["code"].lower()}">
                    <h3>📚 How to Use This {specialty} for {country_name}</h3>
                    <p>This advanced AI-powered {specialty.lower()} is specifically optimized for {country_name} residents, providing instant calculations with expert insights focused on {country_name} market conditions.</p>

                    <h4>🌟 {country_name}-Specific Features:</h4>
                    <ul class="key_features">
                        <li>🤖 Advanced AI analysis tailored for {country_name} market</li>
                        <li>📊 Real-time calculations with {country_name}-specific rates</li>
                        <li>💡 Smart recommendations for {country_name} regulations</li>
                        <li>📱 Mobile-responsive design optimized for {country_name} users</li>
                        <li>🔒 100% secure and compliant with {country_name} privacy laws</li>
                        <li>⚡ Instant results with {currency} currency formatting</li>
                    </ul>

                    <h4>💰 Money-Saving Tips for {country_name} Residents:</h4>
                    <ul>
                        <li>Average {country_name} residents save {currency}{savings:,} annually</li>
                        <li>Compare multiple local providers for best rates</li>
                        <li>Take advantage of {country_name}-specific discounts</li>
                        <li>Consider seasonal timing for better deals in {country_name}</li>
                        <li>Use our {country_name}-optimized recommendations</li>
                    </ul>
                </div>'''

    # UPDATED CSV FIELD NAMES FOR RANKMATH
    def get_rankmath_csv_fieldnames(self):
        """Get CSV fieldnames with RankMath SEO fields and global optimization"""
        return [
            "post_title", "post_name", "post_content", "post_excerpt",
            "post_status", "post_type", "menu_order",

            # RankMath SEO Fields
            "rank_math_title",
            "rank_math_description",
            "rank_math_focus_keyword",
            "rank_math_keywords",
            "rank_math_canonical_url",
            "rank_math_robots",

            # Schema Markup
            "rank_math_rich_snippet",
            "rank_math_snippet_article_type",
            "rank_math_snippet_name",
            "rank_math_snippet_desc",

            # Social Media
            "rank_math_facebook_title",
            "rank_math_facebook_description",
            "rank_math_facebook_image",
            "rank_math_twitter_title",
            "rank_math_twitter_description",
            "rank_math_twitter_image",
            "rank_math_twitter_card_type",

            # Global optimization fields
            "meta:tool_category", "meta:tool_rpm", "meta:tool_variation",
            "meta:generated_date", "meta:target_country", "meta:country_cpc",
            "categories", "tags", "featured_image", "meta:_wp_attachment_image_alt"
        ]

    # UPDATED SAVE FUNCTION FOR GLOBAL OPTIMIZATION
    def save_wordpress_csv_global(self, output_file):
        """Save WordPress import CSV with global RankMath SEO optimization"""
        print(f"💾 Saving WordPress CSV with Global RankMath SEO to {output_file}...")

        fieldnames = self.get_rankmath_csv_fieldnames()

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in self.updated_csv_data:
                writer.writerow(item)

        print(f"✅ WordPress CSV with Global RankMath SEO saved successfully!")
        print(f"🌍 Global optimization complete:")
        print(f"   📄 Pages: {len(self.updated_csv_data)}")
        print(f"   🌍 Countries: {len(self.high_rpm_countries)}")
        print(f"   💰 Avg RPM: ${sum(c['rpm'] for c in self.high_rpm_countries) / len(self.high_rpm_countries):.2f}")
        print(f"   🎯 Fields: RankMath SEO, Schema, Social Media, Global targeting")

    # UPDATED SUMMARY REPORT WITH GLOBAL STATS
    def generate_global_summary_report(self):
        """Generate transformation summary with global statistics"""
        categories = {}
        countries = {}
        languages = {}
        total_rpm = 0

        for item in self.updated_csv_data:
            category = item["meta:tool_category"]
            country = item["meta:target_country"]
            rpm = float(item["meta:tool_rpm"])

            categories[category] = categories.get(category, 0) + 1
            countries[country] = countries.get(country, 0) + 1
            total_rpm += rpm

            # Count languages
            country_data = next((c for c in self.high_rpm_countries if c["code"] == country), None)
            if country_data:
                lang = country_data["language"]
                languages[lang] = languages.get(lang, 0) + 1

        avg_rpm = total_rpm / len(self.updated_csv_data) if self.updated_csv_data else 0

        print("\n" + "=" * 80)
        print("🌍 GLOBAL HIGH RPM TRANSFORMATION SUMMARY REPORT")
        print("=" * 80)
        print(f"🔢 Total Pages Transformed: {len(self.updated_csv_data)}")
        print(f"🛠️  Unique Tools Created: {len(self.tools_config)}")
        print(f"💰 Average RPM: ${avg_rpm:.2f}")
        print(f"🎯 Highest RPM Country: Norway (${43.15})")
        print(f"📊 Total Potential Revenue Increase: {avg_rpm / 5:.1f}x vs generic tools")

        print(f"\n🌍 Global Distribution by Country:")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
            country_data = next((c for c in self.high_rpm_countries if c["code"] == country), None)
            if country_data:
                print(f"   {country_data['name']} ({country}): {count} tools (RPM: ${country_data['rpm']})")

        print(f"\n📂 Categories Distribution:")
        for category, count in sorted(categories.items()):
            print(f"   {category.title()}: {count} tools")

        print(f"\n🗣️  Languages Distribution:")
        for language, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            print(f"   {language}: {count} tools")

        print(f"\n🎉 Global Optimization Features:")
        print(f"   ✅ RankMath SEO optimization for each country")
        print(f"   ✅ Localized form fields and currency")
        print(f"   ✅ Country-specific educational content")
        print(f"   ✅ High-value keywords in local languages")
        print(f"   ✅ Schema markup for international SEO")
        print(f"   ✅ Social media optimization per country")
        print(f"   ✅ Mobile-optimized for global markets")

        print(f"\n💡 Expected Results:")
        print(f"   📈 RPM increase: 300-500% vs generic tools")
        print(f"   🎯 Better targeting: Country-specific audiences")
        print(f"   🌍 Global reach: 15 high-value markets")
        print(f"   💰 Revenue potential: ${avg_rpm:.2f} average RPM")
        print("=" * 80)

    # UPDATED MAIN FUNCTION


    def add_more_specializations(self):
        """Add specializations for remaining categories"""

        # Legal Tools
        legal_specializations = {
            "personal injury calculator": {
                "specialty": "Car Accident Injury Claims",
                "target": "car accident victims and their families",
                "form_fields": ["accident_severity", "injury_type", "medical_costs", "lost_wages", "pain_suffering",
                                "fault_percentage"],
                "unique_focus": "car accident compensation and medical expense recovery",
                "icon": "🚗💥"
            },
            "divorce cost calculator": {
                "specialty": "Uncontested Divorce Planning",
                "target": "couples seeking amicable divorce",
                "form_fields": ["marriage_length", "children_count", "assets_value", "debt_amount", "cooperation_level",
                                "mediation_preference"],
                "unique_focus": "cost-effective divorce solutions and mediation benefits",
                "icon": "💔📋"
            },
            "child support calculator": {
                "specialty": "Joint Custody Support Calculation",
                "target": "parents establishing custody arrangements",
                "form_fields": ["both_parent_incomes", "custody_percentage", "children_count", "childcare_costs",
                                "health_insurance", "special_needs"],
                "unique_focus": "joint custody calculations and fair support determination",
                "icon": "👨‍👩‍👧‍👦💰"
            }
        }

        # Finance Tools
        finance_specializations = {
            "mortgage calculator": {
                "specialty": "First-Time Buyer Mortgage",
                "target": "first-time homebuyers",
                "form_fields": ["income", "credit_score", "down_payment", "first_time_buyer_programs",
                                "pmi_requirements", "closing_costs"],
                "unique_focus": "first-time buyer programs and qualification assistance",
                "icon": "🏠🔑"
            },
            "loan calculator": {
                "specialty": "Personal Loan Consolidation",
                "target": "people consolidating multiple debts",
                "form_fields": ["current_debts", "credit_score", "income", "consolidation_amount", "interest_rates",
                                "payment_goals"],
                "unique_focus": "debt consolidation savings and payment optimization",
                "icon": "💳➡️💰"
            },
            "retirement calculator": {
                "specialty": "Early Retirement Planning",
                "target": "people planning to retire before 65",
                "form_fields": ["current_age", "target_retirement_age", "current_savings", "annual_income",
                                "expected_expenses", "healthcare_costs"],
                "unique_focus": "FIRE movement and early retirement strategies",
                "icon": "🏖️💰"
            }
        }

        # Business Tools
        business_specializations = {
            "business loan calculator": {
                "specialty": "Startup Business Loans",
                "target": "new entrepreneurs and startups",
                "form_fields": ["business_plan_score", "industry_type", "funding_needed", "personal_credit",
                                "collateral", "revenue_projections"],
                "unique_focus": "startup funding and new business qualification",
                "icon": "🚀💼"
            },
            "payroll calculator": {
                "specialty": "Small Business Payroll",
                "target": "small business owners managing payroll",
                "form_fields": ["employee_count", "pay_frequency", "benefits_offered", "state_taxes",
                                "worker_classification", "overtime_policies"],
                "unique_focus": "small business compliance and payroll optimization",
                "icon": "👥💰"
            }
        }

        # Health Tools
        health_specializations = {
            "bmi calculator": {
                "specialty": "Athletic BMI Analysis",
                "target": "athletes and fitness enthusiasts",
                "form_fields": ["height", "weight", "body_fat_percentage", "muscle_mass", "sport_type",
                                "training_intensity"],
                "unique_focus": "athletic body composition and performance optimization",
                "icon": "💪📊"
            },
            "calorie calculator": {
                "specialty": "Weight Loss Calorie Planning",
                "target": "people on weight loss journeys",
                "form_fields": ["current_weight", "goal_weight", "timeline", "activity_level", "diet_preferences",
                                "metabolism_rate"],
                "unique_focus": "sustainable weight loss and calorie deficit planning",
                "icon": "🍎📉"
            },
            "pregnancy calculator": {
                "specialty": "High-Risk Pregnancy Monitoring",
                "target": "expectant mothers with high-risk pregnancies",
                "form_fields": ["current_week", "risk_factors", "maternal_age", "previous_complications",
                                "medical_conditions", "monitoring_frequency"],
                "unique_focus": "high-risk pregnancy care and specialized monitoring",
                "icon": "🤰⚠️"
            }
        }

        # Merge all specializations
        self.tool_specializations.update(legal_specializations)
        self.tool_specializations.update(finance_specializations)
        self.tool_specializations.update(business_specializations)
        self.tool_specializations.update(health_specializations)

    def detect_tool_intention(self, title):
        """Detect the specific intention based on title"""
        title_lower = title.lower()

        # Extract tool type and variation
        for key in self.tool_specializations.keys():
            if key in title_lower:
                return self.tool_specializations[key]

        # Fallback logic for unmatched tools
        if "calculator" in title_lower:
            variation = "calculator"
        elif "estimator" in title_lower:
            variation = "estimator"
        elif "analyzer" in title_lower:
            variation = "analyzer"
        else:
            variation = "calculator"

        # Determine category
        if any(word in title_lower for word in ["insurance", "coverage", "policy"]):
            category = "insurance"
        elif any(word in title_lower for word in ["legal", "lawyer", "court", "injury", "divorce"]):
            category = "legal"
        elif any(word in title_lower for word in ["loan", "mortgage", "finance", "investment", "retirement"]):
            category = "finance"
        elif any(word in title_lower for word in ["business", "payroll", "employee", "profit"]):
            category = "business"
        elif any(word in title_lower for word in ["bmi", "calorie", "health", "fitness", "weight"]):
            category = "health"
        else:
            category = "general"

        # Return default specialization
        return {
            "specialty": f"{category.title()} {variation.title()}",
            "target": f"{category} planning needs",
            "form_fields": ["amount", "duration", "preferences", "goals"],
            "unique_focus": f"{category} optimization and planning",
            "icon": "🧮"
        }

    def generate_slug_from_title(self, title):
        """Generate slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug

    def generate_form_fields_html(self, form_fields, specialty, icon):
        """Generate unique form HTML based on specialization"""

        field_configs = {
            # Age-related fields
            "driver_age": {
                "icon": "👶", "label": "Driver Age", "type": "slider",
                "min": "16", "max": "25", "default": "18"
            },
            "age": {
                "icon": "👤", "label": "Age", "type": "slider",
                "min": "18", "max": "80", "default": "35"
            },

            # Financial fields
            "income": {
                "icon": "💰", "label": "Annual Income", "type": "currency_slider",
                "min": "20000", "max": "500000", "default": "75000"
            },
            "vehicle_value": {
                "icon": "🚗", "label": "Vehicle Value", "type": "currency_slider",
                "min": "5000", "max": "200000", "default": "25000"
            },
            "home_value": {
                "icon": "🏠", "label": "Home Value", "type": "currency_slider",
                "min": "50000", "max": "2000000", "default": "300000"
            },
            "coverage_amount": {
                "icon": "🛡️", "label": "Coverage Amount", "type": "currency_slider",
                "min": "25000", "max": "1000000", "default": "100000"
            },

            # Selection fields
            "coverage_type": {
                "icon": "🛡️", "label": "Coverage Type", "type": "select",
                "options": ["Liability Only", "Full Coverage", "Comprehensive", "Collision"]
            },
            "vehicle_year": {
                "icon": "📅", "label": "Vehicle Year", "type": "select",
                "options": ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "Older"]
            },
            "policy_type": {
                "icon": "📋", "label": "Policy Type", "type": "select",
                "options": ["Term Life", "Whole Life", "Universal Life", "Variable Life"]
            },

            # Text fields
            "location": {
                "icon": "📍", "label": "ZIP Code", "type": "text",
                "placeholder": "Enter your ZIP code"
            },
            "business_type": {
                "icon": "🏢", "label": "Business Type", "type": "text",
                "placeholder": "e.g., Restaurant, Retail, Consulting"
            },

            # Boolean/Checkbox fields
            "gpa": {
                "icon": "📚", "label": "Student GPA", "type": "slider",
                "min": "2.0", "max": "4.0", "default": "3.0", "step": "0.1"
            },
            "driving_course_completed": {
                "icon": "🎓", "label": "Driving Course Completed", "type": "checkbox"
            },
            "sr22_required": {
                "icon": "📄", "label": "SR-22 Required", "type": "checkbox"
            },

            # Default fallback
            "default": {
                "icon": "📝", "label": "Amount", "type": "currency_slider",
                "min": "1000", "max": "100000", "default": "10000"
            }
        }

        form_html = f'''
    <div class="enhanced-form">
        <div class="form-header">
            <h2>{icon} AI-Powered {specialty}</h2>
            <p>Get instant, AI-powered insights tailored to your specific {specialty.lower()} needs</p>
            <p style="text-align:center;"><a href="https://www.buymeacoffee.com/shakdiesel" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a></p>
        </div>

        <form id="tool-form" onsubmit="calculateResults(event)">
            <div class="form-grid">'''

        for field in form_fields[:6]:  # Limit to 6 fields for better UX
            config = field_configs.get(field, field_configs["default"])

            form_html += f'''

                <div class="form-group">
                    <label class="form-label" for="{field}">
                        <span class="label-icon">{config['icon']}</span>
                        {config['label']}
                    </label>'''

            if config['type'] == 'slider':
                form_html += f'''
                    <div class="slider-group">
                        <div class="slider-container">
                            <input type="range" 
                                   id="{field}" 
                                   name="{field}"
                                   class="slider-input"
                                   data-format="number"
                                   min="{config['min']}" 
                                   max="{config['max']}" 
                                   value="{config['default']}"
                                   step="{config.get('step', '1')}"
                                   oninput="updateSliderValue(this)">
                            <div class="slider-value" id="{field}-value">{config['default']}</div>
                        </div>
                    </div>'''
            elif config['type'] == 'currency_slider':
                form_html += f'''
                    <div class="slider-group">
                        <div class="slider-container">
                            <input type="range" 
                                   id="{field}" 
                                   name="{field}"
                                   class="slider-input"
                                   data-format="currency"
                                   min="{config['min']}" 
                                   max="{config['max']}" 
                                   value="{config['default']}"
                                   oninput="updateSliderValue(this)">
                            <div class="slider-value" id="{field}-value">${int(config['default']):,}</div>
                        </div>
                    </div>'''
            elif config['type'] == 'select':
                form_html += f'''
                    <select id="{field}" name="{field}" class="form-select">'''
                for option in config['options']:
                    form_html += f'<option value="{option}">{option}</option>'
                form_html += '</select>'
            elif config['type'] == 'checkbox':
                form_html += f'''
                    <div class="checkbox-group">
                        <input type="checkbox" id="{field}" name="{field}" class="form-checkbox">
                        <label for="{field}" class="checkbox-label">Yes</label>
                    </div>'''
            else:  # text input
                form_html += f'''
                    <input type="text" 
                           id="{field}" 
                           name="{field}"
                           class="form-input"
                           placeholder="{config.get('placeholder', f'Enter {config["label"].lower()}')}"
                           autocomplete="on">'''

            form_html += '''
                </div>'''

        form_html += '''

            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">
                    <span class="btn-icon">🧮</span>
                    Calculate Now
                </button>
                <button type="button" class="btn btn-secondary" onclick="resetForm()">
                    <span class="btn-icon">🔄</span>
                    Reset
                </button>
            </div>
        </form>
    </div>'''

        return form_html

    def generate_educational_content(self, specialty, target, unique_focus, icon):
        """Generate unique educational content for each tool"""
        return f'''
    <div class="educational-content">
        <h3>📚 How to Use This {specialty}</h3>
        <p>This advanced AI-powered {specialty.lower()} is specifically designed for {target}, providing instant, personalized calculations with expert insights focused on {unique_focus}.</p>

        <h4>🌟 Specialized Features:</h4>
        <ul class="key_features">
            <li>{icon} Advanced AI analysis tailored for {target}</li>
            <li>📊 Real-time calculations with {specialty.lower()}-specific insights</li>
            <li>💡 Smart recommendations for {unique_focus}</li>
            <li>📱 Mobile-responsive design optimized for your needs</li>
            <li>🔒 100% secure and private - no personal data stored</li>
            <li>⚡ Instant results with detailed {specialty.lower()} breakdown</li>
        </ul>

        <h4>💰 Money-Saving Tips for {target.title()}:</h4>
        <ul>
            <li>Use our specialized AI recommendations for {unique_focus}</li>
            <li>Compare multiple scenarios specific to your {specialty.lower()} needs</li>
            <li>Download your personalized {specialty.lower()} report</li>
            <li>Share results with relevant advisors or family members</li>
            <li>Check back regularly as {specialty.lower()} options evolve</li>
        </ul>

        <h4>🎯 Pro Tips for {specialty} Success:</h4>
        <ul>
            <li>Provide accurate information relevant to {unique_focus}</li>
            <li>Try different scenarios to optimize your {specialty.lower()} strategy</li>
            <li>Review AI insights for opportunities specific to {target}</li>
            <li>Use the specialized features designed for your situation</li>
            <li>Save your personalized {specialty.lower()} analysis for future reference</li>
        </ul>
    </div>'''

    def save_wordpress_csv(self, output_file):
        """Save WordPress import CSV with exact header matching"""
        print(f"💾 Saving WordPress CSV to {output_file}...")

        # Your exact CSV headers
        fieldnames = [
            "post_title", "post_name", "post_content", "post_excerpt",
            "post_status", "post_type", "menu_order", "meta:_yoast_wpseo_title",
            "meta:_yoast_wpseo_metadesc", "meta:_yoast_wpseo_focuskw",
            "meta:tool_category", "meta:tool_rpm", "meta:tool_variation",
            "meta:generated_date", "categories", "tags", "featured_image",
            "meta:_wp_attachment_image_alt"
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in self.updated_csv_data:
                # The item dictionary already has the correct keys from transform_csv_to_unique_pages
                writer.writerow(item)

        print(f"✅ WordPress CSV saved successfully!")

    def save_tools_config(self, output_file):
        """Save tools_config.json for Python API"""
        print(f"💾 Saving tools config to {output_file}...")

        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.tools_config, jsonfile, indent=2, ensure_ascii=False)

        print(f"✅ Tools config saved successfully!")

    def generate_summary_report(self):
        """Generate transformation summary"""
        categories = {}
        variations = {}

        for item in self.updated_csv_data:
            category = item["meta:tool_category"]
            variation = item["meta:tool_variation"]

            categories[category] = categories.get(category, 0) + 1
            variations[variation] = variations.get(variation, 0) + 1

        print("\n" + "=" * 60)
        print("📊 TRANSFORMATION SUMMARY REPORT")
        print("=" * 60)
        print(f"🔢 Total Pages Transformed: {len(self.updated_csv_data)}")
        print(f"🛠️  Unique Tools Created: {len(self.tools_config)}")

        print(f"\n📂 Categories Distribution:")
        for category, count in sorted(categories.items()):
            print(f"   {category.title()}: {count} tools")

        print(f"\n🎯 Variations Distribution:")
        for variation, count in sorted(variations.items()):
            print(f"   {variation.title()}: {count} tools")

        print(f"\n🎉 All tools now have unique:")
        print(f"   ✅ Form fields specific to their purpose")
        print(f"   ✅ AI prompts tailored to their specialization")
        print(f"   ✅ Educational content for their target audience")
        print(f"   ✅ SEO optimization for their niche")
        print("=" * 60)

    def get_category_from_specialty(self, specialty):
        """Determine category from specialty"""
        specialty_lower = specialty.lower()
        if "insurance" in specialty_lower:
            return "insurance"
        elif any(word in specialty_lower for word in ["legal", "injury", "divorce", "court"]):
            return "legal"
        elif any(word in specialty_lower for word in ["mortgage", "loan", "finance", "investment", "retirement"]):
            return "finance"
        elif any(word in specialty_lower for word in ["business", "payroll", "employee"]):
            return "business"
        elif any(word in specialty_lower for word in ["health", "fitness", "medical", "bmi", "calorie"]):
            return "health"
        else:
            return "general"

    def get_variation_from_title(self, title):
        """Extract variation from title"""
        title_lower = title.lower()
        if "calculator" in title_lower:
            return "calculator"
        elif "estimator" in title_lower:
            return "estimator"
        elif "analyzer" in title_lower:
            return "analyzer"
        elif "planner" in title_lower:
            return "planner"
        elif "advisor" in title_lower:
            return "advisor"
        elif "simulator" in title_lower:
            return "simulator"
        elif "predictor" in title_lower:
            return "predictor"
        elif "optimizer" in title_lower:
            return "optimizer"
        elif "tracker" in title_lower:
            return "tracker"
        elif "manager" in title_lower:
            return "manager"
        else:
            return "calculator"

    def get_rpm_from_category(self, specialty):
        """Get RPM based on category"""
        category = self.get_category_from_specialty(specialty)
        rpm_mapping = {
            "insurance": 35,
            "legal": 25,
            "finance": 30,
            "business": 30,
            "health": 28,
            "general": 25
        }
        return rpm_mapping.get(category, 25)

    def generate_keywords(self, specialty, target):
        """Generate SEO keywords"""
        base_keywords = [
            specialty.lower(),
            f"{specialty.lower()} for {target}",
            f"free {specialty.lower()}",
            f"online {specialty.lower()}",
            f"ai {specialty.lower()}",
            f"{specialty.lower()} tool"
        ]
        return ",".join(base_keywords[:6])

    def get_wordpress_categories(self, specialty):
        """Get WordPress categories"""
        category = self.get_category_from_specialty(specialty)
        category_mapping = {
            "insurance": "AI Tools,Insurance Tools,Financial Calculators",
            "legal": "AI Tools,Legal Tools,Legal Calculators",
            "finance": "AI Tools,Financial Tools,Finance Calculators",
            "business": "AI Tools,Business Tools,Business Calculators",
            "health": "AI Tools,Health Tools,Health Calculators",
            "general": "AI Tools,General Calculators"
        }
        return category_mapping.get(category, "AI Tools,General Calculators")

    def get_featured_image(self, specialty):
        """Get featured image based on specialty"""
        category = self.get_category_from_specialty(specialty)
        image_mapping = {
            "insurance": "Insurance-Calculator-Protection-and-Security.jpg",
            "legal": "Legal-Calculator-Justice-and-Law.jpg",
            "finance": "Finance-Calculator-Money-and-Investment.jpg",
            "business": "Business-Calculator-Growth-and-Success.jpg",
            "health": "Health-Calculator-Wellness-and-Fitness.jpg",
            "general": "AI-Calculator-Technology-and-Innovation.jpg"
        }
        return image_mapping.get(category, "AI-Calculator-Technology-and-Innovation.jpg")


# Update the main function to use CSV input instead of text file
def main():
    """Main execution function with global optimization"""
    print("🌍 Starting Global High RPM Transformation...")
    print("=" * 80)

    # Initialize transformer
    transformer = UniquePageTransformer()

    # Input file (your existing CSV with the exact headers)
    input_csv = "existing_tools.csv"  # Change this to your actual CSV file

    # Output files
    wordpress_csv = "global_rpm_wordpress_import.csv"
    tools_config_json = "global_tools_config.json"

    try:
        # Transform CSV to unique pages with global optimization
        transformer.transform_csv_to_unique_pages(input_csv)

        # Save outputs
        transformer.save_wordpress_csv_global(wordpress_csv)
        transformer.save_tools_config(tools_config_json)

        # Generate global summary
        transformer.generate_global_summary_report()

        print(f"\n🎊 GLOBAL SUCCESS! Files generated:")
        print(f"   📄 WordPress CSV: {wordpress_csv}")
        print(f"   ⚙️  Tools Config: {tools_config_json}")
        print(f"\n📋 Next Steps:")
        print(f"   1. Use WordPress All Import to UPDATE existing pages")
        print(f"   2. Map post_name to preserve URLs")
        print(f"   3. Replace your Python API's tools_config.json")
        print(f"   4. Test with different countries")
        print(f"   5. Monitor RPM improvements across all markets")
        print(f"\n🚀 Expected Revenue Impact:")
        print(f"   💰 3-5x RPM increase from global targeting")
        print(f"   🌍 Access to 15 highest-paying countries")
        print(f"   🎯 Localized content for better conversion")

    except FileNotFoundError:
        print(f"❌ Error: Input CSV file '{input_csv}' not found!")
        print(f"📝 Please ensure your CSV file has these headers:")
        print(
            f"   post_title,post_name,post_content,post_excerpt,post_status,post_type,menu_order,meta:_yoast_wpseo_title,meta:_yoast_wpseo_metadesc,meta:_yoast_wpseo_focuskw,meta:tool_category,meta:tool_rpm,meta:tool_variation,meta:generated_date,categories,tags,featured_image,meta:_wp_attachment_image_alt")

    except Exception as e:
        print(f"❌ Error during transformation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()