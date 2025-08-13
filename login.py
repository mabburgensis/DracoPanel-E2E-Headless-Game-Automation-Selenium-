import os
import time
import random
import logging
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from common.browser_utils import open_browser
from common.user_data import load_user_data
from locators.login_locators import LoginLocators as L

# -------- Logging (English) --------
LOG_FMT = "%(asctime)s | %(levelname)-7s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("login")

# -------- Helpers --------
def human_pause(a=0.20, b=0.45):
    time.sleep(random.uniform(a, b))

def get_wait(driver, timeout=None):
    from selenium.webdriver.support.ui import WebDriverWait
    t = timeout or int(os.getenv("DEFAULT_TIMEOUT", "10"))
    return WebDriverWait(driver, t)

def wait_clickable(driver, locator, desc, timeout=None):
    log.info(f"⏳ wait clickable: {desc}")
    return get_wait(driver, timeout).until(EC.element_to_be_clickable(locator))

def wait_visible(driver, locator, desc, timeout=None):
    log.info(f"⏳ wait visible: {desc}")
    return get_wait(driver, timeout).until(EC.visibility_of_element_located(locator))

def is_present(driver, locator, timeout=2):
    try:
        get_wait(driver, timeout).until(EC.presence_of_element_located(locator))
        return True
    except TimeoutException:
        return False

def is_clickable(driver, locator, timeout=2):
    try:
        get_wait(driver, timeout).until(EC.element_to_be_clickable(locator))
        return True
    except TimeoutException:
        return False

def type_slow(driver, locator, text, a=0.03, b=0.08, clear=True, desc="input"):
    el = wait_clickable(driver, locator, desc)
    if clear:
        el.clear()
        human_pause(0.08, 0.15)
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(a, b))
    return el

def clear_field(driver, locator):
    el = wait_clickable(driver, locator, "clear field")
    el.clear()
    human_pause(0.05, 0.12)

# -------- Scenarios --------
def open_login_modal(driver):
    log.info("[STEP] Open login modal")
    btn = wait_clickable(driver, L.LOGIN_BUTTON_HEADER, "header login button")
    human_pause(0.2, 0.4)
    btn.click()
    # modal inputs must be visible
    wait_visible(driver, L.USERNAME_INPUT, "username input")
    wait_visible(driver, L.PASSWORD_INPUT, "password input")
    human_pause()

def assert_failed_login(driver, reason: str):
    """
    Failure heuristics:
      - Logout button must NOT be clickable
      - Login modal should still be present (form root visible)
    """
    modal_still_open = is_present(driver, L.MODAL_FORM_ROOT, timeout=3)
    logout_clickable  = is_clickable(driver, L.LOGOUT_BUTTON, timeout=3)

    if not logout_clickable and modal_still_open:
        log.info(f"✅ Expected failure confirmed: {reason}")
    else:
        raise AssertionError(f"❌ Expected failure did not occur: {reason} "
                             f"(logout_clickable={logout_clickable}, modal_open={modal_still_open})")

def do_success_login(driver, username, password):
    log.info("[STEP] Perform successful login")
    type_slow(driver, L.USERNAME_INPUT, username, desc="username")
    human_pause()
    type_slow(driver, L.PASSWORD_INPUT, password, desc="password")
    human_pause(0.2, 0.4)
    wait_clickable(driver, L.LOGIN_SUBMIT_BUTTON, "submit login").click()

    # success: logout appears clickable
    wait_clickable(driver, L.LOGOUT_BUTTON, "logout button", timeout=20)
    log.info("🟢 Success login verified")

def do_logout(driver):
    log.info("[STEP] Logout")
    btn = wait_clickable(driver, L.LOGOUT_BUTTON, "logout button", timeout=20)
    human_pause(0.25, 0.5)
    btn.click()
    # header login button should be back
    wait_clickable(driver, L.LOGIN_BUTTON_HEADER, "header login button after logout", timeout=20)
    log.info("🔄 Logout completed")

# -------- Main --------
def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver, _ = open_browser()
    log.info(f"=== LOGIN TEST START | run_id={run_id} ===")

    try:
        # Load previously registered test user
        try:
            user = load_user_data()
            valid_username = user["username"]
            valid_password = user["password"]
            log.info(f"[DATA] username={valid_username} (password hidden)")
        except FileNotFoundError:
            log.error("test_user_data.json not found. Run register.py first.")
            raise

        # Open modal once and reuse it across scenarios
        open_login_modal(driver)

        # --- Negative #1: Empty fields ---
        log.info("[CASE N1] Submit with empty fields")
        wait_clickable(driver, L.LOGIN_SUBMIT_BUTTON, "submit login").click()
        assert_failed_login(driver, "empty username & password")

        # --- Negative #2: Invalid username ---
        log.info("[CASE N2] Invalid username + valid password")
        type_slow(driver, L.USERNAME_INPUT, "invalid_user", desc="username")
        type_slow(driver, L.PASSWORD_INPUT, valid_password, desc="password")
        wait_clickable(driver, L.LOGIN_SUBMIT_BUTTON, "submit login").click()
        assert_failed_login(driver, "invalid username")
        # clear for next case
        clear_field(driver, L.USERNAME_INPUT)
        clear_field(driver, L.PASSWORD_INPUT)

        # --- Negative #3: Valid username + invalid password ---
        log.info("[CASE N3] Valid username + invalid password")
        type_slow(driver, L.USERNAME_INPUT, valid_username, desc="username")
        type_slow(driver, L.PASSWORD_INPUT, "WrongPassword123!", desc="password")
        wait_clickable(driver, L.LOGIN_SUBMIT_BUTTON, "submit login").click()
        assert_failed_login(driver, "invalid password")
        # prepare for success
        clear_field(driver, L.USERNAME_INPUT)
        clear_field(driver, L.PASSWORD_INPUT)

        # --- Positive: Successful login ---
        log.info("[CASE P1] Successful login")
        do_success_login(driver, valid_username, valid_password)

        # --- Final: Logout ---
        do_logout(driver)

        log.info("✅ TEST COMPLETED")

    except TimeoutException as e:
        log.error(f"Timeout: {e}")
        raise
    except AssertionError as e:
        log.error(str(e))
        raise
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
