JOB_ANALYSIS_SYSTEM_PROMPT = """As a professional resume writer and career coach, your task is to analyze the provided `Job Description` and extract key information into a structured JSON object.

**Instructions:**
1.  **Identify Key Skills:** Extract the most important technical skills, soft skills, tools, and qualifications.
2.  **Extract Responsibilities:** List the primary duties and responsibilities of the role.
3.  **Identify Themes:** Note any high-level themes, company culture points, or recurring keywords (e.g., "fast-paced environment," "data-driven decisions," "strong collaboration").

**Output Format:**
Your response MUST be a single JSON object enclosed in ```json ... ```, conforming to the following schema.

{format_instructions}
"""

JOB_ANALYSIS_HUMAN_PROMPT = """Job Description:
---
{job_description}
---

Now, output the JSON object:
"""

RESUME_REFINE_SYSTEM_PROMPT = """As an expert resume writer, your task is to refine the following resume section to better align with the provided job description.

**Crucial Rules:**
1.  **Stick to the Facts:** You MUST NOT invent, embellish, or add any information that is not present in the original "Resume Section to Refine". Do not use superlatives or grandiose claims. All refined content must be directly traceable to the original text.
2.  **Strictly Adhere to Format:** Your response MUST strictly follow the provided Markdown resume specification. Pay close attention to header levels (`#`, `##`, `###`, `####`), key-value pairs (`Key: Value`), and list formats.
3.  **Skills Section Formatting:** The `Skills` section under a `Role` or `Project` MUST be a bulleted list. Each skill must be a separate line starting with `* `.

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

Resume Section to Refine:
---
{resume_section}
---
Now, output the JSON object:
"""

ROLE_REFINE_SYSTEM_PROMPT = """As an expert resume writer, your task is to refine the provided `role` JSON object to better align with the `job_analysis` JSON object.

**Crucial Rules:**
1.  **Stick to the Facts:** You MUST NOT invent, embellish, or add new achievements. All refined content must be directly traceable to the original text, with one exception: you may generate a responsibility bullet point for a skill listed in the `skills.skills` list (see rule 4). Rephrasing and re-contextualizing are encouraged.
2.  **Strictly Adhere to Format:** Your response MUST be a single JSON object enclosed in ```json ... ```. The JSON object must conform to the schema of the provided `role` object.
3.  **Refine, Don't Replace:** Your goal is to improve the summary and responsibilities based on the job analysis. Do not change factual data like company name, title, or dates.
4.  **Skills and Responsibilities Synchronization:**
    - Critically evaluate the skills in `skills.skills` against the `job_analysis`.
    - For each skill that is **relevant** to the job but **not** already described in `responsibilities.text`, you MUST add a new, separate bullet point to `responsibilities.text`.
    - Each new bullet point must be descriptive and showcase professional use.
        - Example for 'EC2': "- Deployed and managed scalable application infrastructure using Amazon EC2 instances, ensuring high availability and performance."
        - Example for 'Splunk': "- Utilized Splunk for real-time log analysis, system monitoring, and creating performance dashboards."
    - DO NOT group unrelated skills into a single bullet point.
    - Conversely, ensure that any technology or skill you mention in the `responsibilities.text` is also present in the `skills.skills` list.
    - **Verbatim Skill Matching:** When mentioning a skill from the `skills.skills` list within the `responsibilities.text`, you MUST use the exact, verbatim word or phrase from the list. For example, if "Python" is in the skills list, use the word "Python" in your description, not "Python-based". This ensures skills are correctly highlighted in the final document.

**`responsibilities.text` details**
1. `responsibilities.text` is a free text section, but **must** conform to a given structure. It is **imparative** that this section be correct.
2. `responsibilities.text` may include introductory paragraph. If present, it should be refined to better align with the job description.
3. `responsibilities.text` **must** include a bulleted list of skills, achievements, and results. These should be re-ordered to emphasize alignment with the job description. Bullet points may be derived from `skills.skills`.

**Goal:**
Rewrite the `summary.text` and `responsibilities.text` within the `role` to use keywords and concepts from the `job_analysis`. Emphasize accomplishments and align the role's description with the target job's requirements. Analyze, refine, and return **every** `role`.

**Example of Refinement:**

Here is an example of the transformation you should perform.

**INPUT:**

Job Analysis (for context):
```json
{
  "key_skills": ["Python", "AWS", "SQL", "Team Leadership"],
  "primary_duties": ["Develop and maintain backend services", "Lead a small team of junior developers", "Manage cloud infrastructure on AWS", "Optimize database queries"],
  "themes": ["fast-paced environment", "ownership", "mentorship"]
}
```

Role to Refine:
```json
{
  "basics": {
    "company": "Tech Solutions Inc.",
    "start_date": "2020-01-15T00:00:00",
    "end_date": "2022-12-31T00:00:00",
    "title": "Software Engineer"
  },
  "summary": { "text": "Worked as a software engineer on backend systems." },
  "responsibilities": { "text": "Wrote code for different projects. Used Python and AWS." },
  "skills": { "skills": ["Python", "AWS", "Docker", "Git"] },
  "projects": []
}
```

---

**EXPECTED OUTPUT:**
Now, output the refined role as a JSON object:
```json
{
  "basics": {
    "company": "Tech Solutions Inc.",
    "start_date": "2020-01-15T00:00:00",
    "end_date": "2022-12-31T00:00:00",
    "title": "Software Engineer"
  },
  "summary": {
    "text": "Backend-focused Software Engineer with experience developing scalable services in a fast-paced environment. Leveraged expertise in Python and AWS to contribute to key projects, demonstrating strong ownership of features."
  },
  "responsibilities": {
    "text": "Developed and maintained backend services using Python, taking ownership of critical features from design to deployment.\n\n* Engineered RESTful APIs to support new product initiatives, improving system modularity and performance.\n* Managed and provisioned cloud infrastructure using AWS, including services like EC2 and S3, to ensure high availability for key applications.\n* Utilized Docker to containerize applications, streamlining development workflows and improving deployment velocity."
  },
  "skills": {
    "skills": ["Python", "AWS", "Docker", "Git"]
  },
  "projects": []
}
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
