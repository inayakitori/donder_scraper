import getopt
import json
import os
import sqlite3
import sys

from _sqlite3 import Error
from matplotlib import pyplot as plt
from matplotlib.axis import Axis
from matplotlib.figure import Figure

import my_globals
import site_scraper
from scoreboard import get_scoreboard_data
from elo_calc import *
from diff_calc import *

argumentList = sys.argv[1:]

# Long options
long_options = ["aidon_url=", "donder_mail=", "donder_pass="]

arguments, values = getopt.getopt(argumentList, "a:m:p:", long_options)

print((arguments, values))
for currentArgument, currentValue in arguments:
    if currentArgument == "--aidon_url":
        my_globals.aidon_url = currentValue

    elif currentArgument == "--donder_mail":
        my_globals.donder_mail = currentValue

    elif currentArgument == "--donder_pass":
        my_globals.donder_pass = currentValue

sqlite3.threadsafety = 3

conn = sqlite3.connect("./res/taiko.db")
cursor = conn.cursor()

# initialise tables if not present
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                                        user_id int PRIMARY KEY,
                                        discord_id int,
                                        user_name text NOT NULL,
                                        elo1 float,
                                        elo2 float,
                                        elo3 float,
                                        elo4 float
                                    );
                                    """)

cursor.execute("""CREATE TABLE IF NOT EXISTS songs (
                                        song_id int PRIMARY KEY,
                                        song_name_jap text NOT NULL,
                                        song_name_eng text,
                                        genre_id integer
                                    );
                                    """)


cursor.execute("""CREATE TABLE IF NOT EXISTS charts (
                                        song_id int NOT NULL,
                                        level_id int NOT NULL,
                                        score_slope int,
                                        score_miyabi int,
                                        sd_mean float,
                                        sd_sd float,
                                        PRIMARY KEY (song_id, level_id)
                                    );
                                    """)

cursor.execute("""CREATE TABLE IF NOT EXISTS top_plays (
                                        user_id int NOT NULL,
                                        song_id int NOT NULL,
                                        level_id int NOT NULL,
                                        score int NOT NULL,
                                        rank int,
                                        crown int,
                                        good_cnt int,
                                        ok_cnt int,
                                        bad_cnt int,
                                        combo_cnt int,
                                        roll_cnt int,
                                        PRIMARY KEY (user_id, song_id, level_id)
                                    );
                                    """)

# fill values
with conn:
    site_scraper.update_db(conn)
    # plot_elo_vs_scores(conn, [(882, 5, 'otome', None)])

    generate_elos(conn)

    # plot_scores_and_expected_scores(conn, 594288502311, 4)
    # charts
    songs = cursor.execute("SELECT song_id, song_name_jap, song_name_eng FROM songs").fetchall()
    for song_id, song_name_jap, song_name_eng in songs:
        for level_id in range(1,6):
            song_results = get_song_stats(conn, song_id, level_id)
            if song_results is None:
                cursor.execute(
                    "INSERT OR REPLACE INTO charts (song_id, level_id, score_slope, score_miyabi, sd_mean, sd_sd) VALUES(?,?,?,?,?,?);",
                    (song_id, level_id, None, None, None, None)
                )
                continue
            diff_slope, miyabi_elo, uncertainty_mean_sample, uncertainty_sd = song_results
            print(f"{song_id}\t{level_id}\t{song_name_jap}\t{song_name_eng}\t{diff_slope}\t{miyabi_elo}\t{uncertainty_mean_sample}\t{uncertainty_sd}")

            cursor.execute(
                "INSERT OR REPLACE INTO charts (song_id, level_id, score_slope, score_miyabi, sd_mean, sd_sd) VALUES(?,?,?,?,?,?);",
                (song_id, level_id, int(diff_slope), int(miyabi_elo), uncertainty_mean_sample, uncertainty_sd)
            )
    conn.commit()

if conn:
    conn.close()
exit()
