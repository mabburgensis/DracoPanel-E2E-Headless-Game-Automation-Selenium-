# -*- coding: utf-8 -*-
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

from locators.login_locators import LoginLocators as LL
from locators.keno_locators import KenoLocators as L

LOG_FMT = "%(asctime)s | %(levelname)-7s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("keno")

BASE_URL = os.getenv("BASE_URL", "https://operator-frontend-v2-641161620205.europe-west1.run.app/")
DEFAULT_TIMEOUT   = int(os.getenv("DEFAULT_TIMEOUT", "25"))
GAME_LOAD_TIMEOUT = int(os.getenv("GAME_LOAD_TIMEOUT", "90"))

# —— Beklemeler (isteğinize göre) ——
AFTER_OPEN_SLEEP     = (0.9, 1.3)
BET_RESOLVE_WAIT     = (0.8, 1.0)     # SPACE sonrası kısa animasyon
PRE_BET_DELAY_SEC    = 1.0            # HER place bet öncesi tam 1 sn
BETWEEN_ROUNDS_SEC   = 1.0            # Eller arası tam 1 sn
AFTER_SINGLE_Q_SEC   = 2.0            # İlk Q’dan sonra tam 2 sn
LOGIN_PRE_CLICK_SEC  = 3.0            # Login butonuna basmadan önce 3 sn
LOGIN_POST_CLICK_SEC = 3.0            # Login butonuna bastıktan sonra 3 sn
LOGIN_PER_FIELD_SEC  = 2.0            # Username, password ve submit sonrasında 2 sn
AFTER_FINAL_WIN_SEC   = 3.0           # 2. ardışık WIN’den sonra bekleme

KEYPRESS_GAP         = (0.06, 0.12)

def nap(a=0.6, b=1.2): time.sleep(random.uniform(a, b))
def tiny_nap(a=0.12, b=0.25): time.sleep(random.uniform(a, b))

def load_test_user(fp="test_user_data.json"):
    if not os.path.exists(fp): raise FileNotFoundError(f"{fp} bulunamadı")
    with open(fp, "r", encoding="utf-8") as f: data = json.load(f)
    username = (data.get("username") or data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password: raise ValueError("username/email ve password gerekli")
    return username, password

def make_driver():
    opts = Options()
    if os.getenv("HEADLESS", "0") in ("1", "true", "True"):
        opts.add_argument("--headless=new"); opts.add_argument("--window-size=1366,900")
        opts.add_argument("--hide-scrollbars"); opts.add_argument("--use-gl=swiftshader"); opts.add_argument("--disable-gpu")
    else:
        opts.add_argument("--start-maximized")
    opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage"); opts.add_argument("--mute-audio")
    return webdriver.Chrome(service=Service(), options=opts)

def wait_clickable(driver, locator, desc, timeout=DEFAULT_TIMEOUT):
    log.info(f"⏳ wait clickable: {desc}")
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))

def wait_visible(driver, locator, desc, timeout=DEFAULT_TIMEOUT):
    log.info(f"⏳ wait visible: {desc}")
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))

def send_hotkey(driver, key):
    ActionChains(driver).pause(random.uniform(*KEYPRESS_GAP)).send_keys(key).perform()
    tiny_nap()

# —— In-page hook (fetch + XHR) ——
HOOK_JS = r"""
(() => {
  try {
    if (window.__PLAY_HOOK_INSTALLED__) return;
    window.__PLAY_HOOK_INSTALLED__ = true;
    window.__PLAY_RESULTS = [];

    const PLAY_HINT = "/v1/play";
    function norm(v){
      if(!v) return null;
      v = String(v).toLowerCase();
      if (v === "win" || v === "won" || v === "success") return "win";
      if (v === "loss" || v === "lose" || v === "lost" || v === "fail") return "lose";
      if (v === "in_progress" || v === "inprogress") return "inprogress";
      return null;
    }
    function push(url, payload){
      try{
        const d = (payload && payload.data) || {};
        window.__PLAY_RESULTS.push({
          t: Date.now(),
          url, payload,
          action: d.action || null,
          result: norm(d.result),
          session_id: d.session_id || null
        });
      }catch(e){}
    }
    window.__PLAY_FLUSH_ALL__ = () => { try { window.__PLAY_RESULTS.length = 0; } catch(e){} };

    const _fetch = window.fetch;
    window.fetch = async function(input, init){
      const reqUrl = (typeof input === "string" ? input : (input && input.url)) || "";
      const p = _fetch.apply(this, arguments);
      try{
        const res = await p; const url = (res && res.url) || reqUrl || "";
        if (url.includes(PLAY_HINT)) { try{ const t = await res.clone().text(); try{ push(url, JSON.parse(t)); }catch{} }catch{} }
        return res;
      }catch(e){ throw e; }
    };

    const XHR = window.XMLHttpRequest, _open = XHR.prototype.open, _send = XHR.prototype.send;
    XHR.prototype.open = function(m,u){ this.__url=u||""; return _open.apply(this, arguments); };
    XHR.prototype.send = function(){
      this.addEventListener("load", () => {
        try{
          const url = this.__url || "";
          if (url.includes(PLAY_HINT)) { const t = this.responseText || ""; try{ push(url, JSON.parse(t)); }catch{} }
        }catch(e){}
      });
      return _send.apply(this, arguments);
    };
  } catch(err){ console.error("HOOK_ERR", err); }
})();
"""

class DomPlayWatcher:
    def __init__(self, driver): self.driver = driver
    def install(self): self.driver.execute_script(HOOK_JS)
    def flush_all(self): self.driver.execute_script("window.__PLAY_FLUSH_ALL__ && window.__PLAY_FLUSH_ALL__();")
    def pop_result_since(self, since_ms: int, session_id: str | None):
        return self.driver.execute_script("""
          const since = arguments[0]>>>0, sid = arguments[1]||null;
          if (!Array.isArray(window.__PLAY_RESULTS)) return null;
          for (let i=0;i<window.__PLAY_RESULTS.length;i++){
            const it = window.__PLAY_RESULTS[i];
            if (it.t >= since && it.action === 'result' && (!sid || it.session_id === sid)){
              window.__PLAY_RESULTS.splice(i,1); return it;
            }
          }
          return null;
        """, int(since_ms), session_id)
    def wait_result(self, since_ms: int, session_id: str | None, timeout: float = 15.0):
        t_end = time.time() + timeout
        while time.time() < t_end:
            it = self.pop_result_since(since_ms, session_id)
            if it: return it
            time.sleep(0.09)
        return None

# —— Game helpers ——
def switch_to_game_iframe(driver):
    log.info("🔍 searching for game iframe (with a <canvas>)")
    t_end = time.time() + GAME_LOAD_TIMEOUT
    while time.time() < t_end:
        driver.switch_to.default_content()
        for fr in driver.find_elements(By.CSS_SELECTOR, "iframe"):
            driver.switch_to.default_content(); driver.switch_to.frame(fr)
            if driver.find_elements(By.CSS_SELECTOR, "canvas"):
                log.info("🔁 switched into game iframe"); nap(*AFTER_OPEN_SLEEP); return
        nap(0.6, 1.0)
    raise TimeoutException("No iframe with a <canvas> found.")

def focus_canvas_without_click(driver):
    canvas = wait_visible(driver, L.GAME_CANVAS, "game canvas", timeout=GAME_LOAD_TIMEOUT)
    driver.execute_script("arguments[0].setAttribute('tabindex','0'); arguments[0].focus();", canvas)
    return canvas

def now_ms(driver): return driver.execute_script("return Date.now();")

# —— Strategy ——
def run_strategy(driver, watcher: DomPlayWatcher, max_rounds: int = 80) -> str:
    log.info("🟩 Initial single pick (Q)")
    send_hotkey(driver, "q")
    time.sleep(AFTER_SINGLE_Q_SEC)  # tam 2 saniye

    consec_wins = 0
    for rnd in range(1, max_rounds + 1):
        log.info(f"===== ROUND {rnd} =====")

        watcher.flush_all()              # eski kayıtları at
        log.info("▶️  Place bet (SPACE)")
        time.sleep(PRE_BET_DELAY_SEC)    # her bet öncesi 1 sn
        t_bet = now_ms(driver)
        send_hotkey(driver, Keys.SPACE)
        nap(*BET_RESOLVE_WAIT)

        item = watcher.wait_result(since_ms=t_bet, session_id=None, timeout=12)
        result = (item or {}).get("result")
        log.info(f"🎯 round result: {result}")

        if result == "win":
            consec_wins += 1
            log.info(f"✅ WIN (streak {consec_wins}/2)")
            if consec_wins >= 2:
                log.info("🏁 two consecutive wins → stopping.")
                time.sleep(AFTER_FINAL_WIN_SEC)   # <<< 3 saniye bekle
                return "success"
        else:
            consec_wins = 0
            log.info("❌ LOSS/unknown → reset streak (no new pick)")

        time.sleep(BETWEEN_ROUNDS_SEC)   # eller arası 1 sn

    return "stopped"

# —— Login & Navigation ——
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
    log.info("[LOBBY] open Keno tile")
    wait_clickable(driver, L.GAME_TILE_IMG, "keno tile").click(); nap(1.0, 1.4)
    log.info("[GAME] click Real Play")
    wait_clickable(driver, L.REAL_PLAY_BUTTON, "Real Play").click(); nap(1.0, 1.4)

def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log.info(f"=== START (keno) run_id={run_id} ===")
    username, password = load_test_user("test_user_data.json")

    driver = make_driver()
    try:
        driver.get(BASE_URL); nap(1.0, 1.4)

        do_login(driver, username, password)
        open_game(driver)

        switch_to_game_iframe(driver)
        focus_canvas_without_click(driver)  # tıklama yok, sadece odak

        watcher = DomPlayWatcher(driver); watcher.install()
        nap(0.9, 1.2)

        outcome = run_strategy(driver, watcher, max_rounds=int(os.getenv("MAX_ROUNDS", "80")))
        log.info(f"🏁 outcome: {outcome}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
