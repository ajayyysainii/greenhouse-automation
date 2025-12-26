"""Configuration for Greenhouse automation"""

# Timeouts
DEFAULT_WAIT_TIMEOUT = 20
SHORT_WAIT = 2
MEDIUM_WAIT = 5
LONG_WAIT = 10

# Chrome Options
CHROME_OPTIONS = [
    "--no-sandbox",
    # "--headless=new",  # Uncomment to run in headless mode
    "--disable-dev-shm-usage",
    "--start-maximized",
    "--disable-blink-features=AutomationControlled",  # Hide automation
    "--disable-infobars",  # Hide "Chrome is being controlled" message
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Greenhouse form field selectors
class GreenhouseSelectors:
    """CSS selectors and XPaths for Greenhouse form fields"""
    
    # Basic info - Text input fields
    FIRST_NAME = 'input[id="first_name"], input[id*="first_name"], input[name*="first_name"]'
    LAST_NAME = 'input[id="last_name"], input[id*="last_name"], input[name*="last_name"]'
    PREFERRED_FIRST_NAME = 'input[id*="preferred_first_name"], input[name*="preferred_first_name"]'
    EMAIL = 'input[type="email"], input[id="email"], input[id*="email"], input[name*="email"]'
    PHONE = 'input[type="tel"], input[id="phone"], input[id*="phone"], input[name*="phone"]'
    # React Select components - use the input inside select__control
    COUNTRY = 'input[id="country"], input[id*="country"].select__input, div.select__control:has(input[id*="country"]) input'
    LOCATION_CITY = 'input[id="candidate-location"], input[id*="candidate-location"], input[id*="location"].select__input, div.select__control:has(input[id*="location"]) input'
    LOCATE_ME_BUTTON = 'button[class*="locate"], button:contains("Locate me"), button:contains("Locate Me"), button[aria-label*="Locate"], a[class*="locate"], button.btn--tertiary'
    
    # Online profiles
    LINKEDIN = 'input[id="question_29030630003"], input[id*="linkedin"], input[name*="linkedin"], input[placeholder*="LinkedIn"]'
    GITHUB = 'input[id*="github"], input[name*="github"], input[placeholder*="GitHub"], input[placeholder*="Github"]'
    PORTFOLIO = 'input[id*="portfolio"], input[name*="portfolio"], input[placeholder*="Portfolio"]'
    WEBSITE = 'input[id="question_29030631003"], input[id*="website"], input[name*="website"], input[placeholder*="Website"]'
    
    # File upload fields
    RESUME_UPLOAD = 'input[type="file"][id="resume"], input[type="file"][id*="resume"], input[type="file"][name*="resume"]'
    COVER_LETTER_UPLOAD = 'input[type="file"][id="cover_letter"], input[type="file"][id*="cover"], input[type="file"][name*="cover"]'
    
    # Education fields - React Select components
    EDUCATION_SCHOOL = 'input[id="school--0"], input[id^="school--"], input.select__input[id*="school"], div.select__control:has(input[id*="school"]) input'
    EDUCATION_DEGREE = 'input[id="degree--0"], input[id^="degree--"], input.select__input[id*="degree"], div.select__control:has(input[id*="degree"]) input'
    EDUCATION_DISCIPLINE = 'input[id*="discipline"], input.select__input[id*="discipline"]'
    EDUCATION_START_MONTH = 'input[id*="start-month"], input.select__input[id*="start"][id*="month"]'
    EDUCATION_START_YEAR = 'input[id*="start-year"], input[type="number"][id*="start"][id*="year"]'
    EDUCATION_END_MONTH = 'input[id="end-month--0"], input[id^="end-month--"], input.select__input[id*="end-month"], div.select__control:has(input[id*="end-month"]) input'
    EDUCATION_END_YEAR = 'input[id="end-year--0"], input[id^="end-year--"], input[type="number"][id*="end-year"]'
    ADD_ANOTHER_SCHOOL = 'button.add-another-button, button:contains("Add another")'
    
    # Employment fields
    EMPLOYMENT_COMPANY = 'input[id*="company"], input[name*="company"]'
    EMPLOYMENT_TITLE = 'input[id*="title"], input[name*="title"], input[id*="job_title"]'
    EMPLOYMENT_START_MONTH = 'select[id*="employment"][id*="start"][id*="month"], select[name*="employment"][name*="start"][name*="month"]'
    EMPLOYMENT_START_YEAR = 'input[id*="employment"][id*="start"][id*="year"], input[name*="employment"][name*="start"][name*="year"]'
    EMPLOYMENT_END_MONTH = 'select[id*="employment"][id*="end"][id*="month"], select[name*="employment"][name*="end"][name*="month"]'
    EMPLOYMENT_END_YEAR = 'input[id*="employment"][id*="end"][id*="year"], input[name*="employment"][name*="end"][name*="year"]'
    EMPLOYMENT_CURRENT = 'input[type="checkbox"][id*="current"], input[type="checkbox"][name*="current"], input[type="checkbox"][id*="current_role"]'
    ADD_ANOTHER_ROLE = 'button:contains("Add another role"), button:contains("Add Role"), a:contains("Add another role")'
    
    # Voluntary self-identification - React Select
    GENDER = 'input[id="gender"], input.select__input[id*="gender"], div.select__control:has(input[id="gender"]) input'
    HISPANIC_LATINO = 'input[id="hispanic_ethnicity"], input.select__input[id*="hispanic"], input.select__input[id*="latino"], div.select__control:has(input[id*="hispanic"]) input'
    VETERAN_STATUS = 'input[id="veteran_status"], input.select__input[id*="veteran"], div.select__control:has(input[id="veteran_status"]) input'
    DISABILITY_STATUS = 'input[id="disability_status"], input.select__input[id*="disability"], div.select__control:has(input[id="disability_status"]) input'
    
    # Work preferences
    LANGUAGES = 'select[id*="language"], select[name*="language"], input[id*="language"], input[name*="language"]'
    EMPLOYMENT_TYPES = 'select[id*="employment_type"], select[name*="employment_type"], input[id*="employment_type"]'
    WORKSITES = 'select[id*="worksite"], select[name*="worksite"], input[id*="worksite"]'
    LOCATION = 'input[id*="location"], input[name*="location"], input[placeholder*="Location"]'
    WILLING_TO_RELOCATE = 'input[type="checkbox"][id*="relocate"], input[type="checkbox"][name*="relocate"]'
    
    # Company-specific questions - React Select and textarea
    HOURLY_EXPECTATIONS = 'textarea[id="question_29030632003"], textarea[id*="hourly"], textarea[id*="expectations"]'
    WORK_AUTHORIZED = 'input[id="question_29030633003"], input.select__input[id*="question_29030633003"], div.select__control:has(input[id*="question_29030633003"]) input'
    REQUIRE_SPONSORSHIP = 'input[id="question_29030634003"], input.select__input[id*="question_29030634003"], div.select__control:has(input[id*="question_29030634003"]) input'
    OPEN_TO_RELOCATE = 'input[id="question_29030635003"], input.select__input[id*="question_29030635003"], div.select__control:has(input[id*="question_29030635003"]) input'
    INTERNSHIP_DATES = 'textarea[id="question_29095543003"], textarea[id*="internship"], textarea[id*="targeting"]'
    REFERRED_BY_EMPLOYEE = 'input[id="question_29030636003"], input.select__input[id*="question_29030636003"], div.select__control:has(input[id*="question_29030636003"]) input'
    REFERRER_NAME = 'textarea[id="question_29030637003"], textarea[id*="referrer"], textarea[id*="employee"]'
    
    # Buttons
    SUBMIT_BUTTON = 'button[type="submit"], button.btn--pill:contains("Submit"), button:contains("Submit application")'
    GET_STARTED = 'button:contains("Get Started"), button:contains("get started"), a:contains("Get Started")'
    SAVE_CHANGES = 'button:contains("Save Changes"), button:contains("Save"), a:contains("Save Changes")'
    CANCEL_CHANGES = 'button:contains("Cancel"), a:contains("Cancel")'
    
    # OTP/Verification code fields
    # Single input field (if all in one)
    OTP_INPUT = 'input[id*="otp"], input[id*="verification"], input[id*="code"], input[name*="otp"], input[name*="verification"], input[name*="code"], input[type="text"][placeholder*="code"], input[type="text"][placeholder*="OTP"], input[type="text"][placeholder*="verification"], input[type="text"][placeholder*="Security code"]'
    # Multiple input fields (8-character code split into separate inputs)
    OTP_INPUTS_MULTIPLE = 'input[type="text"][maxlength="1"], input[type="text"][maxlength="2"], input[aria-label*="code"], input[aria-label*="verification"], input[aria-label*="character"], div[class*="code"] input, div[class*="verification"] input, div[class*="security"] input'
    VERIFY_BUTTON = 'button[type="submit"]:contains("Verify"), button:contains("Verify"), button:contains("Submit"), button[id*="verify"], button:contains("Confirm")'
    
    # Alternative selectors using data attributes (common in Greenhouse)
    FIRST_NAME_ALT = 'input[data-field="first_name"]'
    LAST_NAME_ALT = 'input[data-field="last_name"]'
    EMAIL_ALT = 'input[data-field="email"]'

