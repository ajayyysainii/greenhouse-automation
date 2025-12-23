from dataclasses import dataclass
from typing import Optional


@dataclass
class GreenhouseApplicationInput:
    """Input data for Greenhouse job application"""
    first_name: str
    last_name: str
    email: str
    resume_path: str  # Path to resume file
    preferred_first_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    cover_letter_path: Optional[str] = None  # Path to cover letter file
    linkedin_profile: Optional[str] = None
    website: Optional[str] = None
    job_url: str = ""  # Greenhouse job URL
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create GreenhouseApplicationInput from dictionary"""
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            email=data.get("email", ""),
            resume_path=data.get("resumePath", ""),
            preferred_first_name=data.get("preferredFirstName"),
            phone=data.get("phone"),
            country=data.get("country"),
            cover_letter_path=data.get("coverLetterPath"),
            linkedin_profile=data.get("linkedinProfile"),
            website=data.get("website"),
            job_url=data.get("jobUrl", "")
        )


@dataclass
class ApplicationResult:
    """Result of application process"""
    status: str
    message: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "status": self.status,
            "message": self.message
        }

