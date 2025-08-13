import subprocess
import sys
import os

TEST_FILES = [
    "register.py",
    "login.py",
    "warpwar.py",
    "dragon_tower.py",
    "mines.py",
    "diamonds.py",
    "keno.py",
    "limbo.py",
    "dice.py"
]

def run_test(file_name):
    print(f"\n▶ {file_name} başlatılıyor...")
    headless_env = {**os.environ, "HEADLESS": "1"}  # <<< TÜM çocuk süreçlere HEADLESS=1
    result = subprocess.run([sys.executable, file_name], env=headless_env)
    if result.returncode != 0:
        print(f"❌ {file_name} başarısız. Test zinciri durdu.")
        sys.exit(result.returncode)
    else:
        print(f"✅ {file_name} tamamlandı.")

def main():
    for test_file in TEST_FILES:
        run_test(test_file)

if __name__ == "__main__":
    main()
