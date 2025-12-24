from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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
            
            # Location (City) - required in some forms
            # Location (City) - React Select dropdown
            if application_input.location_city:
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.LOCATION_CITY],
                    value=application_input.location_city,
                    field_name="Location (City)",
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
            
            # GitHub Profile
            if application_input.github_profile:
                self._fill_field(
                    selectors=[GreenhouseSelectors.GITHUB],
                    value=application_input.github_profile,
                    field_name="GitHub Profile",
                    required=False,
                    silent=True
                )
            
            # Portfolio
            if application_input.portfolio:
                self._fill_field(
                    selectors=[GreenhouseSelectors.PORTFOLIO],
                    value=application_input.portfolio,
                    field_name="Portfolio",
                    required=False,
                    silent=True
                )
            
            # Fill Education section
            if application_input.education:
                self.logger.info("Filling Education section...")
                self._fill_education_section(application_input.education)
            
            # Fill Employment section (if present)
            if application_input.employment:
                self.logger.info("Filling Employment section...")
                self._fill_employment_section(application_input.employment)
            
            # Fill Company-specific questions
            self.logger.info("Filling company-specific questions...")
            self._fill_company_questions(application_input)
            
            # Fill Voluntary self-identification
            self.logger.info("Filling Voluntary self-identification...")
            self._fill_voluntary_identification(application_input)
            
            # Fill Work Preferences (if present)
            if application_input.languages or application_input.employment_types:
                self.logger.info("Filling Work Preferences...")
                self._fill_work_preferences(application_input)
            
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
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                sleep(0.2)
                
                # Check if it's a textarea
                if element.tag_name.lower() == "textarea":
                    element.clear()
                    element.send_keys(value)
                    self.logger.info(f"Filled {field_name}")
                    return True
                else:
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
        """Fill a dropdown/select field - handles native select, React Select, and custom dropdowns"""
        from selenium.webdriver.support.ui import Select
        
        element = self.helper.find_element_by_multiple_selectors(selectors, silent=silent)
        if element:
            try:
                # Check if it's a native select element
                tag_name = element.tag_name.lower()
                
                if tag_name == "select":
                    # Native select element
                    try:
                        select = Select(element)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        sleep(0.3)
                        
                        try:
                            select.select_by_visible_text(value)
                            self.logger.info(f"Selected '{value}' in {field_name} (by visible text)")
                            return True
                        except:
                            try:
                                select.select_by_value(value)
                                self.logger.info(f"Selected '{value}' in {field_name} (by value)")
                                return True
                            except:
                                # Try partial match
                                options = select.options
                                for option in options:
                                    if value.lower() in option.text.lower() or option.text.lower() in value.lower():
                                        select.select_by_visible_text(option.text)
                                        self.logger.info(f"Selected '{option.text}' in {field_name} (partial match)")
                                        return True
                    except Exception as e:
                        if not silent:
                            self.logger.error(f"Failed to select native dropdown {field_name}", e)
                
                # React Select component (most common in Greenhouse)
                # Check if it's a React Select input (check by class, ID, or by parent structure)
                is_react_select = False
                if element.tag_name.lower() == "input":
                    element_class = element.get_attribute("class") or ""
                    element_id = element.get_attribute("id") or ""
                    
                    # Check if it has select__input class
                    if "select__input" in element_class:
                        is_react_select = True
                    # Check if it's candidate-location or country (known React Select fields)
                    elif "candidate-location" in element_id or element_id == "country":
                        is_react_select = True
                    else:
                        # Check if parent has select__control class
                        try:
                            parent = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'select__control')]")
                            if parent:
                                is_react_select = True
                        except:
                            # Also check for select-shell parent
                            try:
                                parent = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'select-shell')]")
                                if parent:
                                    is_react_select = True
                            except:
                                pass
                
                if is_react_select:
                    try:
                        # Find the parent select__control div
                        try:
                            control_div = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'select__control')]")
                        except:
                            # Try alternative path
                            control_div = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'select-shell')]//div[contains(@class, 'select__control')]")
                        
                        if control_div:
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", control_div)
                            sleep(0.3)
                            
                            # Click the control to open dropdown
                            try:
                                control_div.click()
                            except:
                                # Try clicking the toggle button
                                toggle_btn = control_div.find_element(By.CSS_SELECTOR, "button.icon-button, button[aria-label*='Toggle']")
                                toggle_btn.click()
                            sleep(0.8)  # Wait for menu to appear
                            
                            # React Select menu options are typically in a menu with role="listbox" or class="select__menu"
                            value_lower = value.lower()
                            # For long text options, try exact match first, then partial match
                            option_selectors = [
                                # Exact match (case-insensitive)
                                f"//div[contains(@class, 'select__menu')]//div[@role='option' and translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{value_lower}']",
                                f"//div[@role='listbox']//div[@role='option' and translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{value_lower}']",
                                # Partial match (contains)
                                f"//div[contains(@class, 'select__menu')]//div[contains(@class, 'option') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]",
                                f"//div[@role='listbox']//div[@role='option' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]",
                                f"//div[contains(@class, 'select__menu')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]",
                                f"//div[@id='react-select-{element.get_attribute('id')}-listbox']//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]"
                            ]
                            
                            # First check if menu is open and has options
                            try:
                                # Check for "no options" message
                                no_options_msg = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'select__menu')]//div[contains(@class, 'no-options') or contains(text(), 'No options') or contains(text(), 'No results found')]")
                                if no_options_msg and any(msg.is_displayed() for msg in no_options_msg):
                                    self.logger.info(f"No options message found for '{value}' in {field_name}")
                                    return False  # Return False to trigger fallback
                            except:
                                pass
                            
                            for option_selector in option_selectors:
                                try:
                                    options = self.driver.find_elements(By.XPATH, option_selector)
                                    visible_options = [opt for opt in options if opt.is_displayed()]
                                    
                                    if not visible_options:
                                        continue  # Try next selector
                                    
                                    for option in visible_options:
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                                        sleep(0.2)
                                        try:
                                            option.click()
                                        except:
                                            self.driver.execute_script("arguments[0].click();", option)
                                        sleep(0.5)
                                        self.logger.info(f"Selected '{value}' in {field_name} (React Select)")
                                        return True
                                except:
                                    continue
                            
                            # If we get here, no options were found
                            # Check one more time if menu is empty
                            try:
                                all_menu_options = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'select__menu')]//div[@role='option']")
                                if not all_menu_options or not any(opt.is_displayed() for opt in all_menu_options):
                                    self.logger.info(f"No options found in dropdown for '{value}' in {field_name}")
                                    return False  # Return False to trigger fallback
                            except:
                                pass
                            
                            # Alternative: Type into the input and wait for autocomplete
                            try:
                                element.clear()
                                element.send_keys(value)
                                sleep(1.0)  # Wait for options to filter (longer for location autocomplete)
                                
                                # For location fields, wait a bit more for autocomplete
                                if "location" in field_name.lower() or "candidate-location" in element.get_attribute("id") or "":
                                    sleep(0.5)
                                
                                # Check if any options are available in the dropdown
                                try:
                                    # Check for "no options" message or empty menu
                                    no_options = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'select__menu')]//div[contains(@class, 'no-options') or contains(text(), 'No options') or contains(text(), 'No results')]")
                                    if no_options and any(opt.is_displayed() for opt in no_options):
                                        self.logger.info(f"No options found for '{value}' in {field_name}")
                                        return False  # Return False to trigger fallback
                                    
                                    # Try to find options
                                    all_options = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'select__menu')]//div[@role='option']")
                                    visible_options = [opt for opt in all_options if opt.is_displayed()]
                                    
                                    if not visible_options:
                                        # No visible options found
                                        self.logger.info(f"No visible options found for '{value}' in {field_name}")
                                        return False  # Return False to trigger fallback
                                    
                                    # Look for options that match the value
                                    matching_options = self.driver.find_elements(By.XPATH, f"//div[contains(@class, 'select__menu')]//div[@role='option' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value.lower()}')]")
                                    visible_matching = [opt for opt in matching_options if opt.is_displayed()]
                                    
                                    if visible_matching:
                                        visible_matching[0].click()
                                        sleep(0.3)
                                        self.logger.info(f"Selected matching option for '{value}' in {field_name}")
                                        return True
                                    
                                    # If no match, try first option
                                    if visible_options:
                                        visible_options[0].click()
                                        sleep(0.3)
                                        self.logger.info(f"Selected first option for '{value}' in {field_name}")
                                        return True
                                    else:
                                        # No options available
                                        self.logger.info(f"No options available for '{value}' in {field_name}")
                                        return False
                                except Exception as e:
                                    # If we can't find options, try pressing Enter
                                    try:
                                        element.send_keys(Keys.ENTER)
                                        sleep(0.5)
                                        # Check if value was actually selected by checking the input value
                                        current_value = element.get_attribute("value") or ""
                                        if current_value.lower() == value.lower() or value.lower() in current_value.lower():
                                            self.logger.info(f"Selected '{value}' in {field_name} (typed and Enter)")
                                            return True
                                        else:
                                            self.logger.info(f"Value not selected after Enter, no options available")
                                            return False
                                    except:
                                        return False
                            except Exception as e:
                                if not silent:
                                    self.logger.error(f"Failed to type and select in React Select {field_name}", e)
                                return False
                            
                    except Exception as e:
                        if not silent:
                            self.logger.error(f"Failed to select React Select {field_name}", e)
                
                # Custom dropdown (div-based) - try clicking approach
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    sleep(0.3)
                    
                    # Click to open dropdown
                    try:
                        element.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", element)
                    sleep(0.8)
                    
                    # Try to find and click the option
                    value_lower = value.lower()
                    option_xpaths = [
                        f"//option[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]",
                        f"//li[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]",
                        f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]",
                        f"//*[@role='option' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{value_lower}')]"
                    ]
                    
                    for option_xpath in option_xpaths:
                        try:
                            options = self.driver.find_elements(By.XPATH, option_xpath)
                            for option in options:
                                if option.is_displayed():
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                                    sleep(0.2)
                                    try:
                                        option.click()
                                    except:
                                        self.driver.execute_script("arguments[0].click();", option)
                                    sleep(0.3)
                                    self.logger.info(f"Selected '{value}' in {field_name} (custom dropdown)")
                                    return True
                        except:
                            continue
                    
                    # Alternative: Type the value and press Enter (if it's an input)
                    if element.tag_name.lower() == "input":
                        element.clear()
                        element.send_keys(value)
                        sleep(0.3)
                        element.send_keys(Keys.ENTER)
                        sleep(0.3)
                        self.logger.info(f"Selected '{value}' in {field_name} (typed and Enter)")
                        return True
                    
                except Exception as e:
                    if not silent:
                        self.logger.error(f"Failed to select custom dropdown {field_name}", e)
                
                return False
                
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
    
    def _fill_education_section(self, education_entries):
        """Fill education section - can have multiple entries"""
        for idx, edu in enumerate(education_entries):
            if idx > 0:
                # Click "Add another school" button
                self.logger.info(f"Adding education entry {idx + 1}...")
                self._click_add_another_school()
                sleep(SHORT_WAIT)
            
            self.logger.info(f"Filling education entry {idx + 1}: {edu.school}")
            
            # School (can be input or select) - with "Other" fallback
            school_filled = self._fill_dropdown_with_fallback(
                selectors=[GreenhouseSelectors.EDUCATION_SCHOOL],
                value=edu.school,
                fallback_value="Other",
                field_name=f"School {idx + 1}",
                silent=True
            )
            
            # Degree (can be input or select) - with "Other" fallback
            degree_filled = self._fill_dropdown_with_fallback(
                selectors=[GreenhouseSelectors.EDUCATION_DEGREE],
                value=edu.degree,
                fallback_value="Other",
                field_name=f"Degree {idx + 1}",
                silent=True
            )
            
            # Discipline (optional - not all forms have this)
            if edu.discipline:
                self._fill_field_or_dropdown(
                    selectors=[GreenhouseSelectors.EDUCATION_DISCIPLINE],
                    value=edu.discipline,
                    field_name=f"Discipline {idx + 1}",
                    silent=True
                )
            
            # Start date (optional - not all forms have this)
            if edu.start_month and edu.start_year:
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.EDUCATION_START_MONTH],
                    value=edu.start_month,
                    field_name=f"Start Month {idx + 1}",
                    required=False,
                    silent=True
                )
                self._fill_field(
                    selectors=[GreenhouseSelectors.EDUCATION_START_YEAR],
                    value=edu.start_year,
                    field_name=f"Start Year {idx + 1}",
                    required=False,
                    silent=True
                )
            
            # End date (if provided)
            if edu.end_month and edu.end_year:
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.EDUCATION_END_MONTH],
                    value=edu.end_month,
                    field_name=f"End Month {idx + 1}",
                    required=False,
                    silent=True
                )
                self._fill_field(
                    selectors=[GreenhouseSelectors.EDUCATION_END_YEAR],
                    value=edu.end_year,
                    field_name=f"End Year {idx + 1}",
                    required=False,
                    silent=True
                )
            
            sleep(SHORT_WAIT)
    
    def _fill_employment_section(self, employment_entries):
        """Fill employment section - can have multiple entries"""
        for idx, emp in enumerate(employment_entries):
            if idx > 0:
                # Click "Add another role" button
                self.logger.info(f"Adding employment entry {idx + 1}...")
                self._click_add_another_role()
                sleep(SHORT_WAIT)
            
            self.logger.info(f"Filling employment entry {idx + 1}: {emp.title} at {emp.company}")
            
            # Company
            self._fill_field(
                selectors=[GreenhouseSelectors.EMPLOYMENT_COMPANY],
                value=emp.company,
                field_name=f"Company {idx + 1}",
                required=False,
                silent=True
            )
            
            # Title
            self._fill_field(
                selectors=[GreenhouseSelectors.EMPLOYMENT_TITLE],
                value=emp.title,
                field_name=f"Title {idx + 1}",
                required=False,
                silent=True
            )
            
            # Start date
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.EMPLOYMENT_START_MONTH],
                value=emp.start_month,
                field_name=f"Employment Start Month {idx + 1}",
                required=False,
                silent=True
            )
            self._fill_field(
                selectors=[GreenhouseSelectors.EMPLOYMENT_START_YEAR],
                value=emp.start_year,
                field_name=f"Employment Start Year {idx + 1}",
                required=False,
                silent=True
            )
            
            # End date (if not current role)
            if not emp.current_role and emp.end_month and emp.end_year:
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.EMPLOYMENT_END_MONTH],
                    value=emp.end_month,
                    field_name=f"Employment End Month {idx + 1}",
                    required=False,
                    silent=True
                )
                self._fill_field(
                    selectors=[GreenhouseSelectors.EMPLOYMENT_END_YEAR],
                    value=emp.end_year,
                    field_name=f"Employment End Year {idx + 1}",
                    required=False,
                    silent=True
                )
            
            # Current role checkbox
            if emp.current_role:
                self._check_checkbox(
                    selectors=[GreenhouseSelectors.EMPLOYMENT_CURRENT],
                    field_name=f"Current Role {idx + 1}",
                    silent=True
                )
            
            sleep(SHORT_WAIT)
    
    def _fill_voluntary_identification(self, application_input):
        """Fill voluntary self-identification section"""
        # Gender
        if application_input.gender:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.GENDER],
                value=application_input.gender,
                field_name="Gender",
                required=False,
                silent=True
            )
        
        # Hispanic or Latino
        if application_input.hispanic_latino:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.HISPANIC_LATINO],
                value=application_input.hispanic_latino,
                field_name="Hispanic or Latino",
                required=False,
                silent=True
            )
        
        # Veteran status
        if application_input.veteran_status:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.VETERAN_STATUS],
                value=application_input.veteran_status,
                field_name="Veteran Status",
                required=False,
                silent=True
            )
        
        # Disability status (with value normalization for common variations)
        if application_input.disability_status:
            # Normalize common variations to match the actual dropdown options
            disability_value = application_input.disability_status.strip()
            disability_lower = disability_value.lower()
            
            # Map common variations to actual dropdown options
            if "yes" in disability_lower or "have a disability" in disability_lower or "have one in the past" in disability_lower:
                if "yes" in disability_lower or ("have" in disability_lower and "disability" in disability_lower):
                    disability_value = "Yes, I have a disability, or have one in the past"
            elif "no" in disability_lower and ("don't" in disability_lower or "do not" in disability_lower or "not have" in disability_lower):
                disability_value = "No, I do not have a disability and have not one in the past"
            elif "do not want" in disability_lower or "don't want" in disability_lower or "not want" in disability_lower or "decline" in disability_lower:
                disability_value = "I do not want to answer"
            
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.DISABILITY_STATUS],
                value=disability_value,
                field_name="Disability Status",
                required=False,
                silent=True
            )
    
    def _fill_work_preferences(self, application_input):
        """Fill work preferences section"""
        # Click "Get Started" if present (for work preferences section)
        self._click_get_started()
        
        # Languages (can add up to 5)
        if application_input.languages:
            for idx, language in enumerate(application_input.languages[:5]):  # Max 5
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.LANGUAGES],
                    value=language,
                    field_name=f"Language {idx + 1}",
                    required=False,
                    silent=True
                )
                sleep(0.5)  # Small delay between language selections
        
        # Employment types
        if application_input.employment_types:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.EMPLOYMENT_TYPES],
                value=application_input.employment_types,
                field_name="Employment Types",
                required=False,
                silent=True
            )
        
        # Worksites
        if application_input.worksites:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.WORKSITES],
                value=application_input.worksites,
                field_name="Worksites",
                required=False,
                silent=True
            )
        
        # Location
        if application_input.location:
            self._fill_field(
                selectors=[GreenhouseSelectors.LOCATION],
                value=application_input.location,
                field_name="Location",
                required=False,
                silent=True
            )
        
        # Willing to relocate checkbox
        if application_input.willing_to_relocate:
            self._check_checkbox(
                selectors=[GreenhouseSelectors.WILLING_TO_RELOCATE],
                field_name="Willing to Relocate",
                silent=True
            )
    
    def _fill_field_or_dropdown(self, selectors: list, value: str, field_name: str, required: bool = False, silent: bool = False) -> bool:
        """Try to fill as dropdown first, then as text field"""
        # Try as dropdown first
        success = self._fill_dropdown(selectors, value, field_name, required, silent=True)
        if success:
            return True
        
        # If dropdown failed, try as text field
        return self._fill_field(selectors, value, field_name, required, silent)
    
    def _fill_dropdown_with_fallback(self, selectors: list, value: str, fallback_value: str, field_name: str, required: bool = False, silent: bool = False) -> bool:
        """Fill a dropdown with a fallback value if the primary value is not found"""
        # First try to fill with the primary value
        success = self._fill_dropdown(selectors, value, field_name, required=required, silent=silent)
        
        # If primary value failed, try fallback (try common variations)
        if not success and fallback_value:
            self.logger.info(f"'{value}' not found in {field_name}, trying '{fallback_value}'...")
            sleep(0.5)  # Brief pause before trying fallback
            
            # Try the fallback value as-is first
            success = self._fill_dropdown(selectors, fallback_value, f"{field_name} ({fallback_value})", required=required, silent=silent)
            
            # If that fails, try common variations (Other, other, OTHER)
            if not success and fallback_value.lower() == "other":
                for variant in ["Other", "other", "OTHER"]:
                    if variant != fallback_value:
                        self.logger.info(f"Trying variant '{variant}'...")
                        success = self._fill_dropdown(selectors, variant, f"{field_name} ({variant})", required=required, silent=silent)
                        if success:
                            break
            
            if success:
                self.logger.info(f"Successfully selected fallback value for {field_name}")
        
        return success
    
    def _check_checkbox(self, selectors: list, field_name: str, required: bool = False, silent: bool = False) -> bool:
        """Check a checkbox if not already checked"""
        element = self.helper.find_element_by_multiple_selectors(selectors, silent=silent)
        if element:
            try:
                if not element.is_selected():
                    element.click()
                    if not silent:
                        self.logger.info(f"Checked {field_name}")
                    return True
                else:
                    if not silent:
                        self.logger.info(f"{field_name} already checked")
                    return True
            except Exception as e:
                if not silent:
                    self.logger.error(f"Failed to check {field_name}", e)
                return False
        else:
            if required and not silent:
                self.logger.error(f"Required checkbox not found: {field_name}")
            elif not silent:
                self.logger.info(f"Optional checkbox not found (skipping): {field_name}")
            return not required
    
    def _click_add_another_school(self) -> bool:
        """Click 'Add another school' button"""
        xpath = "//button[contains(text(), 'Add another school')] | //button[contains(text(), 'Add School')] | //a[contains(text(), 'Add another school')]"
        return self.helper.safe_click(By.XPATH, xpath, timeout=5) or \
               self.helper.safe_click_by_css(GreenhouseSelectors.ADD_ANOTHER_SCHOOL, timeout=5)
    
    def _click_add_another_role(self) -> bool:
        """Click 'Add another role' button"""
        xpath = "//button[contains(text(), 'Add another role')] | //button[contains(text(), 'Add Role')] | //a[contains(text(), 'Add another role')]"
        return self.helper.safe_click(By.XPATH, xpath, timeout=5) or \
               self.helper.safe_click_by_css(GreenhouseSelectors.ADD_ANOTHER_ROLE, timeout=5)
    
    def _click_get_started(self) -> bool:
        """Click 'Get Started' button if present"""
        xpath = "//button[contains(text(), 'Get Started')] | //button[contains(text(), 'get started')] | //a[contains(text(), 'Get Started')]"
        return self.helper.safe_click(By.XPATH, xpath, timeout=2)
    
    def _fill_company_questions(self, application_input):
        """Fill company-specific questions"""
        # Hourly expectations (textarea)
        if application_input.hourly_expectations:
            # Try as textarea first, then as input
            element = self.helper.find_element_by_multiple_selectors(
                ['textarea[id="question_29030632003"]', 'textarea[id*="hourly"]', 'input[id*="hourly"]'],
                silent=True
            )
            if element:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    sleep(0.2)
                    element.clear()
                    element.send_keys(application_input.hourly_expectations)
                    self.logger.info("Filled Hourly Expectations")
                except Exception as e:
                    self.logger.error(f"Failed to fill Hourly Expectations: {str(e)}")
            else:
                self._fill_field(
                    selectors=[GreenhouseSelectors.HOURLY_EXPECTATIONS],
                    value=application_input.hourly_expectations,
                    field_name="Hourly Expectations",
                    required=False,
                    silent=True
                )
        
        # Work authorization
        if application_input.work_authorized:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.WORK_AUTHORIZED],
                value=application_input.work_authorized,
                field_name="Work Authorized",
                required=False,
                silent=True
            )
        
        # Require sponsorship
        if application_input.require_sponsorship:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.REQUIRE_SPONSORSHIP],
                value=application_input.require_sponsorship,
                field_name="Require Sponsorship",
                required=False,
                silent=True
            )
        
        # Open to relocate
        if application_input.open_to_relocate:
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.OPEN_TO_RELOCATE],
                value=application_input.open_to_relocate,
                field_name="Open to Relocate",
                required=False,
                silent=True
            )
        
        # Internship dates (textarea)
        if application_input.internship_dates:
            # Try as textarea first
            element = self.helper.find_element_by_multiple_selectors(
                ['textarea[id="question_29095543003"]', 'textarea[id*="internship"]', 'textarea[id*="targeting"]'],
                silent=True
            )
            if element:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    sleep(0.2)
                    element.clear()
                    element.send_keys(application_input.internship_dates)
                    self.logger.info("Filled Internship Dates")
                except Exception as e:
                    self.logger.error(f"Failed to fill Internship Dates: {str(e)}")
            else:
                self._fill_dropdown(
                    selectors=[GreenhouseSelectors.INTERNSHIP_DATES],
                    value=application_input.internship_dates,
                    field_name="Internship Dates",
                    required=False,
                    silent=True
                )
        
        # Referred by employee
        was_referred = False
        if application_input.referred_by_employee:
            referred_value = application_input.referred_by_employee.strip()
            referred_lower = referred_value.lower()
            
            # Check if the answer indicates they were referred
            was_referred = (
                "yes" in referred_lower and "no" not in referred_lower or
                referred_lower == "yes" or
                "referred" in referred_lower and "not" not in referred_lower
            )
            
            self._fill_dropdown(
                selectors=[GreenhouseSelectors.REFERRED_BY_EMPLOYEE],
                value=application_input.referred_by_employee,
                field_name="Referred by Employee",
                required=False,
                silent=True
            )
            
            # Wait a bit for any conditional fields to appear
            sleep(1.0)  # Increased wait time for conditional field to appear
        
        # Referrer name field - always try to fill if provided
        # The field label says "If you were referred, please provide the name of the employee"
        # It's required when referred, but the field might always be visible
        if application_input.referrer_name:
            self.logger.info("Filling referrer name field...")
            # Try as textarea first (this is the actual field ID from the HTML)
            element = self.helper.find_element_by_multiple_selectors(
                ['textarea[id="question_29030637003"]', 'textarea[id*="referrer"]', 'textarea[id*="employee"]', 'input[id*="referrer"]'],
                silent=True
            )
            if element:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    sleep(0.3)
                    element.clear()
                    element.send_keys(application_input.referrer_name)
                    self.logger.info(f"Filled Referrer Name: {application_input.referrer_name}")
                except Exception as e:
                    self.logger.error(f"Failed to fill Referrer Name: {str(e)}")
            else:
                # Fallback to generic selector
                self._fill_field(
                    selectors=[GreenhouseSelectors.REFERRER_NAME],
                    value=application_input.referrer_name,
                    field_name="Referrer Name",
                    required=False,
                    silent=True
                )
        elif was_referred:
            self.logger.warning("User was referred but no referrer name provided. The form may require this field.")


def run_automation(input_data: dict) -> dict:
    """Convenience function to run automation from dict input"""
    application_input = GreenhouseApplicationInput.from_dict(input_data)
    automation = GreenhouseAutomation()
    result = automation.run(application_input)
    return result.to_dict()

