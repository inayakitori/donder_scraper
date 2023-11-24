import json
import os

from selenium.webdriver.common.by import By


def log_in(driver, wait):
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

    wait.until(lambda _: driver.find_element(by=By.CSS_SELECTOR, value=".buttonCenterLink > a:nth-child(1)").click() or True)


def get_users(driver, wait, user_ids):

    users = {}
    for user_no in user_ids:
        driver.get("https://donderhiroba.jp/user_profile.php?taiko_no=" + str(user_no))
        try:
            user_name = driver.find_element(by=By.CSS_SELECTOR, value="#mydon_area > div:nth-child(3)")
            wait.until(lambda _: user_name.is_displayed() or True)
            users[user_no] = user_name.text
        except:
            pass

    with open('users.json', 'w', encoding='utf8') as f:
        json.dump(users, f, ensure_ascii=False)


def load_users():
    with open('users.json', 'r', encoding='utf8') as f:
        return json.loads(f.read())


def get_songs(driver, wait, song_ids):

    songs_list = {}
    for song_id in song_ids:
        driver.get("https://donderhiroba.jp/score_detail.php?song_no=" + str(song_id) + "&level=3")
        try:
            song_name = driver.find_element(by=By.CSS_SELECTOR, value=".songNameTitleScore")
            wait.until(lambda _: song_name.is_displayed() or True)
            songs_list[song_id] = song_name.text
        except :
            pass

    with open('songs.json', 'w', encoding='utf8') as f:
        json.dump(songs_list, f, ensure_ascii=False)


def load_songs():
    with open('songs.json', 'r', encoding='utf8') as f:
        return json.loads(f.read())


def get_scores(driver, wait, users, songs):
    scores = {}
    for user_id in users:

        for song_id in songs:
            scores[(user_id, song_id)] = get_score(driver, wait, user_id, song_id)
            print(songs[song_id] + " | " + users[user_id] + " : " + str(scores[(user_id, song_id)]))

    with open('scores.json', 'w', encoding='utf8') as f:
        json.dump(scores, f, ensure_ascii=False)


def get_score(driver, wait, user_id, song_id):
    driver.get("https://donderhiroba.jp/score_detail.php?song_no=" + str(song_id) + "&level=3&taiko_no=" + str(user_id))
    score_box = driver.find_element(by=By.CSS_SELECTOR, value=".high_score")
    wait.until(lambda _: score_box.is_displayed() or True)
    score_text = score_box.text[:-1]
    return int(score_text)


