# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By

class KenoLocators:
    """Keno – lobby kartı, real play butonu ve oyun alanı (iframe/canvas)."""

    # Lobby -> Keno banner
    GAME_TILE_IMG = (
        By.XPATH,
        '//*[@id="root"]/main/div/div[2]/div/div[2]/a[5]/img'
    )

    # Real Play butonu
    REAL_PLAY_BUTTON = (
        By.XPATH,
        '//*[@id="root"]/main/div/div/div/button[1]'
    )

    # Oyun alanı
    GAME_IFRAME = (By.CSS_SELECTOR, "iframe")
    GAME_CANVAS = (By.CSS_SELECTOR, "canvas")
