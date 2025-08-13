# common/user_data.py
import json, os

# Dosyayı proje kökünde sabitle (cwd değişse de sorun olmasın)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILE = os.path.join(ROOT, "test_user_data.json")

def save_user_data(email, username, password):
    data = {"email": email, "username": username, "password": password}
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_user_data():
    if not os.path.exists(FILE):
        raise FileNotFoundError(
            "test_user_data.json bulunamadı. Lütfen önce register.py çalıştırın."
        )
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)
