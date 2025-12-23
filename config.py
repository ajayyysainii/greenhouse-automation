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
    
    # Text input fields
    FIRST_NAME = 'input[id*="first_name"], input[name*="first_name"]'
    LAST_NAME = 'input[id*="last_name"], input[name*="last_name"]'
    PREFERRED_FIRST_NAME = 'input[id*="preferred_first_name"], input[name*="preferred_first_name"]'
    EMAIL = 'input[type="email"], input[id*="email"], input[name*="email"]'
    PHONE = 'input[type="tel"], input[id*="phone"], input[name*="phone"]'
    COUNTRY = 'select[id*="country"], select[name*="country"]'
    LINKEDIN = 'input[id*="linkedin"], input[name*="linkedin"], input[placeholder*="LinkedIn"]'
    WEBSITE = 'input[id*="website"], input[name*="website"], input[placeholder*="Website"]'
    
    # File upload fields
    RESUME_UPLOAD = 'input[type="file"][id*="resume"], input[type="file"][name*="resume"], input[type="file"][accept*="pdf"]'
    COVER_LETTER_UPLOAD = 'input[type="file"][id*="cover"], input[type="file"][name*="cover"], input[type="file"][accept*="pdf"]'
    
    # Buttons
    SUBMIT_BUTTON = 'input[type="submit"], button[type="submit"], button:contains("Submit"), a:contains("Submit")'
    
    # Alternative selectors using data attributes (common in Greenhouse)
    FIRST_NAME_ALT = 'input[data-field="first_name"]'
    LAST_NAME_ALT = 'input[data-field="last_name"]'
    EMAIL_ALT = 'input[data-field="email"]'

