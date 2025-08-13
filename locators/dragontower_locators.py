# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By

class DragonTowerLocators:
    """
    Dragon Tower – ana sayfadaki oyun kartı, real play butonu ve oyun alanı
    """

    # Lobby -> Oyun kartı (Dragon Tower)
    GAME_TILE_IMG = (
        By.XPATH,
        '//*[@id="root"]/main/div/div[2]/div/div[2]/a[2]/img'
    )

    # Real Play butonu
    REAL_PLAY_BUTTON = (
        By.XPATH,
        '//*[@id="root"]/main/div/div/div/button[1]'
    )

    # Oyun alanı (iframe + canvas)
    GAME_IFRAME = (By.CSS_SELECTOR, "iframe")
    GAME_CANVAS = (By.CSS_SELECTOR, "canvas")

    # (İsteğe bağlı) fallback: metinle Place Bet / Cashout araması – hotkey kullandığımız için gerekmiyor
    X_PLACEBET = (
        By.XPATH,
        "//*[self::button or self::div or self::span]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğıiöşü'),'place bet') "
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğıiöşü'),'bahis yap')]"
    )
    X_CASHOUT = (
        By.XPATH,
        "//*[self::button or self::div or self::span]"
        "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğıiöşü'),'cashout') "
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğıiöşü'),'kazancı topla') "
        " or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİİÖŞÜ','abcdefghijklmnopqrstuvwxyzçğıiöşü'),'kazanci topla')]"
    )
