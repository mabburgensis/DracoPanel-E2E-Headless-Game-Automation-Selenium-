from selenium.webdriver.common.by import By

class RegisterLocators:
    OPEN_REGISTER_BUTTON = (By.XPATH, '//*[@id="root"]/main/header/div/nav[2]/button[2]')

    EMAIL_INPUT    = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/div/label[1]/input')
    USERNAME_INPUT = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/div/label[2]/input')
    PASSWORD_INPUT = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/div/label[3]/input')

    SUBMIT_BUTTON  = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/div/button')
    LOGOUT_BUTTON  = (By.XPATH, '//*[@id="root"]/main/header/div/div/button')
