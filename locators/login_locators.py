from selenium.webdriver.common.by import By

class LoginLocators:
    # Header button that opens the login modal
    LOGIN_BUTTON_HEADER = (By.XPATH, '//*[@id="root"]/main/header/div/nav[2]/button[1]')

    # Modal fields
    USERNAME_INPUT      = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/div/label[1]/input')
    PASSWORD_INPUT      = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/div/label[2]/input')
    LOGIN_SUBMIT_BUTTON = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form/button')

    # Optional: modal root (used to verify the modal stays open on failure)
    MODAL_FORM_ROOT     = (By.XPATH, '//*[@id="root"]/div[2]/div/section/div/form')

    # Successful login indicator (same as we used earlier)
    LOGOUT_BUTTON       = (By.XPATH, '//*[@id="root"]/main/header/div/div/button')

    # Optional error messages (leave as-is or update if you have stable locators)
    # USERNAME_REQUIRED_ERROR = (By.XPATH, 'CHANGE_ME')
    # PASSWORD_REQUIRED_ERROR = (By.XPATH, 'CHANGE_ME')
