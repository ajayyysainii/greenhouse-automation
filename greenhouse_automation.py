import os
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
    try:
        from .gmail_otp import GmailOTPReader
    except ImportError:
        GmailOTPReader = None
    try:
        from .gpt_field_filler import GPTFieldFiller
    except ImportError:
        GPTFieldFiller = None
except ImportError:
    from config import DEFAULT_WAIT_TIMEOUT, CHROME_OPTIONS, GreenhouseSelectors, SHORT_WAIT, MEDIUM_WAIT
    from models import GreenhouseApplicationInput, ApplicationResult
    from utils import WebDriverHelper, Logger, sleep
    try:
        from utils import take_screenshot
    except ImportError:
        take_screenshot = None
    try:
        from gmail_otp import GmailOTPReader
    except ImportError:
        GmailOTPReader = None
    try:
        from gpt_field_filler import GPTFieldFiller
    except ImportError:
        GPTFieldFiller = None


class GreenhouseAutomation:
    """Main automation class for Greenhouse job application"""
    
    def __init__(self, enable_gmail_otp: bool = False, gmail_credentials_file: str = 'credentials.json', gmail_token_file: str = 'token.json', enable_gpt: bool = True, gpt_model: str = 'gpt-4', openai_api_key: str = None):
        self.driver = None
        self.helper = None
        self.logger = Logger()
        self.gmail_otp_reader = None
        self.gpt_filler = None
        self.enable_gpt = enable_gpt
        self.application_context = {}
        
        # Initialize GPT field filler if enabled
        if enable_gpt and GPTFieldFiller:
            try:
                self.gpt_filler = GPTFieldFiller(api_key=openai_api_key, model=gpt_model)
                self.logger.info(f"✅ GPT field filler initialized (model: {gpt_model})")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not initialize GPT filler: {str(e)}")
                self.logger.warning("Continuing without GPT support")
                self.enable_gpt = False
        elif enable_gpt and not GPTFieldFiller:
            self.logger.warning("⚠️  GPT field filler not available (openai package not installed)")
            self.enable_gpt = False
        
        # Initialize Gmail OTP reader if enabled
        if enable_gmail_otp:
            if GmailOTPReader:
                try:
                    self.gmail_otp_reader = GmailOTPReader(gmail_credentials_file, gmail_token_file)
                    self.gmail_otp_reader.set_logger(self.logger)
                    self.logger.info("✅ Gmail OTP reader initialized")
                    
                    # Pre-authenticate if no token exists (to open browser upfront)
                    if not os.path.exists(gmail_token_file):
                        self.logger.info("🔐 No existing Gmail token found. Will authenticate when OTP is needed.")
                        self.logger.info("   A browser window will open for Google OAuth authorization.")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize Gmail OTP reader: {str(e)}")
                    self.logger.error("Please check that credentials.json exists and is valid")
                    self.gmail_otp_reader = None
            else:
                self.logger.error("❌ Gmail OTP reader requested but required packages are not installed!")
                self.logger.error("Please install: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
                self.logger.error("Or run: pip install -r requirements.txt")
    
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
        
        # Store application context for GPT
        if self.enable_gpt:
            self.application_context = application_input.to_dict() if hasattr(application_input, 'to_dict') else {}
        
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
                location_filled = self._fill_dropdown(
                    selectors=[GreenhouseSelectors.LOCATION_CITY],
                    value=application_input.location_city,
                    field_name="Location (City)",
                    required=False,
                    silent=True
                )
                
                # If location city was not filled, try clicking "Locate me" button as fallback
                if not location_filled:
                    self.logger.info("Location city not filled, trying 'Locate me' button as fallback...")
                    self._click_locate_me_button()
            
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
            
            # IMPORTANT: Fill any remaining empty fields with GPT before submitting
            if self.enable_gpt and self.gpt_filler:
                self.logger.info("🔍 Scanning for unfilled fields to complete with GPT...")
                sleep(1)  # Wait for any dynamic fields
                filled_count = self._fill_unknown_fields_with_gpt()
                if filled_count > 0:
                    self.logger.success(f"✨ GPT filled {filled_count} additional field(s)")
            
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
                return ApplicationResult(
                    status="success",
                    message="Application submitted successfully"
                )
            else:
                # Take a screenshot for debugging
                try:
                    if take_screenshot:
                        take_screenshot(self.driver, "greenhouse_submission_failed.png")
                        self.logger.info("Screenshot saved as greenhouse_submission_failed.png")
                except:
                    pass
                
                return ApplicationResult(
                    status="error",
                    message="Failed to submit application form - submission could not be verified"
                )
                
        except Exception as e:
            self.logger.error("Error filling form", e)
            return ApplicationResult(
                status="error",
                message=f"Error filling form: {str(e)}"
            )
    
    def _fill_field(self, selectors: list, value: str, field_name: str, required: bool = True, silent: bool = False) -> bool:
        """Fill a form field using multiple selector strategies"""
        # If value is missing/empty and GPT is enabled, try to generate it
        if (not value or not str(value).strip()) and self.enable_gpt and self.gpt_filler:
            try:
                self.logger.info(f"🤖 Value not provided for '{field_name}', using GPT to generate...")
                value = self.gpt_filler.get_answer(field_name, self.application_context)
                if value:
                    self.logger.success(f"✅ GPT generated: {value[:60]}...")
            except Exception as e:
                self.logger.warning(f"⚠️  GPT generation failed for '{field_name}': {str(e)}")
        
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
                            value_lower = value.lower().strip()
                            
                            # First check if menu is open and has options
                            try:
                                # Check for "no options" message
                                no_options_msg = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'select__menu')]//div[contains(@class, 'no-options') or contains(text(), 'No options') or contains(text(), 'No results found')]")
                                if no_options_msg and any(msg.is_displayed() for msg in no_options_msg):
                                    self.logger.info(f"No options message found for '{value}' in {field_name}")
                                    return False  # Return False to trigger fallback
                            except:
                                pass
                            
                            # Get all available options from the dropdown
                            all_option_selectors = [
                                "//div[contains(@class, 'select__menu')]//div[@role='option']",
                                "//div[@role='listbox']//div[@role='option']",
                                "//div[contains(@class, 'select__menu')]//div[contains(@class, 'option')]",
                                f"//div[@id='react-select-{element.get_attribute('id')}-listbox']//div[@role='option']"
                            ]
                            
                            all_options = []
                            for selector in all_option_selectors:
                                try:
                                    options = self.driver.find_elements(By.XPATH, selector)
                                    visible_options = [opt for opt in options if opt.is_displayed()]
                                    if visible_options:
                                        all_options = visible_options
                                        break
                                except:
                                    continue
                            
                            if not all_options:
                                self.logger.info(f"No options found in dropdown for '{value}' in {field_name}")
                                return False
                            
                            # Go through all options and find exact matches first
                            exact_matches = []
                            partial_matches = []
                            
                            for option in all_options:
                                try:
                                    option_text = option.text.strip()
                                    option_text_lower = option_text.lower().strip()
                                    
                                    # Check for exact match (case-insensitive)
                                    if option_text_lower == value_lower:
                                        exact_matches.append((option, option_text))
                                    # Check for partial match (contains)
                                    elif value_lower in option_text_lower:
                                        partial_matches.append((option, option_text))
                                except:
                                    continue
                            
                            # Prioritize exact matches
                            if exact_matches:
                                self.logger.info(f"Found {len(exact_matches)} exact match(es) for '{value}' in {field_name}")
                                # Select the first exact match
                                option, option_text = exact_matches[0]
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                                sleep(0.2)
                                try:
                                    option.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", option)
                                sleep(0.5)
                                self.logger.info(f"Selected exact match '{option_text}' for '{value}' in {field_name}")
                                return True
                            
                            # If no exact match, try partial matches
                            if partial_matches:
                                self.logger.info(f"Found {len(partial_matches)} partial match(es) for '{value}' in {field_name}")
                                # Select the first partial match
                                option, option_text = partial_matches[0]
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                                sleep(0.2)
                                try:
                                    option.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", option)
                                sleep(0.5)
                                self.logger.info(f"Selected partial match '{option_text}' for '{value}' in {field_name}")
                                return True
                            
                            # If no matches found, log all available options for debugging
                            try:
                                available_options = [opt.text.strip() for opt in all_options[:10]]  # First 10 options
                                self.logger.info(f"No match found for '{value}'. Available options: {available_options}")
                            except:
                                pass
                            
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
                                    
                                    # Get all filtered options after typing
                                    filtered_options = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'select__menu')]//div[@role='option']")
                                    visible_filtered = [opt for opt in filtered_options if opt.is_displayed()]
                                    
                                    if not visible_filtered:
                                        # No visible options found
                                        self.logger.info(f"No visible options found for '{value}' in {field_name}")
                                        return False  # Return False to trigger fallback
                                    
                                    # Go through all filtered options and find exact matches first
                                    exact_matches = []
                                    partial_matches = []
                                    
                                    for option in visible_filtered:
                                        try:
                                            option_text = option.text.strip()
                                            option_text_lower = option_text.lower().strip()
                                            
                                            # Check for exact match (case-insensitive)
                                            if option_text_lower == value_lower:
                                                exact_matches.append((option, option_text))
                                            # Check for partial match (contains)
                                            elif value_lower in option_text_lower:
                                                partial_matches.append((option, option_text))
                                        except:
                                            continue
                                    
                                    # Prioritize exact matches
                                    if exact_matches:
                                        self.logger.info(f"Found {len(exact_matches)} exact match(es) after typing '{value}' in {field_name}")
                                        option, option_text = exact_matches[0]
                                        option.click()
                                        sleep(0.3)
                                        self.logger.info(f"Selected exact match '{option_text}' for '{value}' in {field_name}")
                                        return True
                                    
                                    # If no exact match, try partial matches
                                    if partial_matches:
                                        self.logger.info(f"Found {len(partial_matches)} partial match(es) after typing '{value}' in {field_name}")
                                        option, option_text = partial_matches[0]
                                        option.click()
                                        sleep(0.3)
                                        self.logger.info(f"Selected partial match '{option_text}' for '{value}' in {field_name}")
                                        return True
                                    
                                    # If no match, try first visible option
                                    if visible_filtered:
                                        visible_filtered[0].click()
                                        sleep(0.3)
                                        self.logger.info(f"Selected first filtered option for '{value}' in {field_name}")
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
    
    def _get_field_label(self, element) -> str:
        """Extract the label/question text for a form field"""
        try:
            # Try to find associated label by ID
            field_id = element.get_attribute("id")
            if field_id:
                labels = self.driver.find_elements(By.CSS_SELECTOR, f'label[for="{field_id}"]')
                if labels and labels[0].text.strip():
                    return labels[0].text.strip()
            
            # Try parent label
            try:
                parent = element.find_element(By.XPATH, "./ancestor::label[1]")
                if parent and parent.text.strip():
                    return parent.text.strip()
            except:
                pass
            
            # Try preceding label (sibling)
            try:
                label = element.find_element(By.XPATH, "./preceding-sibling::label[1]")
                if label and label.text.strip():
                    return label.text.strip()
            except:
                pass
            
            # Try label in parent's previous sibling
            try:
                parent_div = element.find_element(By.XPATH, "./parent::div")
                prev_label = parent_div.find_element(By.XPATH, "./preceding-sibling::label[1]")
                if prev_label and prev_label.text.strip():
                    return prev_label.text.strip()
            except:
                pass
            
            # Try finding label in parent container
            try:
                parent_container = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'field') or contains(@class, 'form-group') or contains(@class, 'question')][1]")
                labels_in_container = parent_container.find_elements(By.TAG_NAME, "label")
                if labels_in_container and labels_in_container[0].text.strip():
                    return labels_in_container[0].text.strip()
            except:
                pass
            
            # Try finding any text in parent div that looks like a question
            try:
                parent_div = element.find_element(By.XPATH, "./parent::div")
                # Get all text from parent
                parent_text = parent_div.text.strip()
                if parent_text and len(parent_text) < 200:  # Reasonable length for a question
                    # Remove the current input value from text
                    current_value = element.get_attribute("value") or ""
                    if current_value:
                        parent_text = parent_text.replace(current_value, "").strip()
                    if parent_text:
                        return parent_text
            except:
                pass
            
            # Try aria-label
            aria_label = element.get_attribute("aria-label")
            if aria_label and aria_label.strip():
                return aria_label.strip()
            
            # Try aria-labelledby
            aria_labelledby = element.get_attribute("aria-labelledby")
            if aria_labelledby:
                try:
                    label_element = self.driver.find_element(By.ID, aria_labelledby)
                    if label_element and label_element.text.strip():
                        return label_element.text.strip()
                except:
                    pass
            
            # Try placeholder
            placeholder = element.get_attribute("placeholder")
            if placeholder and placeholder.strip():
                return placeholder.strip()
            
            # Try name attribute as last resort
            name = element.get_attribute("name")
            if name:
                # Convert name to readable text
                readable = name.replace("_", " ").replace("-", " ").title()
                return readable
            
            return None
            
        except Exception as e:
            return None
    
    def _fill_unknown_fields_with_gpt(self) -> int:
        """Scan form for empty text fields and textareas, fill them with GPT"""
        if not self.enable_gpt or not self.gpt_filler:
            return 0
        
        filled_count = 0
        
        try:
            # Scroll through the page to ensure all fields are loaded
            self.logger.info("📄 Scrolling through form to load all fields...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            sleep(0.5)
            
            # Scroll to bottom to trigger any lazy-loaded fields
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            current_position = 0
            
            while current_position < total_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                sleep(0.3)
                current_position += viewport_height
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            sleep(0.5)
            
            # First, handle ALL types of text inputs and textareas
            self.logger.info("🔍 Scanning for ALL empty input fields...")
            text_fields = self.driver.find_elements(
                By.CSS_SELECTOR,
                'input[type="text"], input[type="url"], input[type="number"], input[type="tel"], input:not([type]), textarea'
            )
            
            self.logger.info(f"   Found {len(text_fields)} input fields to check")
            
            for field in text_fields:
                try:
                    # Skip if not displayed
                    if not field.is_displayed():
                        continue
                    
                    # Skip if already filled
                    current_value = field.get_attribute("value")
                    if field.tag_name.lower() == "textarea":
                        current_value = field.text or current_value
                    
                    if current_value and current_value.strip():
                        continue
                    
                    # Skip if disabled or readonly
                    if field.get_attribute("disabled") or field.get_attribute("readonly"):
                        continue
                    
                    # Skip file inputs and search inputs
                    field_type = field.get_attribute("type")
                    if field_type in ["file", "hidden", "submit", "button", "search", "checkbox", "radio"]:
                        continue
                    
                    # Skip React Select input fields (they're handled separately)
                    field_class = field.get_attribute("class") or ""
                    if "select__input" in field_class or "react-select" in field_class:
                        continue
                    
                    # Get the field label/question
                    label = self._get_field_label(field)
                    if not label:
                        # Try harder to get a label
                        field_id = field.get_attribute("id")
                        field_name = field.get_attribute("name")
                        if field_name:
                            label = field_name.replace("_", " ").replace("-", " ").title()
                        elif field_id:
                            label = field_id.replace("_", " ").replace("-", " ").title()
                        else:
                            continue
                    
                    # Skip common fields we already filled
                    label_lower = label.lower()
                    skip_keywords = ['email', 'first name', 'last name', 'phone', 'resume', 'cv', 'password', 'confirm password']
                    if any(keyword in label_lower for keyword in skip_keywords):
                        continue
                    
                    # Check if this field matches known data from input.json
                    # If we have LinkedIn/Website in JSON but field wasn't found earlier, use it now
                    answer = None
                    
                    if ('linkedin' in label_lower or 'linked in' in label_lower) and self.application_context.get('linkedin_profile'):
                        answer = self.application_context['linkedin_profile']
                        self.logger.info(f"📋 Using LinkedIn from input.json for: {label}")
                    elif ('website' in label_lower or 'personal site' in label_lower or 'portfolio' in label_lower) and self.application_context.get('website'):
                        answer = self.application_context['website']
                        self.logger.info(f"📋 Using Website from input.json for: {label}")
                    elif ('github' in label_lower or 'git hub' in label_lower) and self.application_context.get('github_profile'):
                        answer = self.application_context['github_profile']
                        self.logger.info(f"📋 Using GitHub from input.json for: {label}")
                    elif 'portfolio' in label_lower and self.application_context.get('portfolio'):
                        answer = self.application_context['portfolio']
                        self.logger.info(f"📋 Using Portfolio from input.json for: {label}")
                    
                    # If no direct match, generate answer with GPT
                    if not answer:
                        self.logger.info(f"🤖 Generating answer for: {label}")
                        answer = self.gpt_filler.get_answer(label, self.application_context)
                    
                    if answer and answer.strip():
                        # Fill the field
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
                        sleep(0.3)
                        field.clear()
                        field.send_keys(answer)
                        self.logger.success(f"✅ Filled '{label}': {answer[:60]}{'...' if len(answer) > 60 else ''}")
                        filled_count += 1
                        sleep(0.5)
                    
                except Exception as e:
                    # Silently skip fields that cause errors
                    continue
            
            # Now handle dropdown/select fields
            self.logger.info("🔍 Scanning for empty dropdown fields...")
            select_fields = self.driver.find_elements(By.CSS_SELECTOR, 'select')
            
            for select_field in select_fields:
                try:
                    if not select_field.is_displayed():
                        continue
                    
                    # Skip if disabled
                    if select_field.get_attribute("disabled"):
                        continue
                    
                    # Check if already selected (not default/empty)
                    from selenium.webdriver.support.ui import Select
                    select = Select(select_field)
                    selected_option = select.first_selected_option
                    selected_text = selected_option.text.strip()
                    
                    # Skip if already has a non-empty selection
                    if selected_text and selected_text.lower() not in ['select', 'choose', 'please select', '-', '--', '---', '']:
                        continue
                    
                    # Get the field label
                    label = self._get_field_label(select_field)
                    if not label:
                        continue
                    
                    # Get all available options
                    options = select.options
                    option_texts = [opt.text.strip() for opt in options if opt.text.strip() and opt.text.strip().lower() not in ['select', 'choose', 'please select', '-', '--', '---', '']]
                    
                    if not option_texts:
                        continue
                    
                    # Ask GPT to choose from available options
                    question = f"{label}\n\nAvailable options: {', '.join(option_texts)}\n\nChoose the most appropriate option from the list above."
                    self.logger.info(f"🤖 Asking GPT to select from dropdown: {label}")
                    
                    answer = self.gpt_filler.get_answer(question, self.application_context)
                    
                    if answer and answer.strip():
                        # Try to select the GPT's choice
                        success = False
                        answer_clean = answer.strip()
                        
                        # Try exact match first
                        for option in options:
                            if option.text.strip() == answer_clean:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_field)
                                sleep(0.3)
                                select.select_by_visible_text(option.text.strip())
                                self.logger.success(f"✅ Selected '{option.text.strip()}' in '{label}'")
                                filled_count += 1
                                success = True
                                sleep(0.5)
                                break
                        
                        # Try partial match if exact didn't work
                        if not success:
                            for option in options:
                                if answer_clean.lower() in option.text.strip().lower() or option.text.strip().lower() in answer_clean.lower():
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_field)
                                    sleep(0.3)
                                    select.select_by_visible_text(option.text.strip())
                                    self.logger.success(f"✅ Selected '{option.text.strip()}' in '{label}' (partial match)")
                                    filled_count += 1
                                    success = True
                                    sleep(0.5)
                                    break
                        
                        if not success:
                            self.logger.warning(f"⚠️ Could not match GPT answer '{answer_clean}' to dropdown options for '{label}'")
                    
                except Exception as e:
                    continue
            
            # Handle React Select dropdowns
            self.logger.info("🔍 Scanning for React Select dropdowns...")
            react_selects = self.driver.find_elements(By.CSS_SELECTOR, 'div.select__control, div[class*="react-select"]')
            
            for react_select in react_selects:
                try:
                    if not react_select.is_displayed():
                        continue
                    
                    # Check if already has a value
                    value_div = react_select.find_elements(By.CSS_SELECTOR, '.select__single-value, .react-select__single-value')
                    if value_div and value_div[0].text.strip():
                        continue
                    
                    # Get label
                    label = self._get_field_label(react_select)
                    if not label:
                        # Try to find label by looking at parent structure
                        try:
                            parent = react_select.find_element(By.XPATH, "./ancestor::div[contains(@class, 'field')]")
                            label_elem = parent.find_element(By.CSS_SELECTOR, "label")
                            label = label_elem.text.strip()
                        except:
                            continue
                    
                    if not label:
                        continue
                    
                    # Click to open dropdown
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", react_select)
                    sleep(0.3)
                    react_select.click()
                    sleep(0.5)
                    
                    # Get available options
                    option_elements = self.driver.find_elements(By.CSS_SELECTOR, '.select__option, .react-select__option')
                    option_texts = [opt.text.strip() for opt in option_elements if opt.text.strip()]
                    
                    if option_texts:
                        # Ask GPT to choose
                        question = f"{label}\n\nAvailable options: {', '.join(option_texts)}\n\nChoose the most appropriate option from the list above."
                        self.logger.info(f"🤖 Asking GPT to select from React dropdown: {label}")
                        
                        answer = self.gpt_filler.get_answer(question, self.application_context)
                        
                        if answer and answer.strip():
                            answer_clean = answer.strip()
                            success = False
                            
                            # Try to click the matching option
                            for opt in option_elements:
                                if opt.text.strip() == answer_clean or answer_clean.lower() in opt.text.strip().lower():
                                    opt.click()
                                    self.logger.success(f"✅ Selected '{opt.text.strip()}' in '{label}'")
                                    filled_count += 1
                                    success = True
                                    sleep(0.5)
                                    break
                            
                            if not success:
                                # Close dropdown if we didn't select anything
                                react_select.click()
                                self.logger.warning(f"⚠️ Could not match GPT answer '{answer_clean}' to options for '{label}'")
                    else:
                        # Close dropdown
                        react_select.click()
                    
                except Exception as e:
                    # Try to close dropdown if error
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').click()
                    except:
                        pass
                    continue
            
            return filled_count
            
        except Exception as e:
            self.logger.error(f"Error scanning for unknown fields: {str(e)}")
            return filled_count
    
    def _handle_otp_verification(self) -> bool:
        """
        Handle OTP verification if required after form submission
        Returns True if OTP was found and filled, False otherwise
        """
        try:
            # Check if OTP input field(s) are present
            # First try single input field
            otp_element = self.helper.find_element_by_multiple_selectors(
                [GreenhouseSelectors.OTP_INPUT],
                silent=True,
                timeout=5
            )
            
            # Also check for multiple input fields (8-character code split into separate inputs)
            otp_inputs_multiple = self.driver.find_elements(By.CSS_SELECTOR, GreenhouseSelectors.OTP_INPUTS_MULTIPLE)
            # Filter to only visible inputs that look like code inputs (usually 6-8 inputs)
            visible_otp_inputs = [inp for inp in otp_inputs_multiple if inp.is_displayed()]
            # Check if we have multiple inputs (typically 6-8 for verification codes)
            has_multiple_inputs = len(visible_otp_inputs) >= 6 and len(visible_otp_inputs) <= 10
            
            if not otp_element and not has_multiple_inputs:
                # No OTP field found, form might have submitted successfully
                return False
            
            if has_multiple_inputs:
                self.logger.info(f"OTP verification detected: {len(visible_otp_inputs)} separate input fields found")
            else:
                self.logger.info("OTP verification field detected (single input)")
            
            # Check if Gmail OTP reader is available
            if not self.gmail_otp_reader:
                self.logger.error("❌ OTP field detected but Gmail OTP reader is not enabled!")
                self.logger.error("To enable Gmail OTP:")
                self.logger.error("1. Install Gmail API packages: pip install google-api-python-client google-auth-oauthlib")
                self.logger.error("2. Set up credentials.json (see GMAIL_SETUP.md)")
                self.logger.error("3. Enable Gmail OTP when creating GreenhouseAutomation:")
                self.logger.error("   automation = GreenhouseAutomation(enable_gmail_otp=True)")
                return False
            
            # Authenticate with Gmail if not already done
            if not self.gmail_otp_reader.service:
                self.logger.info("=" * 60)
                self.logger.info("🔐 GMAIL OAUTH AUTHENTICATION REQUIRED")
                self.logger.info("=" * 60)
                self.logger.info("A browser window will open shortly for Google OAuth authorization.")
                self.logger.info("Please complete the authorization in the browser window.")
                self.logger.info("This is a one-time setup - your token will be saved for future use.")
                self.logger.info("=" * 60)
                
                # Small delay to ensure message is visible
                sleep(1)
                
                if not self.gmail_otp_reader.authenticate():
                    self.logger.error("=" * 60)
                    self.logger.error("❌ Gmail API authentication failed")
                    self.logger.error("=" * 60)
                    self.logger.error("Please check:")
                    self.logger.error("1. credentials.json file exists in the greenhouse_automation folder")
                    self.logger.error("2. A browser window opened for OAuth (check if it was blocked)")
                    self.logger.error("3. You completed the OAuth authorization in the browser")
                    self.logger.error("4. Gmail API is enabled in your Google Cloud project")
                    self.logger.error("5. OAuth consent screen is configured in Google Cloud Console")
                    self.logger.error("")
                    self.logger.error("If no browser window opened:")
                    self.logger.error("- Check if pop-ups are blocked")
                    self.logger.error("- Try running the script again")
                    self.logger.error("- Check firewall/antivirus settings")
                    self.logger.error("")
                    self.logger.error("See GMAIL_SETUP.md for detailed setup instructions")
                    self.logger.error("=" * 60)
                    return False
                
                self.logger.info("=" * 60)
                self.logger.info("✅ Gmail API authentication successful!")
                self.logger.info("=" * 60)
            
            # Wait a moment for email to arrive
            self.logger.info("Waiting for OTP email...")
            sleep(5)  # Give email time to arrive
            
            # Try to get OTP from email
            # Common Greenhouse email patterns
            otp = None
            max_attempts = 3
            wait_seconds = 3
            
            for attempt in range(max_attempts):
                self.logger.info(f"Attempting to retrieve OTP (attempt {attempt + 1}/{max_attempts})...")
                
                # Try different email filters
                otp = self.gmail_otp_reader.get_otp_from_latest_email(
                    from_email=None,  # Greenhouse might use different sender addresses
                    subject_contains="verification",  # Common subject keywords
                    max_age_minutes=5
                )
                
                if not otp:
                    # Try without subject filter
                    otp = self.gmail_otp_reader.get_otp_from_latest_email(
                        from_email=None,
                        subject_contains=None,
                        max_age_minutes=5
                    )
                
                if otp:
                    self.logger.info(f"OTP retrieved: {otp}")
                    break
                
                if attempt < max_attempts - 1:
                    self.logger.info(f"OTP not found yet, waiting {wait_seconds} seconds...")
                    sleep(wait_seconds)
            
            if not otp:
                self.logger.error("Could not retrieve OTP from Gmail")
                return False
            
            # Fill OTP field(s)
            try:
                filled_successfully = False
                last_filled_element = None
                
                if has_multiple_inputs:
                    # Handle multiple input fields (8-character code)
                    self.logger.info(f"Filling {len(visible_otp_inputs)} separate input fields with code: {otp}")
                    
                    # Sort inputs by their position (left to right, top to bottom)
                    try:
                        # Get positions and sort
                        input_positions = []
                        for inp in visible_otp_inputs:
                            location = inp.location
                            input_positions.append((location['y'], location['x'], inp))
                        input_positions.sort(key=lambda x: (x[0], x[1]))  # Sort by y then x
                        sorted_inputs = [inp[2] for inp in input_positions]
                    except:
                        # Fallback: use inputs in order found
                        sorted_inputs = visible_otp_inputs
                    
                    # Fill each character into its corresponding input field
                    otp_chars = list(otp)
                    for i, input_field in enumerate(sorted_inputs[:len(otp_chars)]):
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
                            sleep(0.1)
                            input_field.clear()
                            input_field.send_keys(otp_chars[i])
                            self.logger.info(f"Filled character {i+1}/{len(otp_chars)}: {otp_chars[i]}")
                            last_filled_element = input_field
                            sleep(0.1)
                        except Exception as e:
                            self.logger.warning(f"Failed to fill character {i+1}: {str(e)}")
                    
                    self.logger.info(f"✅ OTP filled into {min(len(sorted_inputs), len(otp_chars))} input fields")
                    filled_successfully = True
                    sleep(1)
                elif otp_element:
                    # Handle single input field
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", otp_element)
                    sleep(0.3)
                    otp_element.clear()
                    otp_element.send_keys(otp)
                    self.logger.info(f"✅ OTP filled: {otp}")
                    last_filled_element = otp_element
                    filled_successfully = True
                    sleep(1)
                else:
                    self.logger.error("❌ Could not find OTP input field(s)")
                    return False
                
                if not filled_successfully:
                    self.logger.error("❌ Failed to fill OTP")
                    return False
                
                # Find and click verify/submit button
                self.logger.info("Looking for submit/verify button...")
                
                # Try multiple selectors for submit button
                submit_selectors = [
                    GreenhouseSelectors.VERIFY_BUTTON,
                    'button[type="submit"]',
                    'button:contains("Submit")',
                    'button:contains("Verify")',
                    'button:contains("Confirm")',
                    'input[type="submit"]',
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
                ]
                
                verify_button = None
                for selector in submit_selectors:
                    try:
                        if selector.startswith("//"):
                            verify_button = self.helper.safe_find_element(By.XPATH, selector, timeout=2, silent=True)
                        else:
                            verify_button = self.helper.safe_find_element_by_css(selector, timeout=2, silent=True)
                        
                        if verify_button and verify_button.is_displayed() and verify_button.is_enabled():
                            break
                        else:
                            verify_button = None
                    except:
                        continue
                
                if verify_button:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", verify_button)
                    sleep(0.3)
                    try:
                        verify_button.click()
                        self.logger.info("✅ Clicked submit/verify button")
                    except:
                        try:
                            self.driver.execute_script("arguments[0].click();", verify_button)
                            self.logger.info("✅ Clicked submit/verify button (JS)")
                        except Exception as e:
                            self.logger.warning(f"Failed to click button: {str(e)}")
                    sleep(2)
                    return True
                else:
                    # Try pressing Enter on the last filled element
                    if last_filled_element:
                        try:
                            self.logger.info("Submit button not found, pressing Enter on OTP field...")
                            last_filled_element.send_keys(Keys.ENTER)
                            self.logger.info("✅ Pressed Enter on OTP field")
                            sleep(2)
                            return True
                        except Exception as e:
                            self.logger.warning(f"Failed to press Enter: {str(e)}")
                    
                    # Last resort: try to find any submit button on the page
                    self.logger.info("Trying to find submit button by searching all buttons...")
                    try:
                        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in all_buttons:
                            try:
                                btn_text = btn.text.lower()
                                btn_type = btn.get_attribute("type")
                                if (btn.is_displayed() and btn.is_enabled() and 
                                    (btn_type == "submit" or "submit" in btn_text or "verify" in btn_text or "confirm" in btn_text)):
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                    sleep(0.3)
                                    btn.click()
                                    self.logger.info(f"✅ Clicked submit button: {btn_text[:30]}")
                                    sleep(2)
                                    return True
                            except:
                                continue
                    except Exception as e:
                        self.logger.warning(f"Failed to find submit button: {str(e)}")
                    
                    self.logger.warning("⚠️ Could not find or click submit button, but OTP was filled")
                    return True  # Return True anyway since OTP was filled
                    
            except Exception as e:
                self.logger.error(f"Failed to fill OTP: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in OTP verification: {str(e)}")
            return False
    
    def _verify_submission(self, original_url: str, otp_handled: bool = False) -> bool:
        """Verify that the form was actually submitted successfully"""
        self.logger.info("Verifying form submission...")
        
        if otp_handled:
            self.logger.info("OTP was handled - using more lenient verification criteria")
        
        # Check if OTP field is still present (form waiting for OTP)
        otp_element = self.helper.find_element_by_multiple_selectors(
            [GreenhouseSelectors.OTP_INPUT],
            silent=True,
            timeout=2
        )
        
        if otp_element and otp_element.is_displayed():
            self.logger.warning("⚠️ OTP field is still visible - form may be waiting for OTP")
            # If OTP handling failed, this is an error
            if not self.gmail_otp_reader:
                self.logger.error("❌ OTP required but Gmail OTP reader is not enabled!")
                self.logger.error("Please enable Gmail OTP: GreenhouseAutomation(enable_gmail_otp=True)")
                return False
            # If OTP reader exists but OTP field is still there, OTP might not have been filled correctly
            self.logger.warning("OTP field still present after OTP handling - checking if OTP was filled...")
            try:
                otp_value = otp_element.get_attribute("value") or ""
                if not otp_value:
                    self.logger.error("❌ OTP field is empty - OTP was not filled correctly")
                    return False
                else:
                    self.logger.info(f"OTP field has value: {otp_value[:2]}** (waiting for verification to complete...)")
                    # Wait a bit more for verification
                    sleep(3)
            except:
                pass
        
        # Wait for page to process submission
        sleep(3)
        
        try:
            current_url = self.driver.current_url
            
            # Check if URL changed (indicates navigation to success page)
            if current_url != original_url:
                self.logger.info(f"URL changed from {original_url[:50]}... to {current_url[:50]}...")
                # Check for success indicators in new URL
                if any(indicator in current_url.lower() for indicator in ['success', 'thank', 'confirm', 'complete', 'submitted']):
                    self.logger.success("Form submitted successfully (URL indicates success)")
                    return True
            
            # Check for success messages on the page
            success_indicators = [
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'thank you')]",
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'application received')]",
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'successfully submitted')]",
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submitted successfully')]",
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'application complete')]",
                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'we received your application')]",
                "//*[contains(@class, 'success')]",
                "//*[contains(@class, 'thank-you')]",
                "//*[contains(@id, 'success')]"
            ]
            
            for indicator in success_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.lower()
                            if any(word in text for word in ['thank', 'success', 'received', 'submitted', 'complete']):
                                self.logger.success(f"Form submitted successfully (found success message: {elem.text[:50]}...)")
                                return True
                except:
                    continue
            
            # Check for error messages (validation errors)
            error_indicators = [
                "//*[contains(@class, 'error')]",
                "//*[contains(@class, 'validation')]",
                "//*[contains(@class, 'required')]",
                "//*[contains(text(), 'required')]",
                "//*[contains(text(), 'please')]",
                "//*[contains(text(), 'invalid')]",
                "//*[contains(@role, 'alert')]"
            ]
            
            for indicator in error_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.lower()
                            # Check if it's actually an error (not just a class name)
                            if text and any(word in text for word in ['error', 'required', 'invalid', 'please', 'missing']):
                                self.logger.warning(f"Found validation error: {elem.text[:100]}")
                                return False
                except:
                    continue
            
            # Check if submit button still exists (form not submitted)
            submit_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]"
            ]
            
            for selector in submit_button_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            self.logger.warning("Submit button still visible and enabled - form may not have been submitted")
                            return False
                except:
                    continue
            
            # Check if form fields are still present and editable (form not submitted)
            try:
                form_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], textarea")
                if form_inputs:
                    # If we still have many form inputs visible, form might not be submitted
                    visible_inputs = [inp for inp in form_inputs if inp.is_displayed()]
                    if len(visible_inputs) > 5:  # If more than 5 visible inputs, form likely still present
                        self.logger.warning(f"Form still appears to be present ({len(visible_inputs)} visible inputs)")
                        return False
            except:
                pass
            
            # If we can't determine, wait a bit more and check URL again
            sleep(2)
            final_url = self.driver.current_url
            if final_url != original_url:
                self.logger.success("Form submitted successfully (URL changed after wait)")
                return True
            
            # If OTP was handled, be more lenient - OTP flow might have completed even if we can't verify
            if otp_handled:
                # Check if OTP field is gone (indicating OTP was processed)
                otp_element = self.helper.find_element_by_multiple_selectors(
                    [GreenhouseSelectors.OTP_INPUT],
                    silent=True,
                    timeout=1
                )
                if not otp_element or not otp_element.is_displayed():
                    self.logger.info("OTP field is no longer visible - OTP was likely processed successfully")
                    self.logger.success("Form submission likely successful (OTP processed, but couldn't verify final state)")
                    return True
                else:
                    self.logger.warning("OTP field still visible - OTP may not have been processed correctly")
            
            # If we get here, we're not sure - log warning
            self.logger.warning("Could not definitively verify submission. Form may or may not have been submitted.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying submission: {str(e)}")
            return False
    
    def _submit_form(self) -> bool:
        """Submit the application form and verify submission"""
        self.logger.info("Looking for submit button...")
        
        # Store original URL for verification
        original_url = self.driver.current_url
        
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
        
        submit_clicked = False
        
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
                        self.logger.info(f"Clicked submit button using selector: {selector}")
                        submit_clicked = True
                        break
                    # If not enabled, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    self.logger.info(f"Clicked submit button (JS) using selector: {selector}")
                    submit_clicked = True
                    break
                except Exception as e:
                    self.logger.info(f"Failed to click with selector {selector}: {str(e)}")
                    continue
        
        if not submit_clicked:
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
                            self.logger.info(f"Clicked submit button using XPath: {xpath[:50]}...")
                            submit_clicked = True
                            break
                        # Try JavaScript click
                        self.driver.execute_script("arguments[0].click();", element)
                        self.logger.info(f"Clicked submit button (JS) using XPath: {xpath[:50]}...")
                        submit_clicked = True
                        break
                    except Exception as e:
                        self.logger.info(f"Failed to click with XPath {xpath[:50]}: {str(e)}")
                        continue
        
        if not submit_clicked:
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
                                self.logger.info(f"Clicked submit button by text/type: {text[:30]}")
                                submit_clicked = True
                                break
                    except:
                        continue
            except Exception as e:
                self.logger.error(f"Error in last resort button search: {str(e)}")
        
        if not submit_clicked:
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
        
        # Wait a bit for page to respond after clicking submit
        sleep(2)
        
        # Check if OTP is required and handle it
        otp_handled = False
        otp_required = self._handle_otp_verification()
        if otp_required:
            self.logger.info("✅ OTP was filled and verified")
            otp_handled = True
            # Wait for form to process OTP and complete submission
            self.logger.info("Waiting for form to process OTP and complete submission...")
            sleep(5)  # Give more time for OTP verification and final submission
        
        # Verify that the form was actually submitted
        # If OTP was handled, give it more time and be more lenient in verification
        if otp_handled:
            self.logger.info("Verifying submission after OTP verification...")
            # Wait a bit more for final submission to complete
            sleep(3)
        
        # Pass otp_handled flag to verification for more lenient checking
        return self._verify_submission(original_url, otp_handled=otp_handled)
    
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
        
        # Disability status (with smart pattern matching)
        if application_input.disability_status:
            disability_input = application_input.disability_status.strip().lower()
            
            # Determine which option to select based on input
            # Options are:
            # 1. "Yes, I have a disability, or have had one in the past"
            # 2. "No, I do not have a disability and have not had one in the past"
            # 3. "I do not want to answer"
            
            if "yes" in disability_input:
                # Select first option that contains "yes" (Yes option)
                self._fill_dropdown_by_pattern(
                    selectors=[GreenhouseSelectors.DISABILITY_STATUS],
                    pattern="yes",
                    option_index=0,  # First matching option
                    field_name="Disability Status",
                    silent=True
                )
            elif "no" in disability_input:
                # Select first option that contains "no" (No option)
                self._fill_dropdown_by_pattern(
                    selectors=[GreenhouseSelectors.DISABILITY_STATUS],
                    pattern="no",
                    option_index=0,  # First matching option
                    field_name="Disability Status",
                    silent=True
                )
            else:
                # Select last option (I do not want to answer)
                self._fill_dropdown_by_pattern(
                    selectors=[GreenhouseSelectors.DISABILITY_STATUS],
                    pattern="",
                    option_index=-1,  # Last option
                    field_name="Disability Status",
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
    
    def _fill_dropdown_by_pattern(self, selectors: list, pattern: str, option_index: int, field_name: str, required: bool = False, silent: bool = False) -> bool:
        """
        Fill dropdown by selecting option by index (0-based, -1 for last)
        If pattern is provided, it will try to match options containing the pattern first
        """
        element = self.helper.find_element_by_multiple_selectors(selectors, silent=silent)
        if not element:
            if required:
                self.logger.error(f"Required dropdown not found: {field_name}")
            elif not silent:
                self.logger.info(f"Optional dropdown not found (skipping): {field_name}")
            return not required
        
        try:
            # Check if it's a React Select component
            is_react_select = False
            try:
                parent = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'select__control')]")
                if parent:
                    is_react_select = True
            except:
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
                        control_div = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'select-shell')]//div[contains(@class, 'select__control')]")
                    
                    if control_div:
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", control_div)
                        sleep(0.3)
                        
                        # Click the control to open dropdown
                        try:
                            control_div.click()
                        except:
                            try:
                                toggle_btn = control_div.find_element(By.CSS_SELECTOR, "button.icon-button, button[aria-label*='Toggle']")
                                toggle_btn.click()
                            except:
                                pass
                        sleep(0.8)  # Wait for menu to appear
                        
                        # Get all available options
                        all_option_selectors = [
                            "//div[contains(@class, 'select__menu')]//div[@role='option']",
                            "//div[@role='listbox']//div[@role='option']",
                            "//div[contains(@class, 'select__menu')]//div[contains(@class, 'option')]"
                        ]
                        
                        all_options = []
                        for selector in all_option_selectors:
                            try:
                                options = self.driver.find_elements(By.XPATH, selector)
                                visible_options = [opt for opt in options if opt.is_displayed()]
                                if visible_options:
                                    all_options = visible_options
                                    break
                            except:
                                continue
                        
                        if not all_options:
                            self.logger.warning(f"No options found in {field_name} dropdown")
                            return False
                        
                        selected_option = None
                        option_text = ""
                        
                        # If pattern is provided, try to find matching options first
                        if pattern:
                            pattern_lower = pattern.lower()
                            matching_options = []
                            for opt in all_options:
                                try:
                                    opt_text = opt.text.strip().lower()
                                    if pattern_lower in opt_text:
                                        matching_options.append((opt, opt.text.strip()))
                                except:
                                    continue
                            
                            if matching_options:
                                # Use the option at the specified index from matching options
                                if option_index == -1:
                                    selected_option, option_text = matching_options[-1]
                                elif 0 <= option_index < len(matching_options):
                                    selected_option, option_text = matching_options[option_index]
                                else:
                                    selected_option, option_text = matching_options[0]
                            else:
                                # No pattern match, use index from all options
                                if option_index == -1:
                                    selected_option = all_options[-1]
                                    option_text = all_options[-1].text.strip()
                                elif 0 <= option_index < len(all_options):
                                    selected_option = all_options[option_index]
                                    option_text = all_options[option_index].text.strip()
                                else:
                                    selected_option = all_options[0]
                                    option_text = all_options[0].text.strip()
                        else:
                            # No pattern, use index directly
                            if option_index == -1:
                                selected_option = all_options[-1]
                                option_text = all_options[-1].text.strip()
                            elif 0 <= option_index < len(all_options):
                                selected_option = all_options[option_index]
                                option_text = all_options[option_index].text.strip()
                            else:
                                selected_option = all_options[0]
                                option_text = all_options[0].text.strip()
                        
                        # Click the selected option
                        if selected_option:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selected_option)
                            sleep(0.2)
                            try:
                                selected_option.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", selected_option)
                            sleep(0.5)
                            self.logger.info(f"Selected option '{option_text}' (index {option_index}) in {field_name}")
                            return True
                        
                        return False
                except Exception as e:
                    if not silent:
                        self.logger.error(f"Failed to select by pattern in {field_name}", e)
                    return False
            else:
                # For native select, use standard dropdown filling
                return self._fill_dropdown(selectors, pattern if pattern else "other", field_name, required, silent)
        except Exception as e:
            if not silent:
                self.logger.error(f"Error in pattern-based dropdown selection for {field_name}", e)
            return False
    
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
    
    def _click_locate_me_button(self) -> bool:
        """Click the 'Locate me' button as fallback for location city"""
        try:
            # Try multiple selectors for the "Locate me" button
            locate_me_selectors = [
                'button[class*="locate"]',
                'button:contains("Locate me")',
                'button:contains("Locate Me")',
                'button[aria-label*="Locate"]',
                'a[class*="locate"]',
                'button.btn--tertiary',
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'locate me')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'locate')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'locate me')]"
            ]
            
            for selector in locate_me_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.helper.safe_find_element(By.XPATH, selector, timeout=2, silent=True)
                    else:
                        element = self.helper.safe_find_element_by_css(selector, timeout=2, silent=True)
                    
                    if element and element.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        sleep(0.3)
                        try:
                            element.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", element)
                        sleep(1)  # Wait for location to be detected
                        self.logger.info("Clicked 'Locate me' button")
                        return True
                except:
                    continue
            
            self.logger.warning("Could not find 'Locate me' button")
            return False
        except Exception as e:
            self.logger.error(f"Error clicking 'Locate me' button: {str(e)}")
            return False
    
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


def run_automation(input_data: dict, enable_gmail_otp: bool = False, gmail_credentials_file: str = 'credentials.json', gmail_token_file: str = 'token.json', enable_gpt: bool = True, gpt_model: str = 'gpt-4', openai_api_key: str = None) -> dict:
    """
    Convenience function to run automation from dict input
    
    Args:
        input_data: Dictionary containing application form data
        enable_gmail_otp: Enable Gmail API for automatic OTP retrieval
        gmail_credentials_file: Path to Gmail OAuth2 credentials JSON file
        gmail_token_file: Path to store/load Gmail OAuth2 token
        enable_gpt: Enable GPT for filling missing fields (default: True)
        gpt_model: GPT model to use (default: 'gpt-4')
        openai_api_key: OpenAI API key (optional, uses env var if not provided)
    """
    application_input = GreenhouseApplicationInput.from_dict(input_data)
    automation = GreenhouseAutomation(
        enable_gmail_otp=enable_gmail_otp,
        gmail_credentials_file=gmail_credentials_file,
        gmail_token_file=gmail_token_file,
        enable_gpt=enable_gpt,
        gpt_model=gpt_model,
        openai_api_key=openai_api_key
    )
    result = automation.run(application_input)
    return result.to_dict()

