from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

# Handle both relative and absolute imports
try:
    from .config import DEFAULT_WAIT_TIMEOUT, CHROME_OPTIONS, GreenhouseSelectors, SHORT_WAIT, MEDIUM_WAIT
    from .models import GreenhouseApplicationInput, ApplicationResult
    from .utils import WebDriverHelper, Logger, sleep
    try:
        from .utils import take_screenshot
    except ImportError:
        take_screenshot = None
except ImportError:
    from config import DEFAULT_WAIT_TIMEOUT, CHROME_OPTIONS, GreenhouseSelectors, SHORT_WAIT, MEDIUM_WAIT
    from models import GreenhouseApplicationInput, ApplicationResult
    from utils import WebDriverHelper, Logger, sleep
    try:
        from utils import take_screenshot
    except ImportError:
        take_screenshot = None


class GreenhouseAutomation:
    """Main automation class for Greenhouse job application"""
    
    def __init__(self):
        self.driver = None
        self.helper = None
        self.logger = Logger()
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        self.logger.info("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        for option in CHROME_OPTIONS:
            chrome_options.add_argument(option)
        
        # Additional stealth settings to reduce CAPTCHA triggers
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute stealth scripts to hide automation
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        wait = WebDriverWait(self.driver, DEFAULT_WAIT_TIMEOUT)
        self.helper = WebDriverHelper(self.driver, wait)
        
        self.logger.success("WebDriver setup complete")
    
    def teardown_driver(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.logger.info("Closing WebDriver...")
            self.driver.quit()
    
    def run(self, application_input: GreenhouseApplicationInput) -> ApplicationResult:
        """Main entry point for automation"""
        try:
            self.logger.info("Starting Greenhouse automation...")
            
            # Setup
            self.setup_driver()
            
            # Navigate to job URL
            if not application_input.job_url:
                return ApplicationResult(
                    status="error",
                    message="Job URL is required"
                )
            
            self.logger.info(f"Navigating to job URL: {application_input.job_url}")
            self.driver.get(application_input.job_url)
            sleep(MEDIUM_WAIT)
            
            # Fill the application form
            result = self._fill_application_form(application_input)
            
            if result.status == "success":
                self.logger.success("Application submitted successfully!")
            else:
                self.logger.error(f"Application failed: {result.message}")
            
            return result
            
        except Exception as e:
            self.logger.error("Automation failed", e)
            return ApplicationResult(
                status="error",
                message=f"Automation error: {str(e)}"
            )
        
        finally:
            # Keep browser open briefly to see the result, then close
            sleep(2)
            self.teardown_driver()
    
    def _fill_application_form(self, application_input: GreenhouseApplicationInput) -> ApplicationResult:
        """Fill the Greenhouse application form"""
        self.logger.info("Filling application form...")
        
        try:
            # Wait for form to load
            sleep(SHORT_WAIT)
            
            # Fill required fields
            self.logger.info("Filling required fields...")
            
            # First Name (required)
            if not self._fill_field(
                selectors=[GreenhouseSelectors.FIRST_NAME, GreenhouseSelectors.FIRST_NAME_ALT],
                value=application_input.first_name,
                field_name="First Name"
            ):
                return ApplicationResult(status="error", message="Failed to fill First Name field")
            
            # Last Name (required)
            if not self._fill_field(
                selectors=[GreenhouseSelectors.LAST_NAME, GreenhouseSelectors.LAST_NAME_ALT],
                value=application_input.last_name,
                field_name="Last Name"
            ):
                return ApplicationResult(status="error", message="Failed to fill Last Name field")
            
            # Email (required)
            if not self._fill_field(
                selectors=[GreenhouseSelectors.EMAIL, GreenhouseSelectors.EMAIL_ALT],
                value=application_input.email,
                field_name="Email"
            ):
                return ApplicationResult(status="error", message="Failed to fill Email field")
            
            # Resume upload (required)
            if not self.helper.safe_upload_file(
                GreenhouseSelectors.RESUME_UPLOAD,
                application_input.resume_path
            ):
                return ApplicationResult(status="error", message="Failed to upload Resume")
            
            sleep(SHORT_WAIT)  # Wait for file upload to process
            
            # Fill optional fields
            self.logger.info("Filling optional fields...")
            
            # Preferred First Name
            if application_input.preferred_first_name:
                self._fill_field(
                    selectors=[GreenhouseSelectors.PREFERRED_FIRST_NAME],
                    value=application_input.preferred_first_name,
                    field_name="Preferred First Name",
                    required=False,
                    silent=True
                )
            
            # Phone
            if application_input.phone:
                self._fill_field(
                    selectors=[GreenhouseSelectors.PHONE],
                    value=application_input.phone,
                    field_name="Phone",
                    required=False,
                    silent=True
                )
            
            # Country
            if application_input.country:
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.COUNTRY],
                    value=application_input.country,
                    field_name="Country",
                    required=False,
                    silent=True
                )
            
            # Cover Letter upload
            if application_input.cover_letter_path:
                self.helper.safe_upload_file(
                    GreenhouseSelectors.COVER_LETTER_UPLOAD,
                    application_input.cover_letter_path
                )
                sleep(SHORT_WAIT)
            
            # LinkedIn Profile
            if application_input.linkedin_profile:
                self._fill_field(
                    selectors=[GreenhouseSelectors.LINKEDIN],
                    value=application_input.linkedin_profile,
                    field_name="LinkedIn Profile",
                    required=False,
                    silent=True
                )
            
            # Website
            if application_input.website:
                self._fill_field(
                    selectors=[GreenhouseSelectors.WEBSITE],
                    value=application_input.website,
                    field_name="Website",
                    required=False,
                    silent=True
                )
            
            # Submit the form
            self.logger.info("Submitting application...")
            sleep(MEDIUM_WAIT)  # Wait a bit longer for form to be ready
            
            # Scroll to top first, then to bottom to ensure all fields are processed
            try:
                self.driver.execute_script("window.scrollTo(0, 0);")
                sleep(0.5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(1)
            except:
                pass
            
            # Try to find and click submit button
            submit_success = self._submit_form()
            
            if submit_success:
                sleep(MEDIUM_WAIT)  # Wait for submission to process
                return ApplicationResult(
                    status="success",
                    message="Application submitted successfully"
                )
            else:
                return ApplicationResult(
                    status="error",
                    message="Failed to submit application form"
                )
                
        except Exception as e:
            self.logger.error("Error filling form", e)
            return ApplicationResult(
                status="error",
                message=f"Error filling form: {str(e)}"
            )
    
    def _fill_field(self, selectors: list, value: str, field_name: str, required: bool = True, silent: bool = False) -> bool:
        """Fill a form field using multiple selector strategies"""
        element = self.helper.find_element_by_multiple_selectors(selectors, silent=silent)
        if element:
            try:
                element.clear()
                element.send_keys(value)
                self.logger.info(f"Filled {field_name}")
                return True
            except Exception as e:
                if not silent:
                    self.logger.error(f"Failed to fill {field_name}", e)
                return False
        else:
            if required:
                self.logger.error(f"Required field not found: {field_name}")
            elif not silent:
                self.logger.info(f"Optional field not found (skipping): {field_name}")
            return not required
    
    def _fill_dropdown(self, selectors: list, value: str, field_name: str, required: bool = True, silent: bool = False) -> bool:
        """Fill a dropdown/select field"""
        from selenium.webdriver.support.ui import Select
        
        element = self.helper.find_element_by_multiple_selectors(selectors, silent=silent)
        if element:
            try:
                select = Select(element)
                # Try to select by visible text first
                try:
                    select.select_by_visible_text(value)
                except:
                    # If that fails, try by value
                    select.select_by_value(value)
                self.logger.info(f"Selected {value} in {field_name}")
                return True
            except Exception as e:
                if not silent:
                    self.logger.error(f"Failed to select {field_name}", e)
                return False
        else:
            if required:
                self.logger.error(f"Required dropdown not found: {field_name}")
            elif not silent:
                self.logger.info(f"Optional dropdown not found (skipping): {field_name}")
            return not required
    
    def _submit_form(self) -> bool:
        """Submit the application form"""
        self.logger.info("Looking for submit button...")
        
        # Scroll to bottom to ensure submit button is visible
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)
        except:
            pass
        
        # Try CSS selectors first (simple ones)
        css_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[data-testid*="submit"]',
            'button[id*="submit"]',
            'button[class*="submit"]',
            'button[class*="Submit"]',
            'a[class*="submit"]',
            '[data-testid*="submit"]',
            '[id*="submit"]',
            '[class*="submit"]',
            'button[aria-label*="Submit"]',
            'button[aria-label*="submit"]'
        ]
        
        for selector in css_selectors:
            element = self.helper.safe_find_element_by_css(selector, timeout=2)
            if element:
                try:
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    sleep(0.5)
                    # Try regular click first
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        self.logger.success(f"Clicked submit button using selector: {selector}")
                        return True
                    # If not enabled, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    self.logger.success(f"Clicked submit button (JS) using selector: {selector}")
                    return True
                except Exception as e:
                    self.logger.info(f"Failed to click with selector {selector}: {str(e)}")
                    continue
        
        # Try finding by text content using XPath (case-insensitive)
        xpath_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
            "//input[@type='submit']",
            "//button[@type='submit']",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//button[normalize-space(text())='Submit']",
            "//button[normalize-space(text())='Submit application']",
            "//button[normalize-space(text())='Apply']"
        ]
        
        for xpath in xpath_selectors:
            element = self.helper.safe_find_element(By.XPATH, xpath, timeout=2)
            if element:
                try:
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    sleep(0.5)
                    if element.is_displayed():
                        element.click()
                        self.logger.success(f"Clicked submit button using XPath: {xpath[:50]}...")
                        return True
                    # Try JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    self.logger.success(f"Clicked submit button (JS) using XPath: {xpath[:50]}...")
                    return True
                except Exception as e:
                    self.logger.info(f"Failed to click with XPath {xpath[:50]}: {str(e)}")
                    continue
        
        # Last resort: Try to find any button near the bottom of the form
        self.logger.info("Trying to find submit button by position...")
        try:
            # Find all buttons on the page
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
            all_submit_candidates = list(buttons) + list(inputs)
            
            # Filter buttons that might be submit buttons
            for btn in all_submit_candidates:
                try:
                    text = btn.text.lower()
                    btn_type = btn.get_attribute("type")
                    btn_class = btn.get_attribute("class") or ""
                    
                    if (btn_type == "submit" or 
                        "submit" in text or 
                        "apply" in text or
                        "submit" in btn_class.lower()):
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", btn)
                            self.logger.success(f"Clicked submit button by text/type: {text[:30]}")
                            return True
                except:
                    continue
        except Exception as e:
            self.logger.error(f"Error in last resort button search: {str(e)}")
        
        # Debug: Print page source snippet to help diagnose
        self.logger.error("Could not find submit button. Attempting to debug...")
        try:
            # Take a screenshot for debugging
            if take_screenshot:
                take_screenshot(self.driver, "greenhouse_form_debug.png")
                self.logger.info("Screenshot saved as greenhouse_form_debug.png")
            
            # Try to find any buttons and log their info
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
            all_buttons = list(buttons) + list(inputs)
            
            self.logger.info(f"Found {len(all_buttons)} buttons/inputs on page")
            for i, btn in enumerate(all_buttons[:10]):  # Log first 10 buttons
                try:
                    text = btn.text or btn.get_attribute("value") or ""
                    btn_type = btn.get_attribute("type") or ""
                    btn_class = btn.get_attribute("class") or ""
                    btn_id = btn.get_attribute("id") or ""
                    is_displayed = btn.is_displayed()
                    is_enabled = btn.is_enabled()
                    self.logger.info(f"Button {i+1}: text='{text[:50]}', type='{btn_type}', id='{btn_id}', class='{btn_class[:50]}', displayed={is_displayed}, enabled={is_enabled}")
                except Exception as e:
                    self.logger.info(f"Button {i+1}: Error reading - {str(e)}")
        except Exception as e:
            self.logger.error(f"Error in debug logging: {str(e)}")
        
        return False


def run_automation(input_data: dict) -> dict:
    """Convenience function to run automation from dict input"""
    application_input = GreenhouseApplicationInput.from_dict(input_data)
    automation = GreenhouseAutomation()
    result = automation.run(application_input)
    return result.to_dict()

