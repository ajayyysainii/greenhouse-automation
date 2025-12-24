from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class EducationEntry:
    """Education entry data"""
    school: str
    degree: str
    discipline: Optional[str] = None  # Not always present
    start_month: Optional[str] = None  # Not always present
    start_year: Optional[str] = None  # Not always present
    end_month: Optional[str] = None
    end_year: Optional[str] = None


@dataclass
class EmploymentEntry:
    """Employment entry data"""
    company: str
    title: str
    start_month: str
    start_year: str
    end_month: Optional[str] = None
    end_year: Optional[str] = None
    current_role: bool = False


@dataclass
class GreenhouseApplicationInput:
    """Input data for Greenhouse job application"""
    first_name: str
    last_name: str
    email: str
    resume_path: str  # Path to resume file
    job_url: str = ""  # Greenhouse job URL
    
    # Basic info
    preferred_first_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    location_city: Optional[str] = None  # Location (City) - required in some forms
    cover_letter_path: Optional[str] = None  # Path to cover letter file
    
    # Online profiles
    linkedin_profile: Optional[str] = None
    github_profile: Optional[str] = None
    portfolio: Optional[str] = None
    website: Optional[str] = None
    
    # Education (can have multiple)
    education: List[EducationEntry] = field(default_factory=list)
    
    # Employment (can have multiple)
    employment: List[EmploymentEntry] = field(default_factory=list)
    
    # Voluntary self-identification
    gender: Optional[str] = None
    hispanic_latino: Optional[str] = None  # "yes", "no", "do not wish to answer"
    veteran_status: Optional[str] = None
    disability_status: Optional[str] = None
    
    # Work preferences
    languages: List[str] = field(default_factory=list)  # Up to 5 languages
    employment_types: Optional[str] = None
    worksites: Optional[str] = None
    location: Optional[str] = None
    willing_to_relocate: bool = False
    
    # Company-specific questions
    hourly_expectations: Optional[str] = None  # Hourly pay expectations in USD
    work_authorized: Optional[str] = None  # Are you legally authorized to work in the United States?
    require_sponsorship: Optional[str] = None  # Will you require sponsorship?
    open_to_relocate: Optional[str] = None  # Are you open to relocating?
    internship_dates: Optional[str] = None  # Which internship start/end date are you targeting?
    referred_by_employee: Optional[str] = None  # Were you referred by a current employee?
    referrer_name: Optional[str] = None  # If referred, name of the employee
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create GreenhouseApplicationInput from dictionary"""
        # Parse education entries
        education_entries = []
        if "education" in data:
            for edu in data["education"]:
                education_entries.append(EducationEntry(
                    school=edu.get("school", ""),
                    degree=edu.get("degree", ""),
                    discipline=edu.get("discipline"),
                    start_month=edu.get("startMonth"),
                    start_year=edu.get("startYear"),
                    end_month=edu.get("endMonth"),
                    end_year=edu.get("endYear")
                ))
        
        # Parse employment entries
        employment_entries = []
        if "employment" in data:
            for emp in data["employment"]:
                employment_entries.append(EmploymentEntry(
                    company=emp.get("company", ""),
                    title=emp.get("title", ""),
                    start_month=emp.get("startMonth", ""),
                    start_year=emp.get("startYear", ""),
                    end_month=emp.get("endMonth"),
                    end_year=emp.get("endYear"),
                    current_role=emp.get("currentRole", False)
                ))
        
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            email=data.get("email", ""),
            resume_path=data.get("resumePath", ""),
            job_url=data.get("jobUrl", ""),
            preferred_first_name=data.get("preferredFirstName"),
            phone=data.get("phone"),
            country=data.get("country"),
            location_city=data.get("locationCity"),
            cover_letter_path=data.get("coverLetterPath"),
            linkedin_profile=data.get("linkedinProfile"),
            github_profile=data.get("githubProfile"),
            portfolio=data.get("portfolio"),
            website=data.get("website"),
            education=education_entries,
            employment=employment_entries,
            gender=data.get("gender"),
            hispanic_latino=data.get("hispanicLatino"),
            veteran_status=data.get("veteranStatus"),
            disability_status=data.get("disabilityStatus"),
            languages=data.get("languages", []),
            employment_types=data.get("employmentTypes"),
            worksites=data.get("worksites"),
            location=data.get("location"),
            willing_to_relocate=data.get("willingToRelocate", False),
            hourly_expectations=data.get("hourlyExpectations"),
            work_authorized=data.get("workAuthorized"),
            require_sponsorship=data.get("requireSponsorship"),
            open_to_relocate=data.get("openToRelocate"),
            internship_dates=data.get("internshipDates"),
            referred_by_employee=data.get("referredByEmployee"),
            referrer_name=data.get("referrerName")
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

