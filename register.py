# register.py
import os
import time
import random
import secrets
import string
import logging
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from common.browser_utils import open_browser
from common.user_data import save_user_data
from locators.register_locators import RegisterLocators as L

# ---------- Logging ----------
LOG_FMT = "%(asctime)s | %(levelname)-7s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("register")

# ---------- Helpers ----------
def human_pause(a=0.25, b=0.6):
    """İnsan benzeri küçük beklemeler."""
    time.sleep(random.uniform(a, b))

def get_wait(driver, timeout=None):
    from selenium.webdriver.support.ui import WebDriverWait
    t = timeout or int(os.getenv("DEFAULT_TIMEOUT", "10"))
    return WebDriverWait(driver, t)

def wait_until_clickable(driver, locator, desc, timeout=None):
    wait = get_wait(driver, timeout)
    log.info(f"⏳ Bekleniyor (clickable): {desc}")
    return wait.until(EC.element_to_be_clickable(locator))

def wait_until_visible(driver, locator, desc, timeout=None):
    wait = get_wait(driver, timeout)
    log.info(f"⏳ Bekleniyor (visible): {desc}")
    return wait.until(EC.visibility_of_element_located(locator))

def type_slow(driver, locator, text, a=0.03, b=0.09, clear=True, desc=""):
    """Karakter karakter yazar; gerçek kullanıcıya yakın."""
    el = wait_until_clickable(driver, locator, desc or "input")
    if clear:
        el.clear()
        human_pause(0.1, 0.2)
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(a, b))
    return el

def random_email():
    rnd = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    return f"test_{int(time.time())}_{rnd}@example.com"

def random_username():
    rnd = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(7))
    return f"user_{rnd}"

def random_password():
    alpha = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alpha) for _ in range(14))

# ---------- Main flow ----------
def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver, _ = open_browser()   # wait objesine ihtiyac yok; kendi wait helper'larımızı kullanıyoruz
    step = 0

    try:
        step += 1
        log.info(f"[STEP {step}] Ana sayfa yüklendi. Kayıt akışı başlıyor. run_id={run_id}")
        human_pause()

        # 1) Kayıt Ol butonuna tıkla
        step += 1
        log.info(f"[STEP {step}] 'Kayıt Ol' butonuna tıklanıyor.")
        btn_register = wait_until_clickable(driver, L.OPEN_REGISTER_BUTTON, "Kayıt Ol butonu")
        human_pause(0.2, 0.5)
        btn_register.click()

        # 2) Form alanlarının görünmesini bekle
        step += 1
        log.info(f"[STEP {step}] Kayıt formu alanları bekleniyor.")
        wait_until_visible(driver, L.EMAIL_INPUT, "E-posta alanı")
        wait_until_visible(driver, L.USERNAME_INPUT, "Kullanıcı adı alanı")
        wait_until_visible(driver, L.PASSWORD_INPUT, "Parola alanı")
        human_pause()

        # 3) Rastgele veriler üret
        email = random_email()
        username = random_username()
        password = random_password()
        log.info(f"[DATA] email={email} username={username} (şifre loglanmaz)")

        # 4) Formu doldur (insan gibi yaz)
        step += 1
        log.info(f"[STEP {step}] Form dolduruluyor.")
        type_slow(driver, L.EMAIL_INPUT, email, desc="E-posta")
        human_pause()
        type_slow(driver, L.USERNAME_INPUT, username, desc="Kullanıcı adı")
        human_pause()
        type_slow(driver, L.PASSWORD_INPUT, password, desc="Parola")
        human_pause(0.2, 0.5)

        # 5) Gönder
        step += 1
        log.info(f"[STEP {step}] 'Kayıt Ol' formu gönderiliyor.")
        submit_el = wait_until_clickable(driver, L.SUBMIT_BUTTON, "Kayıt Ol (submit)")
        human_pause(0.1, 0.3)
        submit_el.click()

        # 6) Modal kapanışı / ana ekrana dönüş (logout butonu görünmeli)
        step += 1
        log.info(f"[STEP {step}] Kayıt sonrası ana ekran doğrulaması.")
        # Modal kapandı sayılırsa header’daki logout butonu clickable olur
        logout_btn = wait_until_clickable(driver, L.LOGOUT_BUTTON, "Logout butonu", timeout=20)
        human_pause(0.3, 0.8)
        logout_btn.click()
        log.info("✅ Kayıt ve çıkış tamamlandı.")

        # 7) Test verisini kaydet
        save_user_data(email, username, password)

    except TimeoutException as e:
        log.error(f"⛔ Zaman aşımı hatası: {e}")
        raise
    except Exception as e:
        log.error(f"⛔ Beklenmeyen hata: {e}")
        raise
    finally:
        # Headless pipeline dostu: sadece tarayıcıyı kapat
        driver.quit()

if __name__ == "__main__":
    main()
