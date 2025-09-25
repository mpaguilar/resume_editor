"""This module stores the rendering settings for the resume writer."""
GENERAL_SETTINGS = {
    "personal": True,
    "certifications": True,
    "experience": True,
    "section": {
        "personal": {
            "contact_info": True,
            "banner": True,
            "websites": True,
            "name": True,
            "email": True,
            "phone": True,
            "location": True,
            "linkedin": True,
            "github": True,
            "website": True,
        },
        "certifications": {"name": True, "issuer": True},
        "experience": {
            "roles": True,
            "section": {
                "roles": {
                    "skills": True,
                    "responsibilities": True,
                    "include_situation": True,
                    "include_tasks": True,
                    "location": True,
                    "months_ago": "0",
                    "summary": True,
                }
            }
        },
        "skills_matrix": {"all_skills": True},
        "executive_summary": {
            "categories": "Architecture\nConsulting\nDevOps\nDevelopment\nProduct Support\n"
        },
    },
    "skills_matrix": False,
    "executive_summary": False,
    "font_size": "10",
    "margin_width": ".5",
    "top_margin": ".2",
    "bottom_margin": ".2",
}

EXEC_SUMMARY_SETTINGS = {
    "personal": True,
    "section": {
        "personal": {
            "contact_info": True,
            "banner": True,
            "websites": True,
            "name": True,
            "email": True,
            "phone": True,
            "location": True,
            "linkedin": True,
            "github": True,
            "website": True,
        },
        "certifications": {"name": True, "issuer": True},
        "experience": {
            "section": {
                "roles": {
                    "skills": True,
                    "responsibilities": True,
                    "include_situation": True,
                    "include_tasks": True,
                    "location": True,
                    "months_ago": "0",
                }
            }
        },
        "skills_matrix": {"all_skills": True},
        "executive_summary": {
            "categories": "Architecture\nConsulting\nDevOps\nDevelopment\nProduct Support\n"
        },
    },
    "skills_matrix": True,
    "executive_summary": True,
    "font_size": "10",
    "margin_width": ".5",
    "top_margin": ".2",
    "bottom_margin": ".2",
}


def get_render_settings(name: str) -> dict:
    """get_render_settings gets the render settings

    Args:
        name (str): name of the settings to get

    Raises:
        ValueError: if the name is unknown

    Returns:
        dict: the settings
    """
    if name == "general":
        return GENERAL_SETTINGS
    if name == "executive_summary":
        return EXEC_SUMMARY_SETTINGS
    raise ValueError(f"Unknown render setting name: {name}")
