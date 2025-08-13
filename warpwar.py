import os, json, time, random, logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# --- locator sınıfları ---
from locators.login_locators import LoginLocators as LL
from locators.warpwar_locators import WarpWarLocators as L

# ===== Logging =====
LOG_FMT = "%(asctime)s | %(levelname)-7s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("warpwar")

# ===== Config =====
BASE_URL = os.getenv("BASE_URL", "https://operator-frontend-v2-641161620205.europe-west1.run.app/")
DEFAULT_TIMEOUT   = int(os.getenv("DEFAULT_TIMEOUT", "25"))
GAME_LOAD_TIMEOUT = int(os.getenv("GAME_LOAD_TIMEOUT", "90"))

# ——— Keno/Diamonds ile aynı beklemeler ———
BET_RESOLVE_WAIT     = (0.8, 1.0)     # SPACE sonrası kısa animasyon
PRE_BET_DELAY_SEC    = 1.0            # her bet öncesi tam 1 sn
BETWEEN_ROUNDS_SEC   = 1.0            # eller arası tam 1 sn

# Coinflip pick gecikmeleri (mevcut ayarları koruduk)
BET_BETWEEN_PICKS    = (1.1, 1.5)     # Q seçimleri arası
PICK_SLEEP_1         = (0.35, 0.55)   # 1. pick sonrası min gecikme
PICK_SLEEP_2         = (0.35, 0.60)   # 2. pick sonrası min gecikme
AFTER_CASHOUT_WAIT   = (2.0, 3.0)     # W sonrası kısa bekleme

# Login akışı beklemeleri (Keno/Diamonds ile aynı)
LOGIN_PRE_CLICK_SEC  = 3.0            # Login butonuna basmadan önce
LOGIN_POST_CLICK_SEC = 3.0            # Login modal açıldıktan sonra
LOGIN_PER_FIELD_SEC  = 2.0            # username, password ve submit sonrası

def nap(a=0.6, b=1.2): time.sleep(random.uniform(a, b))
def long_nap(a=1.4, b=2.4): time.sleep(random.uniform(a, b))
def tiny_nap(a=0.18, b=0.35): time.sleep(random.uniform(a, b))

# ===== test_user_data.json =====
def load_test_user(fp="test_user_data.json"):
    if not os.path.exists(fp): raise FileNotFoundError(f"{fp} bulunamadı")
    with open(fp, "r", encoding="utf-8") as f: data = json.load(f)
    username = (data.get("username") or data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password: raise ValueError("username/email ve password gerekli")
    return username, password

# ===== Driver =====
def make_driver():
    opts = Options()
    if os.getenv("HEADLESS", "0") in ("1", "true", "True"):
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1366,900")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--use-gl=swiftshader")
        opts.add_argument("--disable-gpu")
    else:
        opts.add_argument("--start-maximized")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--mute-audio")
    opts.add_argument("--lang=en-US,en")
    driver = webdriver.Chrome(service=Service(), options=opts)
    return driver

def wait_clickable(driver, locator, desc, timeout=DEFAULT_TIMEOUT):
    log.info(f"⏳ wait clickable: {desc}")
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))

def wait_visible(driver, locator, desc, timeout=DEFAULT_TIMEOUT):
    log.info(f"⏳ wait visible: {desc}")
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))

def send_hotkey(driver, key):
    ActionChains(driver).pause(random.uniform(0.06, 0.14)).send_keys(key).perform()
    tiny_nap()

# ===== In-page hook (fetch + XHR) =====
HOOK_JS = r"""
(() => {
  try {
    if (window.__PLAY_HOOK_INSTALLED__) return;
    window.__PLAY_HOOK_INSTALLED__ = true;
    window.__PLAY_RESULTS = [];  // {t, url, payload, result, session_id, index, action}

    const PLAY_HINT = "/v1/play";
    function norm(v) {
      if (!v) return null;
      v = String(v).toLowerCase();
      if (v === "in_progress" || v === "inprogress") return "inprogress";
      if (v === "loss") return "lose";
      return null;
    }
    function push(url, payload) {
      try {
        const d = (payload && payload.data) || {};
        window.__PLAY_RESULTS.push({
          t: Date.now(),
          url, payload,
          result: norm(d.result),
          session_id: d.session_id || null,
          index: typeof d.index === "number" ? d.index : null,
          action: d.action || null
        });
      } catch(e) {}
    }

    // flush helper'ları ekle
    window.__PLAY_FLUSH_ALL__ = () => { try { window.__PLAY_RESULTS.length = 0; } catch(e){} };

    // fetch hook
    const _fetch = window.fetch;
    window.fetch = async function(input, init) {
      const reqUrl = (typeof input === "string" ? input : (input && input.url)) || "";
      const p = _fetch.apply(this, arguments);
      try {
        const res = await p;
        const url = (res && res.url) || reqUrl || "";
        if (url.includes(PLAY_HINT)) {
          try {
            const text = await res.clone().text();
            try { push(url, JSON.parse(text)); } catch {}
          } catch {}
        }
        return res;
      } catch (e) { throw e; }
    };

    // XHR hook
    const XHR = window.XMLHttpRequest;
    const _open = XHR.prototype.open;
    const _send = XHR.prototype.send;
    XHR.prototype.open = function(method, url) { this.__url = url || ""; return _open.apply(this, arguments); };
    XHR.prototype.send = function() {
      this.addEventListener("load", function() {
        try {
          const url = this.__url || "";
          if (url.includes(PLAY_HINT)) {
            const text = this.responseText || "";
            try { push(url, JSON.parse(text)); } catch {}
          }
        } catch {}
      });
      return _send.apply(this, arguments);
    };
  } catch (err) { console.error("HOOK_ERR", err); }
})();
"""

class DomPlayWatcher:
    """hook kuyruğundan, verilen zamandan sonra ve (varsa) session_id eşleşmeli ilk kaydı döndürür."""
    def __init__(self, driver):
        self.driver = driver
    def install(self): self.driver.execute_script(HOOK_JS)
    def flush_all(self): self.driver.execute_script("window.__PLAY_FLUSH_ALL__ && window.__PLAY_FLUSH_ALL__();")
    def pop_next_since(self, since_ms: int, session_id: str | None):
        return self.driver.execute_script("""
            const since = arguments[0] >>> 0, sid = arguments[1] || null;
            if (!Array.isArray(window.__PLAY_RESULTS)) return null;
            for (let i = 0; i < window.__PLAY_RESULTS.length; i++) {
              const it = window.__PLAY_RESULTS[i];
              if (it.t >= since && (!sid || it.session_id === sid)) {
                window.__PLAY_RESULTS.splice(i,1);
                return it;
              }
            }
            return null;
        """, int(since_ms), session_id)
    def wait_result(self, since_ms: int, session_id: str | None, timeout: float = 12.0):
        t_end = time.time() + timeout
        while time.time() < t_end:
            item = self.pop_next_since(since_ms, session_id)
            if item: return item
            time.sleep(0.09)
        return None

# ===== Game helpers =====
def switch_to_game_iframe(driver):
    log.info("🔍 searching for game iframe (with a <canvas>)")
    t_end = time.time() + GAME_LOAD_TIMEOUT
    while time.time() < t_end:
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        for idx, fr in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(fr)
            if driver.find_elements(By.CSS_SELECTOR, "canvas"):
                log.info(f"🔁 switched into game iframe (index={idx})")
                nap(0.8, 1.2)
                return
        nap(0.8, 1.2)
    raise TimeoutException("No iframe with a <canvas> found.")

def focus_canvas_without_click(driver):
    """Canvas'ı tıklamadan odakla (orta ekrana istemsiz click yok)."""
    canvas = wait_visible(driver, L.GAME_CANVAS, "game canvas", timeout=GAME_LOAD_TIMEOUT)
    driver.execute_script("arguments[0].setAttribute('tabindex','0'); arguments[0].focus();", canvas)
    tiny_nap()
    return canvas

# ===== Utils =====
def now_ms(driver) -> int:
    return driver.execute_script("return Date.now();")

# ===== Round logic =====
def play_one_round(driver, watcher: DomPlayWatcher) -> str:
    # round başında eski kayıtları temizle
    watcher.flush_all()

    log.info("▶️  [ROUND] Place bet (SPACE)")
    time.sleep(PRE_BET_DELAY_SEC)           # Keno/Diamonds ile aynı: bet öncesi 1 sn
    t_space = now_ms(driver)
    send_hotkey(driver, Keys.SPACE)
    nap(*BET_RESOLVE_WAIT)                  # kısa animasyon

    # 1) First pick (Q)
    log.info("🎲 First pick (Q)")
    t0 = now_ms(driver)                     # tetiklemeden hemen önce zaman damgası
    send_hotkey(driver, "q")
    nap(*PICK_SLEEP_1)

    item1 = watcher.wait_result(since_ms=t0, session_id=None, timeout=12)
    r1 = (item1 or {}).get("result")
    s1 = (item1 or {}).get("session_id")
    log.info(f"🔎 First play result: {r1}")
    if r1 != "inprogress":
        log.info("🔴 First pick not inprogress → round lost")
        return "lose"

    # Q seçimleri arası doğal bekleme
    nap(*BET_BETWEEN_PICKS)

    # 2) Second pick (Q)
    log.info("🎲 Second pick (Q)")
    t1 = now_ms(driver)
    send_hotkey(driver, "q")
    nap(*PICK_SLEEP_2)

    item2 = watcher.wait_result(since_ms=t1, session_id=s1, timeout=12)
    r2 = (item2 or {}).get("result")
    log.info(f"🔎 Second play result: {r2}")

    if r2 == "inprogress":
        log.info("🟢 Two consecutive inprogress → CASHOUT via (W)")
        nap(0.5, 0.9)       # insanî küçük gecikme
        send_hotkey(driver, "w")            # sadece hotkey
        nap(*AFTER_CASHOUT_WAIT)
        return "success"

    log.info("🟠 Second pick not inprogress → no cashout")
    return "lose"

# ===== Login & Nav =====
def do_login(driver, username, password):
    log.info("[LOGIN] open modal")
    time.sleep(LOGIN_PRE_CLICK_SEC)  # 3 sn önce
    wait_clickable(driver, LL.LOGIN_BUTTON_HEADER, "open login").click()
    time.sleep(LOGIN_POST_CLICK_SEC) # tıkladıktan sonra 3 sn

    wait_visible(driver, LL.USERNAME_INPUT, "username input")
    wait_visible(driver, LL.PASSWORD_INPUT, "password input")
    u = wait_clickable(driver, LL.USERNAME_INPUT, "username")
    p = wait_clickable(driver, LL.PASSWORD_INPUT, "password")
    u.clear(); u.send_keys(username); time.sleep(LOGIN_PER_FIELD_SEC)  # 2 sn
    p.clear(); p.send_keys(password); time.sleep(LOGIN_PER_FIELD_SEC)  # 2 sn
    wait_clickable(driver, LL.LOGIN_SUBMIT_BUTTON, "submit login").click()
    time.sleep(LOGIN_PER_FIELD_SEC)  # 2 sn
    wait_clickable(driver, LL.LOGOUT_BUTTON, "logout visible", timeout=40)
    log.info("🟢 Login successful")

def open_game(driver):
    log.info("[LOBBY] open Warp War tile")
    wait_clickable(driver, L.GAME_TILE_IMG, "game tile").click()
    nap(1.0, 1.4)
    log.info("[GAME] click Real Play")
    wait_clickable(driver, L.REAL_PLAY_BUTTON, "Real Play").click()
    nap(1.0, 1.4)

# ===== Main =====
def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log.info(f"=== START run_id={run_id} ===")
    username, password = load_test_user("test_user_data.json")

    driver = make_driver()
    try:
        driver.get(BASE_URL)
        nap(1.0, 1.4)

        do_login(driver, username, password)
        open_game(driver)

        switch_to_game_iframe(driver)
        focus_canvas_without_click(driver)   # 👈 tıklama yok, sadece odak

        # Hook'u oyunun iç frame'ine enjekte et
        watcher = DomPlayWatcher(driver)
        watcher.install()
        log.info("🧩 in-page play hook installed")

        nap(1.0, 1.4)

        max_rounds = int(os.getenv("MAX_ROUNDS", "20"))
        for i in range(1, max_rounds + 1):
            log.info(f"===== ROUND {i} =====")
            outcome = play_one_round(driver, watcher)
            log.info(f"🏁 round outcome: {outcome}")
            if outcome == "success":
                log.info("✅ target achieved. Stopping.")
                break
            time.sleep(BETWEEN_ROUNDS_SEC)   # eller arası tam 1 sn

        log.info("✅ TEST COMPLETED")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
