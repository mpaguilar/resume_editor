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
1.  **Stick to the Facts:** You MUST NOT invent, embellish, or add any information that is not present in the original `role` object. Rephrasing and re-contextualizing are encouraged.
2.  **Strictly Adhere to Format:** Your response MUST be a single JSON object enclosed in ```json ... ```. The JSON object must conform to the schema of the provided `role` object.
3.  **Refine, Don't Replace:** Your goal is to improve the summary and responsibilities based on the job analysis. Do not change factual data like company name, title, or dates.
4.  **Skills Synchronization:** Ensure that any skill mentioned in the `responsibilities` text is also listed in the `skills.skills` list.

**Goal:**
Rewrite the `summary.text` and `responsibilities.text` within the `role` to use keywords and concepts from the `job_analysis`. Emphasize accomplishments and align the role's description with the target job's requirements.

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
