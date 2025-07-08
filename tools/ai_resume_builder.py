from openai import OpenAI


def generate_ai_resume(resume_data, api_key):
    """Generate AI-enhanced resume"""
    client = OpenAI(api_key=api_key)

    personal = resume_data.get('personal', {})
    experience = resume_data.get('experience', [])
    education = resume_data.get('education', [])
    skills = resume_data.get('skills', [])

    # Build comprehensive prompt
    prompt = f"""
Create a professional, ATS-optimized resume for:

PERSONAL INFORMATION:
Name: {personal.get('name', '')}
Email: {personal.get('email', '')}
Phone: {personal.get('phone', '')}
Location: {personal.get('location', '')}
LinkedIn: {personal.get('linkedin', '')}
Portfolio: {personal.get('portfolio', '')}

EXPERIENCE:
{format_experience_for_prompt(experience)}

EDUCATION:
{format_education_for_prompt(education)}

SKILLS:
{', '.join(skills) if skills else 'No skills provided'}

Requirements:
1. Create a modern, professional resume format
2. Optimize for ATS (Applicant Tracking Systems)
3. Use strong action verbs and quantifiable achievements
4. Include a compelling professional summary
5. Organize sections logically
6. Ensure consistent formatting
7. Highlight key accomplishments and impact

Format as clean, professional text that can be easily copied and pasted.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer and career coach with 15+ years of experience helping professionals land their dream jobs. Create compelling, ATS-optimized resumes that highlight achievements and demonstrate value to employers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )

        resume_content = response.choices[0].message.content

        # Enhance with additional sections
        enhanced_resume = f"""
{resume_content}

---

## 🎯 Resume Optimization Tips

### ATS Optimization:
- Use standard section headings (Experience, Education, Skills)
- Include relevant keywords from job descriptions
- Use simple, clean formatting without graphics
- Save as both .docx and .pdf formats

### Impact Enhancement:
- Quantify achievements with numbers and percentages
- Use strong action verbs (managed, developed, increased)
- Focus on results and business impact
- Tailor content to each job application

### Professional Presentation:
- Keep to 1-2 pages maximum
- Use consistent formatting and fonts
- Proofread carefully for errors
- Include relevant certifications and awards

### Next Steps:
1. Customize this resume for each job application
2. Research company-specific keywords to include
3. Practice discussing your achievements in interviews
4. Keep resume updated with latest accomplishments

**Resume Score:** {calculate_resume_score(resume_data)}/100
**Improvement Areas:** {get_improvement_suggestions(resume_data)}
"""

        return enhanced_resume

    except Exception as e:
        return f"Error generating resume: {str(e)}"


def format_experience_for_prompt(experience):
    """Format experience data for AI prompt"""
    if not experience:
        return "No experience provided"

    formatted = []
    for exp in experience:
        formatted.append(f"""
Company: {exp.get('company', '')}
Position: {exp.get('position', '')}
Duration: {exp.get('start_date', '')} - {exp.get('end_date', 'Present')}
Responsibilities: {exp.get('description', '')}
""")

    return '\n'.join(formatted)


def format_education_for_prompt(education):
    """Format education data for AI prompt"""
    if not education:
        return "No education provided"

    formatted = []
    for edu in education:
        formatted.append(f"""
Institution: {edu.get('institution', '')}
Degree: {edu.get('degree', '')}
Field: {edu.get('field', '')}
Year: {edu.get('year', '')}
GPA: {edu.get('gpa', 'Not specified')}
""")

    return '\n'.join(formatted)


def calculate_resume_score(resume_data):
    """Calculate resume completeness score"""
    score = 0

    personal = resume_data.get('personal', {})
    if personal.get('name'): score += 10
    if personal.get('email'): score += 10
    if personal.get('phone'): score += 5
    if personal.get('linkedin'): score += 5

    experience = resume_data.get('experience', [])
    if experience:
        score += 30
        # Bonus for detailed experience
        if any(exp.get('description') for exp in experience):
            score += 10

    education = resume_data.get('education', [])
    if education: score += 15

    skills = resume_data.get('skills', [])
    if skills: score += 15

    return min(score, 100)


def get_improvement_suggestions(resume_data):
    """Get suggestions for resume improvement"""
    suggestions = []

    personal = resume_data.get('personal', {})
    if not personal.get('linkedin'):
        suggestions.append("Add LinkedIn profile")

    experience = resume_data.get('experience', [])
    if not experience:
        suggestions.append("Add work experience")
    elif len(experience) < 2:
        suggestions.append("Add more experience entries")

    skills = resume_data.get('skills', [])
    if len(skills) < 5:
        suggestions.append("Add more relevant skills")

    if not suggestions:
        suggestions.append("Great! Your resume has all key sections")

    return ', '.join(suggestions)