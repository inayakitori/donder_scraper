from sqlite3 import Connection

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

import random

def get_difficulty_distribution(conn: Connection, song_id, level) -> [(int, int)]:
    cursor = conn.cursor()
    user_plays = cursor.execute(
        "SELECT user_id, score FROM top_plays WHERE song_id=? and level_id=?;",
        (song_id, level)
    ).fetchall()
    elo_plays = []
    for user_id, top_score in user_plays:
        user_elo = cursor.execute(
            "SELECT elo{0} FROM users WHERE user_id=?".format(min(level, 4)),
            (user_id,)
        ).fetchone()
        elo_plays.append((user_elo[0], top_score))
    return elo_plays


def plot_elo_vs_scores(conn: Connection, map_info: list[(int, int, str, str)]):
    cursor = conn.cursor()

    fig: Figure
    fig, ax = plt.subplots()

    for song_id, level, label, color in map_info:
        if label is None:
            label = cursor.execute(
                "SELECT song_name FROM songs WHERE song_id=?",
                (song_id,)
            ).fetchone()

        label += " (" + str(level) + ")"

        elos, scores = zip(*get_difficulty_distribution(conn, song_id, level))
        ax.scatter(elos, scores, label=label, c=color, alpha=0.5)

    ax.set_xlabel("ELO")
    ax.set_ylabel("Score")
    ax.legend()
    ax.grid(True)

    plt.show()


def random_color():
    hexadecimal_alphabets = '0123456789ABCDEF'
    return "#" + ''.join([random.choice(hexadecimal_alphabets) for j in range(6)])


