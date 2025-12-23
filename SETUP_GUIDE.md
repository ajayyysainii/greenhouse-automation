# Setup Guide - Using Greenhouse Automation with Your Real Data

## Step 1: Update input.json with Your Information

Edit the `input.json` file and replace the example data with your real information:

### Required Fields (must fill):
- `firstName`: Your first name
- `lastName`: Your last name  
- `email`: Your email address
- `resumePath`: Path to your resume file (use `./resume.pdf` if it's in the same folder)
- `jobUrl`: The Greenhouse job posting URL you want to apply to

### Optional Fields (can leave empty or remove):
- `preferredFirstName`: If you have a preferred first name
- `phone`: Your phone number (format: +1-555-123-4567 or any format)
- `country`: Your country name (e.g., "United States", "India", "Canada")
- `coverLetterPath`: Path to your cover letter (use `./cover_letter.pdf` if it's in the same folder)
- `linkedinProfile`: Your LinkedIn profile URL
- `website`: Your personal website URL

## Step 2: Prepare Your Files

Make sure your resume and cover letter files are in the `greenhouse_automation` directory:
- `resume.pdf` (or update the path in input.json)
- `cover_letter.pdf` (optional, only if you want to include it)

**Supported file formats:** PDF, DOC, DOCX, TXT, RTF

## Step 3: Update the Job URL

Replace the `jobUrl` in `input.json` with the actual Greenhouse job posting URL you want to apply to.

Example:
```json
"jobUrl": "https://job-boards.greenhouse.io/company-name/jobs/1234567"
```

## Step 4: Run the Automation

From the `greenhouse_automation` directory, run:

```bash
python3 run.py input.json
```

Or from the parent directory:

```bash
cd /Users/ajayyy/Downloads/coding/automation
python3 -m greenhouse_automation.main greenhouse_automation/input.json
```

## Example input.json with Real Data

```json
{
    "firstName": "YourFirstName",
    "lastName": "YourLastName",
    "email": "your.email@example.com",
    "resumePath": "./resume.pdf",
    "jobUrl": "https://job-boards.greenhouse.io/company/jobs/1234567",
    "phone": "+1-555-123-4567",
    "country": "United States",
    "coverLetterPath": "./cover_letter.pdf",
    "linkedinProfile": "https://www.linkedin.com/in/yourprofile",
    "website": "https://yourwebsite.com"
}
```

## Important Notes:

1. **File Paths**: Use `./filename.pdf` for files in the same directory, or absolute paths like `/Users/ajayyy/Downloads/resume.pdf`

2. **Test First**: Consider testing with a job you're less interested in first to make sure everything works

3. **Headless Mode**: The browser runs in headless mode by default. To see what's happening, edit `config.py` and remove `"--headless=new"` from `CHROME_OPTIONS`

4. **ChromeDriver**: Make sure ChromeDriver is installed and up to date

5. **Review Before Submitting**: The automation will fill and submit the form automatically. Make sure your data is correct before running!

## Troubleshooting:

- If file not found: Use absolute paths or make sure files are in the correct directory
- If submit fails: Check the `greenhouse_form_debug.png` screenshot that gets created
- If fields not found: Some Greenhouse forms may have different field names - check the debug output


