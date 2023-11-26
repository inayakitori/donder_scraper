import json
import os
import sqlite3
from sqlite3 import Cursor, Connection
from time import sleep
from typing import List

import selenium.webdriver.firefox.options
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.common import ElementNotInteractableException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import threading

USERS_IDS = [
    13400555573,
    14678744058,
    46359019554,
    65847441251,
    90023356630,
    94227648687,
    102383147279,
    131649595564,
    149585248793,
    191933474995,
    195478548305,
    208321119402,
    227313008892,
    240962837781,
    268172844251,
    308020838473,
    314829087457,
    326921781427,
    363214271477,
    389352301003,
    413797428087,
    428490279701,
    430222689046,
    440673037432,
    468289098677,
    469030163443,
    486534354187,
    495549340545,
    527613099274,
    545922793247,
    594288502311,
    608721728595,
    640708845617,
    650898881996,
    679895090257,
    709503819958,
    719561057294,
    721833239786,
    735744555857,
    816267046818,
    821656887106,
    867253230159,
    921425336631,
    948993286979,
    966813482456,
    973913393844,
    981231646714,
    991782996877,
]

LEVELS = {
    1: "easy",
    2: "normal",
    3: "hard",
    4: "oni",
    5: "ura oni",
}


def update_db(conn: Connection):

    cursor = conn.cursor()

    # initialise tables if not present
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                                        user_id int PRIMARY KEY,
                                        user_name text NOT NULL,
                                        elo float
                                    );
                                    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS songs (
                                        song_id int PRIMARY KEY,
                                        song_name text NOT NULL
                                    );
                                    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS top_plays (
                                        user_id int NOT NULL,
                                        song_id int NOT NULL,
                                        level_id int NOT NULL,
                                        score int NOT NULL,
                                        PRIMARY KEY ( user_id, song_id, level_id)
                                    );
                                    """)

    # get or generate users
    users = cursor.execute("SELECT user_id, user_name FROM users;").fetchall()

    # get or generate songs
    songs = cursor.execute("SELECT * FROM songs;").fetchall()

    # get or generate scores
    user_threads = []

    top_plays = []
    for users_for_thread in divide_chunks(users, 5):
        thread = threading.Thread(target=get_user_top_plays, args=(top_plays, users_for_thread))
        user_threads.append(thread)
        thread.start()

    for thread in user_threads:
        thread.join()

    for top_play in top_plays:
        cursor.execute("INSERT or REPLACE INTO top_plays (user_id, song_id, level_id, score) VALUES(?,?,?,?);",
                       top_play)
        conn.commit()


def setup_donder():
    driver = webdriver.Firefox()
    errors = [NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException]
    wait = WebDriverWait(driver, timeout=30, poll_frequency=0.2, ignored_exceptions=errors)
    driver.get('https://donderhiroba.jp/login.php')

    # login button
    go_to_login_button = driver.find_element(by=By.CSS_SELECTOR, value="div.image_base:nth-child(2) > img:nth-child(1)")
    wait.until(lambda _: go_to_login_button.click() or True)

    # user and pass
    mail_input = driver.find_element(by=By.CSS_SELECTOR, value="#mail")
    wait.until(lambda _: mail_input.click() or True)
    mail_input.send_keys(os.environ['DONDER_MAIL'])

    pass_input = driver.find_element(by=By.CSS_SELECTOR, value="#pass")
    wait.until(lambda _: pass_input.click() or True)
    pass_input.send_keys(os.environ['DONDER_PASS'])

    # donder account page
    account_login = driver.find_element(by=By.CSS_SELECTOR, value="#btn-idpw-login")
    wait.until(lambda _: account_login.click() or True)
    wait.until(
        lambda _: driver.find_element(by=By.CSS_SELECTOR, value=".buttonCenterLink > a:nth-child(1)").click() or True)

    return driver, wait


def get_user_top_plays(top_plays, user_ids):
    driver, wait = setup_donder()

    print("handling users {}".format(user_ids))
    for (user_id, user_name) in user_ids:
        played_maps = set()
        for genre in range(1, 9):
            driver.get(create_link("score_list", taiko_no=user_id, genre=genre))
            buttons: List[WebElement] = driver.find_elements(By.TAG_NAME, "a")
            for button in buttons:
                link = button.get_attribute("href")
                if link is None or "score_detail.php?" not in link: continue

                button_img = button.find_element(By.CSS_SELECTOR, "img")
                # this map has been played, now add to list
                if "none" in button_img.get_attribute("src"):continue

                map_attributes = extract_link_attributes(link)
                map_id = (int(map_attributes["song_no"]), int(map_attributes["level"]))
                played_maps.add(map_id)
        for (song_id, level_id) in played_maps:
            score = get_score(driver, wait, user_id, song_id, level_id)
            if score > 0:
                top_plays.append(
                    (user_id, song_id, level_id, score)
                )
    driver.close()


def get_songs(conn: Connection):
    cursor = conn.cursor()

    driver, wait = setup_donder()
    driver.get(create_link("score_list"))

    self_id = os.environ["DONDER_ID"]
    print("no song db, generating")
    for genre in range(1, 9):
        driver.get(create_link("score_list", taiko_no=self_id, genre=genre))
        song_boxes: List[WebElement] = driver.find_elements(By.XPATH, "/html/body/div/div/div[1]/div[3]/ul[2]/div/li")
        for song_box in song_boxes:
            link_button = song_box.find_element(By.TAG_NAME, "a")
            link = link_button.get_attribute("href")
            map_attributes = extract_link_attributes(link)

            song_name = song_box.text
            song_id = map_attributes["song_no"]

            cursor.execute("INSERT or REPLACE INTO songs (song_id, song_name) VALUES(?,?);", (song_id, song_name))

    driver.close()
    conn.commit()
    return cursor.execute("SELECT * FROM songs;").fetchall()


def get_users(conn: Connection):
    cursor = conn.cursor()
    driver, wait = setup_donder()

    for user_no in USERS_IDS:
        driver.get(create_link("user_profile", taiko_no=user_no))
        try:
            user_name = driver.find_element(by=By.CSS_SELECTOR, value="#mydon_area > div:nth-child(3)")
            wait.until(lambda _: user_name.is_displayed() or True)
            cursor.execute("INSERT or REPLACE INTO users (user_id, user_name) VALUES(?,?);", (user_no, user_name.text))
        except Exception as e:
            print(e)
            pass
    driver.close()
    conn.commit()
    return cursor.execute("SELECT user_id, user_name FROM users;").fetchall()


def get_score(driver, wait, user_id, song_id, level_id):
    driver.get(create_link(page="score_detail", taiko_no=user_id, song_no=song_id, level=level_id))
    score_box = driver.find_element(by=By.CSS_SELECTOR, value=".high_score")
    wait.until(lambda _: score_box.is_displayed() or True)
    score_text = score_box.text[:-1]
    return int(score_text)


def extract_link_attributes(link):
    attributes = {}
    attributes_only = link.split("?")[1].split("&")
    for attribute in attributes_only:
        sections = attribute.split("=")
        key = sections[0]
        value = sections[1]
        attributes[key] = value
    return attributes


def create_link(page, taiko_no=None, song_no=None, level=None, genre=None):
    link = "https://donderhiroba.jp/" + page + ".php?"
    attributes = {
        "taiko_no": None if taiko_no is None else str(taiko_no).zfill(12),
        "song_no":  None if song_no  is None else str(song_no),
        "level":    None if level    is None else str(level),
        "genre":    None if genre    is None else str(genre),
    }

    for attribute in attributes:
        if attributes[attribute] is None: continue
        link += attribute + "=" + attributes[attribute] + "&"

    return link[:-1]


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]