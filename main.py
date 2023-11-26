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

# generate_elos(conn)

# clean up

plot_elo_vs_scores(conn, [
    (285, 5, 'senbon', None),
    (695, 4, 'haikei', None),
])

if conn:
    conn.close()
exit()
