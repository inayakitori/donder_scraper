import json
import os

from selenium import webdriver
from selenium.common import ElementNotInteractableException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from site_scraper import *

driver = webdriver.Firefox()
errors = [NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException]
wait = WebDriverWait(driver, timeout=10, poll_frequency=0.2, ignored_exceptions=errors)

log_in(driver, wait)

# todo: actually use the db

user_ids = [
     90023356630,
    191933474995,
    227313008892,
    240962837781,
    268172844251,
    326921781427,
    389352301003,
    413797428087,
    430222689046,
    469030163443,
    486534354187,
    495549340545,
    527613099274,
    594288502311,
    608721728595,
    640708845617,
    650898881996,
    679895090257,
    719561057294,
    721833239786,
    867253230159,
]

user_ids = set(user_ids)

get_users(driver, wait, user_ids)
users = load_users()  # <-- generates user data

get_songs(driver, wait, range(1, 1300))
songs = load_songs()  # <-- generates song data

get_scores(driver, wait, users, songs)


driver.close()
exit()
