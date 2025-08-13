# common/browser_utils.py
# -*- coding: utf-8 -*-
import os
import sys
import atexit
import shutil
import tempfile

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# .env varsa yükle, yoksa sorun etmeyelim
load_dotenv(override=False)

# İstersen burayı kendi default’unla değiştir
DEFAULT_BASE_URL = "https://operator-frontend-v2-641161620205.europe-west1.run.app/"

def _truthy(env_val: str | None) -> bool:
    if not env_val:
        return False
    return str(env_val).strip().lower() in {"1", "true", "yes", "on"}

def open_browser():
    """
    - HEADLESS = 1/true ise headless-new
    - Her koşumda benzersiz Chrome profili (--user-data-dir) açılır (CI hatası: 'user data dir in use' çözümü)
    - .env/ENV yoksa DEFAULT_BASE_URL kullanılır (hata yerine uyarı mantığı)
    - Önce Selenium Manager ile dener; olmazsa webdriver_manager fallback
    """
    base_url = (os.getenv("BASE_URL") or DEFAULT_BASE_URL).strip()
    if not base_url:
        print("UYARI: BASE_URL boş; DEFAULT_BASE_URL kullanılacak.", file=sys.stderr)
        base_url = DEFAULT_BASE_URL

    headless = _truthy(os.getenv("HEADLESS"))
    timeout = int(os.getenv("DEFAULT_TIMEOUT", "25"))

    opts = Options()

    if headless:
        # Headless CI
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1366,900")
        opts.add_argument("--hide-scrollbars")
        # WebGL/canvas için daha stabil
        opts.add_argument("--use-gl=swiftshader")
        opts.add_argument("--disable-gpu")
    else:
        # Lokal çalıştırma
        opts.add_argument("--start-maximized")
        opts.add_argument("--window-size=1440,900")

    # Her koşum için benzersiz profil → profil çakışması çözüldü
    tmp_profile = tempfile.mkdtemp(prefix="chrome-profile-")
    atexit.register(lambda: shutil.rmtree(tmp_profile, ignore_errors=True))
    opts.add_argument(f"--user-data-dir={tmp_profile}")
    opts.add_argument(f"--data-path={os.path.join(tmp_profile, 'data-path')}")
    opts.add_argument(f"--disk-cache-dir={os.path.join(tmp_profile, 'cache')}")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--password-store=basic")
    opts.add_argument("--use-mock-keychain")

    # Linux runner stabilite bayrakları
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--mute-audio")
    opts.add_argument("--remote-debugging-port=0")
    opts.add_argument("--lang=en-US,en")

    # --- Driver oluşturma (önce Selenium Manager, sonra fallback) ---
    driver = None
    try:
        # Selenium 4.6+ → otomatik chromedriver yönetimi
        driver = webdriver.Chrome(options=opts)
    except Exception as sm_err:
        # Fallback: webdriver_manager (opsiyonel)
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
        except Exception as wdm_err:
            print("Chrome driver başlatılamadı.\n"
                  f"Selenium Manager hatası: {sm_err}\n"
                  f"webdriver_manager hatası: {wdm_err}", file=sys.stderr)
            raise

    # Siteye git ve WebDriverWait döndür
    driver.get(base_url)
    wait = WebDriverWait(driver, timeout)
    return driver, wait
