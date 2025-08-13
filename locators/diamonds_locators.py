# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By

class DiamondsLocators:
    """Diamonds – lobby kartı, real play butonu ve oyun alanı (iframe/canvas)."""

    # Lobby -> Diamonds banner (verdiğin XPath)
    GAME_TILE_IMG = (
        By.XPATH,
        '//*[@id="root"]/main/div/div[2]/div/div[2]/a[4]/img'
    )

    # Real Play butonu (diğer oyunlarla aynı yapı)
    REAL_PLAY_BUTTON = (
        By.XPATH,
        '//*[@id="root"]/main/div/div/div/button[1]'
    )

    # Oyun alanı
    GAME_IFRAME = (By.CSS_SELECTOR, "iframe")
    GAME_CANVAS = (By.CSS_SELECTOR, "canvas")
