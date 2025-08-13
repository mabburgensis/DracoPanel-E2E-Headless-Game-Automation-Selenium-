# DracoPanel E2E – Headless Game Automation (Selenium)

End-to-end, headless Selenium tests for DracoPanel’s mini-games.  
The runner opens the Operator Frontend, logs in with **test_user_data.json**, navigates to each game, and drives gameplay via **hotkeys**, while reading `/v1/play` API responses directly from the page (fetch/XHR hook) to verify results.

## ✨ What’s inside

- **Headless-ready** Chrome WebDriver config (CI friendly)
- Unified **in-page hook** capturing `/v1/play` JSON responses (fetch + XHR)
- Natural human-like **delays** across flows
- Modular **locators/** per game
- One-shot **main.py** to run the whole suite sequentially

## 🕹 Supported games & logic

| Game         | Hotkeys                            | Stop condition                                    | Endpoint example                                  |
|--------------|------------------------------------|---------------------------------------------------|---------------------------------------------------|
| **Coinflip** | `SPACE` place, `Q` pick, `W` cashout | 2× consecutive `inprogress` → `W` cashout         | `…coinflipv2…/v1/play`                            |
| **Dragon Tower** | `SPACE`, `Q`, `W`                    | 4× consecutive `inprogress` → `W` cashout         | `…dragontowerv2…/v1/play`                          |
| **Mines**    | `SPACE`, `Q`, `W`                    | 4× consecutive `inprogress` → `W` cashout         | `…minesv2…/v1/play`                                |
| **Keno**     | `Q` once (pre-pick), `SPACE`         | 2× consecutive `win` → stop (no cashout)          | `…kenov2…/v1/play`                                 |
| **Diamonds** | `SPACE`                              | Play **10 rounds**, log `win`/`loss`              | `…diamondsv2…/v1/play`                             |
| **Limbo**    | `SPACE`                              | Play **10 rounds**, log `win`/`loss`              | `…limbov2…/v1/play`                                |
| **Dice**     | `SPACE`                              | Play **10 rounds**, log `win`/`loss`              | `…dicev2…/v1/play` *(same `/v1/play` pattern)*     |

> The hook **normalizes** `result` to: `win`, `lose`, `inprogress` and (where relevant) filters for `action == "result"`.

## 📁 Project structure (example)

```
.
├─ locators/
│  ├─ login_locators.py
│  ├─ warpwar_locators.py
│  ├─ dragontower_locators.py
│  ├─ mines_locators.py
│  ├─ diamonds_locators.py
│  ├─ keno_locators.py
│  ├─ limbo_locators.py
│  └─ dice_locators.py
├─ coinflip.py
├─ dragon_tower.py
├─ mines.py
├─ diamonds.py
├─ keno.py
├─ limbo.py
├─ dice.py
├─ register.py
├─ login.py
├─ main.py          # sequential runner (calls each script)
└─ test_user_data.json
```

## ⚙️ Requirements

- Python **3.10+**
- Google **Chrome** (stable)
- Python deps:
  ```bash
  pip install -U selenium
  ```

> Selenium Manager auto-installs chromedriver—no manual driver needed.

## 🔐 Credentials

Create **`test_user_data.json`** in repo root (or let CI create it from secrets):

```json
{
  "email": "user@example.com",
  "username": "user@example.com",
  "password": "YourPassword!"
}
```

## 🚀 Run locally (headless or headed)

### One command (sequential runner)
Your `main.py` already runs all tests in order.

**macOS / Linux**
```bash
HEADLESS=1 python main.py
```

**Windows PowerShell**
```powershell
$env:HEADLESS="1"; python .\main.py
```

**Windows CMD**
```cmd
set HEADLESS=1 && python main.py
```

> If you added the small tweak to `main.py` (passing `env={**os.environ, "HEADLESS":"1"}` to `subprocess.run`), you can simply run `python main.py` and it will force headless for all child scripts.

### Run a single game (direct script)
```bash
HEADLESS=1 python limbo.py
```

## 🧠 Behavior & timings (consistent across games)

- **Login flow delays:** 3s before open, 3s after open, 2s after username, 2s after password, 2s after submit.
- **Canvas focus:** **no click**, only focus.
- **Per round:** 1s pre-bet delay (`SPACE`), ~0.8–1.0s resolve wait, 1s between rounds.
- Game-specific pick/cashout delays mirror the logic table above.

## 🧪 GitHub Actions (CI/CD)

Add this file as **`.github/workflows/ci.yml`**:

```yaml
name: E2E Headless Tests
on: [push, pull_request, workflow_dispatch]
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      HEADLESS: "1"
      TZ: Europe/Istanbul
      BASE_URL: ${{ secrets.BASE_URL }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - uses: browser-actions/setup-chrome@v1
      - run: |
          python -m pip install --upgrade pip
          pip install selenium
      - name: Create test_user_data.json
        run: |
          cat > test_user_data.json <<'JSON'
          { "email": "${{ secrets.TEST_EMAIL }}",
            "username": "${{ secrets.TEST_USERNAME }}",
            "password": "${{ secrets.TEST_PASSWORD }}" }
          JSON
      - run: python main.py
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-artifacts
          if-no-files-found: ignore
          path: |
            **/*.log
            **/*.png
            run.log
```

Set repo **Secrets**: `TEST_EMAIL`, `TEST_USERNAME`, `TEST_PASSWORD`, (optional) `BASE_URL`.

## 🛠 Troubleshooting

- **Chrome not found**: install Chrome or set binary path in `make_driver()`:
  ```python
  opts.binary_location = r"C:\Path\To\Chrome.exe"
  ```
- **Linux headless deps**:
  ```bash
  sudo apt-get update && sudo apt-get install -y libnss3 libgdk-pixbuf2.0-0 libgtk-3-0 libx11-xcb1
  ```
- **Limbo/Dice not running from main**: ensure they’re listed in `TEST_FILES` inside `main.py`.

## 🔒 Security

- Never commit real creds. Use **secrets** in CI.
- Keep `test_user_data.json` out of public repos if it contains real data.

## 📜 License

Choose a license (MIT recommended) and add `LICENSE` to the repo.
