import json
import os
import sqlite3

from _sqlite3 import Error

from site_scraper import *

conn = sqlite3.connect("./res/taiko.db")
cursor = conn.cursor()

# fill values
update_db(conn)


# clean up

if conn:
    conn.close()
exit()
