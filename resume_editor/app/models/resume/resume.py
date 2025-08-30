import logging

from pydantic import BaseModel

from .certifications import Certifications
from .education import Education
from .experience import Experience
from .personal import Personal

log = logging.getLogger(__name__)


class Resume(BaseModel):
    """
    Represents a resume.

    This class models a resume document, organizing personal information, education, work experience, and certifications.

    Attributes:
        personal (Personal | None): Personal information such as name, contact details, and summary.
        education (Education | None): Educational background, including degrees and institutions.
        experience (Experience | None): Work history, including job titles, companies, and responsibilities.
        certifications (Certifications | None): Professional certifications held by the individual.

    """

    personal: Personal | None = None
    education: Education | None = None
    experience: Experience | None = None
    certifications: Certifications | None = None
