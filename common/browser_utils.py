# common/browser_utils.py
import os, sys
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

def open_browser():
    base_url = os.getenv("BASE_URL")
    if not base_url:
        print("HATA: BASE_URL .env dosyasında boş.", file=sys.stderr)
        sys.exit(1)

    headless = os.getenv("HEADLESS", "false").lower() == "true"
    timeout = int(os.getenv("DEFAULT_TIMEOUT", "10"))

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")

    # 🔧 ÖNEMLİ: Service ile kullan
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    driver.get(base_url)
    wait = WebDriverWait(driver, timeout)
    return driver, wait
