from selenium.webdriver.common.by import By

class WarpWarLocators:
    # Lobby -> oyun ikonu (Warp War)
    GAME_TILE_IMG = (
        By.XPATH,
        '//*[@id="root"]/main/div/div[2]/div/div[2]/a[1]/img'
    )

    # Real Play
    REAL_PLAY_BUTTON = (
        By.XPATH,
        '//*[@id="root"]/main/div/div/div/button[1]'
    )

    # Game area (iframe + canvas)
    GAME_IFRAME = (By.CSS_SELECTOR, "iframe")
    GAME_CANVAS = (By.CSS_SELECTOR, "canvas")

    # (İsteğe bağlı) DOM fallback aramaları
    X_PLACEBET = (By.XPATH,
        "//*[self::button or self::div or self::span]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğiöşü'),'place bet') "
        "or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğiöşü'),'bahis yap')]"
    )
    X_CASHOUT = (By.XPATH,
        "//*[self::button or self::div or self::span]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğiöşü'),'cashout') "
        "or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğiöşü'),'kazancı topla') "
        "or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğiöşü'),'kazanci topla')]"
    )
