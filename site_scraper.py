import json
import os
import sqlite3
from sqlite3 import Cursor, Connection
from time import sleep
from typing import List

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.common import ElementNotInteractableException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import threading

import my_globals
from aidon import get_aidon_user_ids
from translator import jap_to_eng_conversion, is_english_name

LEVELS = {
    1: "easy",
    2: "normal",
    3: "hard",
    4: "oni",
    5: "ura oni",
}


def update_db(conn: Connection):
    cursor = conn.cursor()

    # generate songs
    # get_songs_and_charts(conn)

    # get user ids. jank but works
    print("getting user ids")
    user_ids = get_aidon_user_ids()
    print("obtained user ids")
    # generate users
    print("getting users")
    users = get_users(conn, user_ids)
    print("obtained users")

    # generate scores
    user_threads = []
    top_plays = []

    print("getting plays")
    for thread_index, users_for_thread in enumerate(divide_chunks(users, 9)):
        thread = threading.Thread(target=get_user_top_plays, args=(thread_index, top_plays, users_for_thread))
        user_threads.append(thread)
        thread.start()

    for thread in user_threads:
        thread.join()

    for top_play in top_plays:
        cursor.execute("INSERT or REPLACE INTO top_plays (user_id, song_id, level_id, score) VALUES(?,?,?,?);",
                       top_play)
        conn.commit()
    print("obtained plays")


def setup_donder():
    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(options=options)
    driver.set_window_rect(10, 10, 1000, 1000)
    errors = [NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException]
    wait = WebDriverWait(driver, timeout=600, poll_frequency=0.2, ignored_exceptions=errors)
    driver.get('https://donderhiroba.jp/login.php')

    # login button
    go_to_login_button = driver.find_element(by=By.CSS_SELECTOR, value="div.image_base:nth-child(2) > img:nth-child(1)")
    wait.until(lambda _: go_to_login_button.click() or True)

    # user and pass
    mail_input = driver.find_element(by=By.CSS_SELECTOR, value="#mail")
    wait.until(lambda _: mail_input.click() or True)
    mail_input.send_keys(my_globals.donder_mail)

    pass_input = driver.find_element(by=By.CSS_SELECTOR, value="#pass")
    wait.until(lambda _: pass_input.click() or True)
    pass_input.send_keys(my_globals.donder_pass)

    # donder account page
    account_login = driver.find_element(by=By.CSS_SELECTOR, value="#btn-idpw-login")
    wait.until(lambda _: account_login.click() or True)
    wait.until(
        lambda _: driver.find_element(by=By.CSS_SELECTOR, value=".buttonCenterLink > a:nth-child(1)").click() or True)

    return driver, wait


def get_user_top_plays(thread_index, top_plays, user_ids):
    driver: WebDriver
    completed = 0
    print(f"#{thread_index} handling users {user_ids}")
    for (user_id, user_name) in user_ids:
        try:
            if 'driver' not in locals():
                driver, wait = setup_donder()
            completed += 1
            print(f"#{thread_index} handling user {user_name} ({completed}/{len(user_ids)})")
            played_maps = set()
            for genre in range(1, 9):
                driver.get(create_link("score_list", taiko_no=user_id, genre=genre))
                buttons: List[WebElement] = driver.find_elements(By.TAG_NAME, "a")
                for button in buttons:
                    link = button.get_attribute("href")
                    if link is None or "score_detail.php?" not in link: continue

                    button_img = button.find_element(By.CSS_SELECTOR, "img")
                    # this map has been played, now add to list
                    if "none" in button_img.get_attribute("src"): continue

                    map_attributes = extract_link_attributes(link)
                    map_id = (int(map_attributes["song_no"]), int(map_attributes["level"]))
                    played_maps.add(map_id)
            for (song_id, level_id) in played_maps:
                attempts = 0
                while attempts < 10:
                    try:
                        score = get_score(driver, wait, user_id, song_id, level_id)
                        if score > 0:
                            top_plays.append(
                                (user_id, song_id, level_id, score)
                            )
                    except Exception as e:
                        print(f"#{thread_index} failed to handle user{user_name}'s score {song_id} {level_id}. attempt {attempts}/10: {e}")
                        driver.close()
                        driver, wait = setup_donder()
                        attempts += 1
                    break
        except Exception as e:
            print(f"#{thread_index} failed to handle user{user_name}: {e}")
            driver.close()
            driver, wait = setup_donder()
    driver.close()


def get_songs_and_charts(conn: Connection):
    cursor = conn.cursor()

    driver, wait = setup_donder()
    driver.get(create_link("score_list"))

    print("no song db, generating")

    jap_to_eng_names = jap_to_eng_conversion()

    for genre in range(1, 9):
        driver.get(create_link("score_list", genre=genre))
        song_boxes: List[WebElement] = driver.find_elements(By.XPATH, "/html/body/div/div/div[1]/div[2]/ul[2]/div/li")
        # print(f"genre {genre}: {song_boxes}")
        for song_box in song_boxes:
            link_button = song_box.find_element(By.TAG_NAME, "a")
            link = link_button.get_attribute("href")
            map_attributes = extract_link_attributes(link)

            song_name_jap = song_box.text
            song_name_eng = ""
            try:
                # Try to get jap song name from dictionary
                song_name_eng = jap_to_eng_names[song_name_jap]
            except KeyError as e:
                # if it can't be found and the japanese name is in english use that instead
                if is_english_name(song_name_jap):
                    song_name_eng = song_name_jap
                    print(f"song {e} 's eng_name does not exist but was converted")
                else:
                    print(f"song {e} 's eng_name does not exist. left empty")

            song_id = map_attributes["song_no"]
            # print(f"adding {song_id}, {song_name_jap}")
            cursor.execute(
                "INSERT or REPLACE INTO songs (song_id, song_name_jap, song_name_eng, genre_id) VALUES(?,?,?,?);",
                (song_id, song_name_jap, song_name_eng, genre)
            )
            diffs_to_add = [1, 2, 3, 4]
            if len(song_box.find_elements(By.TAG_NAME, "a")) == 1:
                diffs_to_add = [5]
            for diff in diffs_to_add:
                cursor.execute(
                    "INSERT or REPLACE INTO charts (song_id, level_id) VALUES(?,?);",
                    (song_id, diff)
                )

    driver.close()
    conn.commit()
    return cursor.execute("SELECT * FROM songs;").fetchall()


def get_users(conn: Connection, user_ids: list[int]):
    cursor = conn.cursor()
    driver, wait = setup_donder()

    for (user_no, discord_no) in user_ids:
        driver.get(create_link("user_profile", taiko_no=user_no))
        try:
            user_name = driver.find_element(by=By.CSS_SELECTOR, value="#mydon_area > div:nth-child(3)")
            wait.until(lambda _: user_name.is_displayed() or True)
            cursor.execute("INSERT or REPLACE INTO users (user_id, discord_id, user_name) VALUES(?,?,?);",
                           (user_no, discord_no, user_name.text))
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
        "song_no": None if song_no is None else str(song_no),
        "level": None if level is None else str(level),
        "genre": None if genre is None else str(genre),
    }

    for attribute in attributes:
        if attributes[attribute] is None: continue
        link += attribute + "=" + attributes[attribute] + "&"

    return link[:-1]


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]
