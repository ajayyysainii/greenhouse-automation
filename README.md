# Greenhouse Job Application Automation

This module automates the process of filling out and submitting job applications on Greenhouse job boards.

## Features

- Automatically fills required fields (First Name, Last Name, Email, Resume)
- Optionally fills additional fields (Preferred First Name, Phone, Country, Cover Letter, LinkedIn, Website)
- Handles file uploads for resume and cover letter
- Robust error handling and logging

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome browser installed and ChromeDriver available in your PATH, or install it:
```bash
# macOS
brew install chromedriver

# Or download from https://chromedriver.chromium.org/
```

## Usage

### As a Python Module

```python
from greenhouse_automation import run_greenhouse_automation

input_data = {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "resumePath": "/path/to/resume.pdf",
    "jobUrl": "https://job-boards.greenhouse.io/didi/jobs/7492964",
    # Optional fields:
    "preferredFirstName": "Johnny",
    "phone": "+1234567890",
    "country": "United States",
    "coverLetterPath": "/path/to/cover_letter.pdf",
    "linkedinProfile": "https://linkedin.com/in/johndoe",
    "website": "https://johndoe.com"
}

result = run_greenhouse_automation(input_data)
print(result)
```

### Command Line Usage

1. Create a JSON input file (e.g., `input.json`):

```json
{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "resumePath": "/path/to/resume.pdf",
    "jobUrl": "https://job-boards.greenhouse.io/didi/jobs/7492964",
    "phone": "+1234567890",
    "linkedinProfile": "https://linkedin.com/in/johndoe"
}
```

2. Run the automation:

**Option 1: From the parent directory (recommended):**
```bash
cd /Users/ajayyy/Downloads/coding/automation
python3 -m greenhouse_automation.main greenhouse_automation/input.json
```

**Option 2: Using the standalone script (from greenhouse_automation directory):**
```bash
cd greenhouse_automation
python3 run.py input.json
```

**Option 3: Pipe JSON via stdin:**
```bash
cd /Users/ajayyy/Downloads/coding/automation
echo '{"firstName":"John","lastName":"Doe",...}' | python3 -m greenhouse_automation.main
```

## Input Data Format

### Required Fields

- `firstName` (string): Your first name
- `lastName` (string): Your last name
- `email` (string): Your email address
- `resumePath` (string): Absolute or relative path to your resume file (PDF, DOC, DOCX, TXT, RTF)
- `jobUrl` (string): The Greenhouse job posting URL

### Optional Fields

- `preferredFirstName` (string): Preferred first name
- `phone` (string): Phone number
- `country` (string): Country name
- `coverLetterPath` (string): Path to cover letter file
- `linkedinProfile` (string): LinkedIn profile URL
- `website` (string): Personal website URL

## Example

```json
{
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane.smith@example.com",
    "resumePath": "./resumes/jane_smith_resume.pdf",
    "jobUrl": "https://job-boards.greenhouse.io/didi/jobs/7492964?gh_src=Simplify",
    "preferredFirstName": "Jane",
    "phone": "+1-555-123-4567",
    "country": "United States",
    "coverLetterPath": "./cover_letters/didi_cover_letter.pdf",
    "linkedinProfile": "https://www.linkedin.com/in/janesmith",
    "website": "https://janesmith.dev"
}
```

## Configuration

You can modify the behavior in `config.py`:

- `DEFAULT_WAIT_TIMEOUT`: Maximum time to wait for elements (default: 20 seconds)
- `CHROME_OPTIONS`: Chrome browser options (headless mode, etc.)

## Notes

- **Browser Visibility**: The automation runs with the browser visible by default (headless mode is disabled) so you can see what's happening and solve CAPTCHAs if needed.
- **CAPTCHA Handling**: If Greenhouse shows a CAPTCHA or security code:
  - The automation will automatically detect it
  - It will pause and wait for you to solve it manually in the browser window
  - Once solved, it will automatically continue and submit the form
  - It will wait up to 5 minutes for you to complete the CAPTCHA
- **Optional Fields**: Fields that aren't found on the form (like Preferred First Name, Country, LinkedIn, Website) will be silently skipped without showing error messages.
- Make sure file paths are absolute or relative to the current working directory.
- The automation will wait for form elements to load before filling them.
- If a required field cannot be found, the automation will stop and return an error.

## Troubleshooting

1. **ChromeDriver not found**: Make sure ChromeDriver is installed and in your PATH
2. **File not found**: Use absolute paths for resume and cover letter files
3. **Form fields not found**: Greenhouse forms may vary. Check the selectors in `config.py` and update if needed.
4. **Submission failed**: The submit button selector may need adjustment for different Greenhouse implementations.

## License

This automation tool is for personal use only. Use responsibly and in accordance with the terms of service of Greenhouse and the companies you're applying to.

