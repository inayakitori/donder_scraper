import json
import os
import sqlite3

from _sqlite3 import Error
from matplotlib import pyplot as plt
from matplotlib.axis import Axis
from matplotlib.figure import Figure

from site_scraper import *
from elo_calc import *
from diff_calc import *

conn = sqlite3.connect("./res/taiko.db")
cursor = conn.cursor()

# fill values

# update_db(conn)

# generate elos

generate_elos(conn)

# clean up

plot_elo_vs_scores(conn, [
    (1103, 4, 'Godish', None),
    (695,  4, 'haikei doppelganger', None),
    (816,  4, 'hoshikuzu', None),
    (1149,  4, 'Phony', None),
    (463,  4, 'yuugen no ran', None),
])

if conn:
    conn.close()
exit()
