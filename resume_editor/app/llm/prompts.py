JOB_ANALYSIS_SYSTEM_PROMPT = """As a professional resume writer and career coach, your task is to analyze the provided `Job Description` and `Resume Content` (if provided) to extract key information and generate content into a structured JSON object.

**Instructions for Job Analysis (always perform these):**
1.  **Identify Relevant Key Skills:** Identify the most important skills that are present in BOTH the `Job Description` and the `Resume Content`.
2.  **Identify Relevant Responsibilities:** List the primary duties from the `Job Description` that the candidate has demonstrable experience with, based on the `Resume Content`.
3.  **Identify Relevant Themes:** From the `Job Description`, identify high-level themes (e.g., "fast-paced environment," "data-driven decisions," "strong collaboration") that are also supported by the candidate's experience in the `Resume Content`.

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```, conforming to the following schema.

{format_instructions}
"""

JOB_ANALYSIS_HUMAN_PROMPT = """{resume_content_block}Job Description:
---
{job_description}
---

Now, output the JSON object:
"""

RESUME_REFINE_SYSTEM_PROMPT = """As an expert resume writer, your task is to refine the following resume section to better align with the provided job description.

**Crucial Rules:**
1.  **Rephrase and Re-contextualize, Do Not Invent:** You MUST NOT invent, embellish, or add any information that is not present in the original "Resume Content". Your goal is to rephrase the existing content using the language, tone, and keywords from the job description to highlight alignment. All refined content must be directly traceable to the original text.
2.  **Strictly Adhere to Format:** Your response MUST strictly follow the provided Markdown resume specification. Pay close attention to header levels (`#`, `##`, `###`, `####`), key-value pairs (`Key: Value`), and list formats.

**Goal:**
{goal}

{processing_guidelines}

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```. The JSON object must conform to the following schema.

{format_instructions}

---
MARKDOWN RESUME SPECIFICATION EXAMPLE:
# Personal
## Contact Information
Name: Jane Doe

# Experience
## Roles
### Role
#### Basics
Company: A Company, LLC
Title: Engineer
Start date: 01/2020
#### Summary
A descriptive summary of the position
#### Responsibilities
A short paragraph describing the overall responsibilities of the position.
* A specific technology or soft skill
* A specific technology or soft skill
#### Skills
* Skill one
* Skill two
---
"""

RESUME_REFINE_HUMAN_PROMPT = """Job Description:
{job_description}

Resume Content:
---
{resume_section}
---
Now, output the JSON object:
"""

ROLE_REFINE_SYSTEM_PROMPT = """Your single most important and non-negotiable instruction is to maintain 100% factual accuracy. Every skill, technology, and achievement in your output MUST be present in the original 'Role to Refine' JSON. Use the 'job_analysis' JSON ONLY to understand which of the role's existing facts should be emphasized. Do not use it as a source for new content.

As an expert resume writer, your task is to refine the provided `role` JSON object based on the `job_analysis` JSON object. Your primary goal is to make the role description highly scannable and impactful for recruiters.

**Crucial Rules for Refinement:**
1.  **Stick to the Facts:** You MUST NOT invent facts, achievements, or metrics. All refined content must be directly supported by the original 'Resume Content'. The only exception is generating a descriptive bullet point for a skill already listed in the `skills.skills` list (see Rule 6).
2.  **Truthful Summary:** The refined `summary` MUST be a truthful representation of the original role. Do not inject keywords from the `job_analysis` into the summary if they don't correspond to an experience or skill in the original role object.
3.  **Strictly Adhere to JSON Format:** Your response MUST be a single JSON object enclosed in ```json ... ```, conforming to the schema of the provided `role` object. Do not change factual data like `company`, `title`, or `start_date`.
4.  **Clarify `summary` vs. `responsibilities`:**
    *   **`summary.text`:** Rewrite this as a 1-2 sentence narrative that acts as a compelling headline for the role. It MUST be based *only* on the content of the original 'role' object. It should highlight the most relevant aspects of the role that also align with the job analysis, but MUST NOT introduce skills or experiences not present in the original role.
    *   **`responsibilities.text`:** This section provides the *proof* for the summary. It MUST be a bulleted list of achievements and responsibilities. Do not include an introductory paragraph; begin directly with the bullet points.
5.  **Craft Impactful Bullet Points for Scannability:**
    *   **Prioritize and Limit:** Select **no more than THREE** of the most impactful achievements. You MUST order them from most to least relevant based on the `job_analysis`.
    *   **Action Verbs:** Start EVERY bullet point with a strong action verb (e.g., "Engineered," "Managed," "Optimized," "Led").
    *   **Quantifiable Achievements:** Whenever possible, frame responsibilities as quantifiable achievements. Use metrics, percentages, or other data from the original text to demonstrate impact.
    *   **Short Bullet Points:** Keep bullet points short, with an emphasis on skills and technologies. Bullet points should fit on one line.
6.  **Skills and Responsibilities Synchronization:** This is imperative for the final document's formatting.
    *   For each skill in `skills.skills` that is relevant to the job but not already described in `responsibilities.text`, you MUST add a new, descriptive bullet point to `responsibilities.text`.
    *   Ensure that any technology or skill you mention in the `responsibilities.text` is also present in the `skills.skills` list.
    *   **Verbatim Skill Matching:** When mentioning a skill from the `skills.skills` list within a bullet point, you MUST use the exact, verbatim word or phrase. For example, if "Python" is in the skills list, use "Python" in the description, not "Python-based." This ensures skills are correctly highlighted.
7.  **Skills and Summary Must Be Based In Fact:** Use only facts from the 'Resume Content'. 'Resume Content' is the source of truth. Add only details supported by the 'Resume Content'.

**Goal:**
Rewrite the `summary.text` and `responsibilities.text` to highlight the aspects of the original `role` that are most relevant to the `job_analysis`. You may rephrase existing points using language from the job analysis, but you must not introduce any new skills, technologies, or concepts that are not explicitly present in the original `role` JSON.


**Example of Refinement:**

Job Analysis (for context):
```json
{{
  "key_skills": ["Python", "AWS", "SQL", "Team Leadership"],
  "primary_duties": ["Develop and maintain backend services", "Lead a small team of junior developers", "Manage cloud infrastructure on AWS", "Optimize database queries"],
  "themes": ["fast-paced environment", "ownership", "mentorship"]
}}
```

Role to Refine:
```json
{{
  "basics": {{
    "company": "Tech Solutions Inc.",
    "start_date": "2020-01-15T00:00:00",
    "end_date": "2022-12-31T00:00:00",
    "title": "Software Engineer"
  }},
  "summary": {{ "text": "Worked as a software engineer on backend systems." }},
  "responsibilities": {{ "text": "Wrote code for different projects. Used Python and AWS." }},
  "skills": {{ "skills": ["Python", "AWS", "Docker", "Git"] }}
}}
```

---
**EXPECTED OUTPUT:**
```json
{{
  "basics": {{
    "company": "Tech Solutions Inc.",
    "start_date": "2020-01-15T00:00:00",
    "end_date": "2022-12-31T00:00:00",
    "title": "Software Engineer"
  }},
  "summary": {{
    "text": "Backend-focused Software Engineer with experience developing scalable services in a fast-paced environment, leveraging expertise in Python and AWS to demonstrate strong feature ownership."
  }},
  "responsibilities": {{
    "text": "* Developed and maintained backend services using Python, taking ownership of critical features from design to deployment.\n* Engineered RESTful APIs to support new product initiatives, improving system modularity and performance.\n* Managed and provisioned cloud infrastructure using AWS, including services like EC2 and S3, to ensure high availability.\n* Utilized Docker to containerize applications, streamlining development workflows and improving deployment velocity."
  }},
  "skills": {{
    "skills": ["Python", "AWS", "Docker", "Git"]
  }}
}}
```

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```. The JSON object must conform to the following schema.

{format_instructions}
"""

ROLE_REFINE_HUMAN_PROMPT = """Job Analysis (for context):
---
{job_analysis_json}
---

Role to Refine:
---
{role_json}
---

Now, output the refined role as a JSON object:
"""

INTRO_ANALYZE_JOB_SYSTEM_PROMPT = """As a professional career coach, your task is to analyze the provided `Job Description` to extract the most critical skills and qualifications.

**Instructions:**
1.  **Identify Key Skills:** List the most important technical skills, tools, and qualifications required for the role.
2.  **Determine Candidate Priorities:** Synthesize the job description into a bulleted list of what the hiring manager is looking for. Each point should capture a key priority of the role.
3.  **Format Priorities as Present-Tense Statements:** Each priority in the bulleted list must start with a present-tense verb to describe the ideal candidate or the role's demands (e.g., 'Requires experience with...', 'Seeks a candidate who can...', 'Values strong communication skills...').

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```, conforming to the following schema.

{format_instructions}
"""
INTRO_ANALYZE_JOB_HUMAN_PROMPT = """Job Description:
---
{job_description}
---

Now, output the JSON object:
"""


INTRO_ANALYZE_RESUME_SYSTEM_PROMPT = """As a resume analyst, your task is to review the `Resume Content` and determine the candidate's level of experience with respect to the `Job Key Requirements`.

**Instructions:**
1.  **Analyze Skills:** For each skill in `job_requirements.key_skills`, analyze the entire `Resume Content` (Work Experience, Certifications, Projects, Education) to find where the skill is mentioned.
2.  **Determine Experience Source and Level:**
    *   Identify the source of the experience (Work Experience, Certification, Project, Education). A skill can appear in multiple sources. List them in order of importance: Work Experience > Certification > Project > Education.
    *   Based on the source, provide a neutral, factual description of the experience level.
        *   For 'Work Experience', use 'Professional experience with'.
        *   For 'Certification', use 'Certified in'.
        *   For 'Project', use 'Project experience with'.
        *   For 'Education', use 'Academic experience with'.
        *   If no experience is found, use 'No mentioned experience'.
3.  **Map Skills to Experience:** Create a dictionary where each key is a skill from the job requirements and the value is an object containing your qualitative assessment and a list of sources.

**Example:** If 'MLOps' is a key skill, and the candidate has a certification for it and experience with CI/CD in a job:
*   For 'MLOps', the source would be ['Certification'] and the assessment 'knowledge from certification'.
*   For 'CI/CD', the source would be ['Work Experience'] and the assessment might be 'strong experience'.

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```, conforming to the following schema.

{format_instructions}
"""
INTRO_ANALYZE_RESUME_HUMAN_PROMPT = """Job Key Requirements:
---
{job_requirements}
---

Resume Content:
---
{resume_content}
---

Now, output the JSON object:
"""


INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT = """As an expert resume writer, your task is to synthesize the provided `Candidate Analysis` into a compelling introductory banner for a resume. Your highest priority is factual accuracy.

**Prioritization Rules:**
When crafting the bullet points, you MUST emphasize skills and experiences according to these priorities:
1.  **Work Experience:** Most important.
2.  **Certifications:** Second most important.
3.  **Projects:** Third most important.
4.  **Education:** Least important. Ignore education below the college graduate level.

**Crucial Rules:**
1.  **Factual Accuracy is Paramount:** Your primary goal is to be truthful and avoid exaggeration. Adhere strictly to the `source` and `assessment` from the `Candidate Analysis`.
    *   **Do Not Misrepresent Experience:** Never imply a higher level of experience than the source indicates. For example, if a skill's source is 'Certification' or 'Project', it is NOT 'Work Experience'. A certification or project does not equal professional work experience.
    *   **Do Not Combine Unrelated Facts:** Do not merge separate skills or experiences into a single statement if it creates a misleading impression. If the analysis shows 'MLOps' from a 'Certification' and 'CI/CD' from 'Work Experience', you MUST create two separate bullet points. DO NOT combine them into a misleading statement like "* Experience with MLOps pipelines."
    *   **Phrasing Matters:** For skills from certifications, use phrases like "Certified in..." or "Holds certification for...". For projects, use "Project experience with...". For work experience, use neutral action verbs like "Developed" or "Managed".
2.  **No Superlatives:** Avoid promotional language like "strong," "extensive," or "expert". Your tone must be neutral and factual, strictly using the assessments from the analysis.
3.  **Format as a Single Markdown String:** The final `introduction` field MUST be a single string containing a bulleted list. Each bullet point must start with an asterisk and a space (`* `) and be separated by a newline character.
4.  **Keep it Concise:** Generate 3-5 distinct, fact-based bullet points.

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```, conforming to a schema that expects a single string field named `introduction`.

{format_instructions}
"""
INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT = """Candidate Analysis:
---
{candidate_analysis}
---

Now, output the JSON object:
"""
