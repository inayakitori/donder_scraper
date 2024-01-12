import json
import os
import sqlite3

from _sqlite3 import Error
from matplotlib import pyplot as plt
from matplotlib.axis import Axis
from matplotlib.figure import Figure

from scoreboard import get_scoreboard_data
from site_scraper import *
from elo_calc import *
from diff_calc import *

conn = sqlite3.connect("./res/taiko.db")
cursor = conn.cursor()


# initialise tables if not present
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                                        user_id int PRIMARY KEY,
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
                                        song_name_eng text
                                    );
                                    """)


cursor.execute("""CREATE TABLE IF NOT EXISTS charts (
                                        song_id int NOT NULL,
                                        level_id int NOT NULL,
                                        score_slope int,
                                        score_miyabi int,
                                        certainty float,
                                        PRIMARY KEY (song_id, level_id)
                                    );
                                    """)

cursor.execute("""CREATE TABLE IF NOT EXISTS top_plays (
                                        user_id int NOT NULL,
                                        song_id int NOT NULL,
                                        level_id int NOT NULL,
                                        score int NOT NULL,
                                        PRIMARY KEY (user_id, song_id, level_id)
                                    );
                                    """)

# fill values

# update_db(conn)

# generate elos

# generate_elos(conn)

# clean up

get_scoreboard_data(conn, 1216, 5)

# plot_scores_and_expected_scores(conn, 594288502311, 4)

exit()

songs = cursor.execute("SELECT song_id, song_name_jap, song_name_eng FROM songs").fetchall()

for song_id, song_name_jap, song_name_eng in songs:
    for level_id in range(1,6):
        song_results = get_song_stats(conn, song_id, level_id)
        if song_results is None: continue
        diff_slope, miyabi_elo, r_squared = song_results
        print(f"{song_id}\t{level_id}\t{song_name_jap}\t{song_name_eng}\t{diff_slope}\t{miyabi_elo}\t{r_squared}")

        cursor.execute(
            "INSERT OR REPLACE INTO charts (song_id, level_id, score_slope, score_miyabi, certainty) VALUES(?,?,?,?,?);",
            (song_id, level_id, int(diff_slope), int(miyabi_elo), r_squared)
        )
conn.commit()

if conn:
    conn.close()
exit()
