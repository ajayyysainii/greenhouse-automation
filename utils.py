import time
import traceback
import os
from typing import Callable, Optional, Any, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Logger:
    """Simple logger for consistent output"""
    
    @staticmethod
    def info(message: str):
        """Log info message"""
        print(f"[INFO] {message}")
    
    @staticmethod
    def error(message: str, error: Optional[Exception] = None):
        """Log error message"""
        print(f"[ERROR] {message}")
        if error:
            traceback.print_exc()
    
    @staticmethod
    def success(message: str):
        """Log success message"""
        print(f"[SUCCESS] {message}")


class WebDriverHelper:
    """Helper methods for WebDriver operations"""
    
    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait
        self.logger = Logger()
    
    def safe_find_element(self, by: By, value: str, timeout: Optional[int] = None, silent: bool = False) -> Optional[WebElement]:
        """Safely find element with optional custom timeout"""
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(EC.presence_of_element_located((by, value)))
            return self.wait.until(EC.presence_of_element_located((by, value)))
        except Exception as e:
            if not silent:
                self.logger.error(f"Element not found: {value}", e)
            return None
    
    def safe_find_element_by_css(self, selector: str, timeout: Optional[int] = None, silent: bool = False) -> Optional[WebElement]:
        """Safely find element by CSS selector"""
        return self.safe_find_element(By.CSS_SELECTOR, selector, timeout, silent)
    
    def safe_find_element_by_xpath(self, xpath: str, timeout: Optional[int] = None, silent: bool = False) -> Optional[WebElement]:
        """Safely find element by XPath"""
        return self.safe_find_element(By.XPATH, xpath, timeout, silent)
    
    def find_element_by_multiple_selectors(self, selectors: List[str], timeout: Optional[int] = None, silent: bool = False) -> Optional[WebElement]:
        """Try multiple CSS selectors to find an element"""
        for selector in selectors:
            element = self.safe_find_element_by_css(selector, timeout=2, silent=silent)
            if element:
                return element
        return None
    
    def safe_click(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """Safely click element"""
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
                element = wait.until(EC.element_to_be_clickable((by, value)))
            else:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Failed to click element: {value}", e)
            return False
    
    def safe_click_by_css(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Safely click element by CSS selector"""
        return self.safe_click(By.CSS_SELECTOR, selector, timeout)
    
    def safe_send_keys(self, by: By, value: str, text: str, clear_first: bool = True) -> bool:
        """Safely send keys to element"""
        try:
            element = self.safe_find_element(by, value)
            if element:
                if clear_first:
                    element.clear()
                element.send_keys(text)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to send keys to element: {value}", e)
            return False
    
    def safe_send_keys_by_css(self, selector: str, text: str, clear_first: bool = True) -> bool:
        """Safely send keys to element by CSS selector"""
        return self.safe_send_keys(By.CSS_SELECTOR, selector, text, clear_first)
    
    def safe_upload_file(self, selector: str, file_path: str, timeout: Optional[int] = None) -> bool:
        """Safely upload a file"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Try to find file input by multiple methods
            element = self.find_element_by_multiple_selectors([selector], timeout)
            if not element:
                # Try finding by input type="file"
                element = self.safe_find_element_by_css('input[type="file"]', timeout)
            
            if element:
                element.send_keys(os.path.abspath(file_path))
                self.logger.info(f"Uploaded file: {file_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to upload file: {file_path}", e)
            return False
    
    def element_exists(self, by: By, value: str) -> bool:
        """Check if element exists"""
        try:
            elements = self.driver.find_elements(by, value)
            return len(elements) > 0
        except:
            return False
    
    def wait_for_condition(self, condition: Callable, timeout: int = 10) -> Any:
        """Wait for custom condition"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(condition)
        except Exception as e:
            self.logger.error(f"Condition not met within {timeout}s", e)
            return None


def sleep(seconds: float):
    """Sleep wrapper for consistency"""
    time.sleep(seconds)


def take_screenshot(driver: WebDriver, filename: str = "screenshot.png"):
    """Take a screenshot for debugging"""
    try:
        driver.save_screenshot(filename)
        return True
    except Exception as e:
        Logger().error(f"Failed to take screenshot: {str(e)}")
        return False

