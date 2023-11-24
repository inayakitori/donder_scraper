import os

from selenium import webdriver
from selenium.common import ElementNotInteractableException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

driver = webdriver.Firefox()
driver.get('https://donderhiroba.jp/login.php')

# login button
go_to_login_button = driver.find_element(by=By.CSS_SELECTOR, value="div.image_base:nth-child(2) > img:nth-child(1)")
go_to_login_button.click()

# user and pass. keeps on trying to click until it can
errors = [NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException]
wait = WebDriverWait(driver, timeout=10, poll_frequency=0.2, ignored_exceptions=errors)

mail_input = driver.find_element(by=By.CSS_SELECTOR, value="#mail")
wait.until(lambda _: mail_input.click() or True)
mail_input.send_keys(os.environ['DONDER_MAIL'])

pass_input = driver.find_element(by=By.CSS_SELECTOR, value="#pass")
wait.until(lambda _: pass_input.click() or True)
pass_input.send_keys(os.environ['DONDER_PASS'])

# donder account page
account_login = driver.find_element(by=By.CSS_SELECTOR, value="#btn-idpw-login")
wait.until(lambda _: account_login.click() or True)

wait.until(lambda _: driver.find_element(by=By.CSS_SELECTOR, value=".buttonCenterLink > a:nth-child(1)").click() or True)
