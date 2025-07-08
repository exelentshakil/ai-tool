from openai import OpenAI


def generate_outline(topic, api_key, **options):
    """Generate AI-powered blog outline"""
    client = OpenAI(api_key=api_key)

    # Extract options with defaults
    content_type = options.get('content_type', 'how-to')
    target_audience = options.get('target_audience', 'general')
    content_length = options.get('content_length', 'medium')
    writing_tone = options.get('writing_tone', 'professional')
    include_intro = options.get('include_intro', True)
    include_conclusion = options.get('include_conclusion', True)
    include_faq = options.get('include_faq', False)
    include_cta = options.get('include_cta', False)
    include_slug = options.get('include_slug', True)
    include_focus_keywords = options.get('include_focus_keywords', True)
    include_keywords = options.get('include_keywords', True)
    include_meta = options.get('include_meta', True)

    # Build comprehensive prompt
    prompt = f"""
Create a comprehensive blog outline for: "{topic}"

Requirements:
- Content Type: {content_type}
- Target Audience: {target_audience}
- Content Length: {content_length}
- Writing Tone: {writing_tone}

Please include:
{"- SEO-optimized slug" if include_slug else ""}
{"- Focus keyword strategy" if include_focus_keywords else ""}
{"- Related keywords list" if include_keywords else ""}
{"- Meta title and description" if include_meta else ""}
{"- Engaging introduction section" if include_intro else ""}
{"- Compelling conclusion" if include_conclusion else ""}
{"- FAQ section" if include_faq else ""}
{"- Call-to-action" if include_cta else ""}

Format the outline with:
1. Clear hierarchy (H1, H2, H3 headings)
2. Brief content descriptions for each section
3. SEO optimization suggestions
4. Estimated word counts for sections
5. Content creation tips
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert content strategist and SEO specialist with 10+ years of experience creating viral blog content. Create detailed, actionable blog outlines that help writers produce engaging, search-optimized content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )

        outline = response.choices[0].message.content

        # Enhance with additional formatting
        enhanced_outline = f"""
# 📝 Blog Outline: {topic}

{outline}

---

## 🎯 Content Strategy Tips

### SEO Optimization:
- Target long-tail keywords related to "{topic}"
- Include semantic keywords naturally throughout
- Optimize images with alt text and descriptive filenames
- Use internal linking to related content

### Engagement Boosters:
- Start with a compelling hook in the introduction
- Include relevant statistics and data points
- Add actionable tips and real examples
- Use bullet points and numbered lists for readability

### Content Enhancement:
- Include relevant images, infographics, or videos
- Add social proof (testimonials, case studies)
- Create downloadable resources (checklists, templates)
- End with a strong call-to-action

**Estimated Total Word Count:** {get_estimated_word_count(content_length)}
**Estimated Reading Time:** {get_estimated_reading_time(content_length)}
**Content Difficulty:** {get_content_difficulty(content_type)}
"""

        return enhanced_outline

    except Exception as e:
        return f"Error generating outline: {str(e)}"


def get_estimated_word_count(content_length):
    """Get estimated word count based on content length"""
    counts = {
        'short': '800-1,200 words',
        'medium': '1,500-2,500 words',
        'long': '2,500-4,000 words',
        'comprehensive': '4,000+ words'
    }
    return counts.get(content_length, '1,500-2,500 words')


def get_estimated_reading_time(content_length):
    """Get estimated reading time"""
    times = {
        'short': '3-5 minutes',
        'medium': '6-10 minutes',
        'long': '10-15 minutes',
        'comprehensive': '15+ minutes'
    }
    return times.get(content_length, '6-10 minutes')


def get_content_difficulty(content_type):
    """Get content difficulty level"""
    difficulty = {
        'how-to': 'Beginner-Intermediate',
        'listicle': 'Beginner',
        'guide': 'Intermediate-Advanced',
        'tutorial': 'Intermediate',
        'review': 'Beginner-Intermediate',
        'comparison': 'Intermediate',
        'case-study': 'Advanced',
        'opinion': 'Intermediate'
    }
    return difficulty.get(content_type, 'Intermediate')