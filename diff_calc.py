from sqlite3 import Connection

import numpy
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
    elo_plays = list(filter(lambda elo_play: elo_play[0] is not None, elo_plays))
    return elo_plays


# noinspection PyTupleAssignmentBalance
def get_song_stats(conn: Connection, song_id, level):
    difficult_distribution = get_difficulty_distribution(conn, song_id, level)
    if len(difficult_distribution) < 4: return None
    elos, scores = zip(*difficult_distribution)
    coeffs = numpy.polyfit(elos, scores, deg=1, full=False)
    (_,residuals,_,_,_) = numpy.polyfit(elos, scores, deg=1, full=True)
    diffs_squared = residuals[0]
    mean_score = numpy.mean(scores)
    scores_squared = sum(map(lambda score: (score - mean_score) ** 2, scores))
    r_squared = 1.0 - (diffs_squared / scores_squared)
    diff_slope = coeffs[0]
    miyabi_elo = (1000000 - coeffs[1]) / diff_slope
    return diff_slope, miyabi_elo, r_squared


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
        difficult_distribution = get_difficulty_distribution(conn, song_id, level)
        elos, scores = zip(*difficult_distribution)
        diff_slope, miyabi_elo, certainty = get_song_stats(conn, song_id, level)
        print("{:<25}: {} score/ELO, {} ELO, R^2 = {:.2f}".format(label, str(int(diff_slope)).zfill(4), int(miyabi_elo), certainty))
        ax.scatter(elos, scores, label=label, c=color, alpha=0.5)

    ax.set_xlabel("ELO")
    ax.set_ylabel("Score")
    ax.legend()
    ax.grid(True)

    plt.show()


# noinspection PyTupleAssignmentBalance
def plot_scores_and_expected_scores(conn: Connection, user_id, level_id):
    top_plays = conn.execute(
        "SELECT song_id, level_id, score FROM top_plays WHERE user_id = ? and level_id=?",
        (user_id,level_id)
    ).fetchall()
    if level_id == 4:
        top_plays += conn.execute(
            "SELECT song_id, level_id, score FROM top_plays WHERE user_id = ? and level_id=?",
            (user_id,5)
        )
    elo, = conn.execute(
        f"SELECT elo{min(level_id, 4)} FROM users where user_id = ?",
        (user_id,)
    ).fetchone()
    score_actual_estimate = []
    for song_id, level_id, score in top_plays:
        estimated_score = estimate_score(conn, song_id, level_id, elo)
        if estimated_score is None: continue
        score_actual_estimate.append((score, int(estimated_score)))

    score_actual, score_estimate = zip(*list(sorted(
        score_actual_estimate,
        key=lambda score_data: -score_data[0]
    )))

    coeffs = numpy.polyfit(score_actual, score_estimate, deg=1, full=False)
    (_,residuals,_,_,_) = numpy.polyfit(score_actual, score_estimate, deg=1, full=True)
    diffs_squared = residuals[0]
    mean_score = numpy.mean(score_estimate)
    scores_squared = sum(map(lambda score: (score - mean_score) ** 2, score_estimate))
    r_squared = 1.0 - (diffs_squared / scores_squared)
    sd = (diffs_squared / len(score_estimate)) ** 0.5
    print(f"score_estimate = {coeffs[0]} * score_actual + {coeffs[1]} (R^2 = {r_squared}), sd = {sd}")

    fig: Figure
    fig, ax = plt.subplots()
    ax.scatter(score_estimate, score_actual, alpha=0.5)

    ax.set_xlabel("actual score")
    ax.set_ylabel("estimated score")
    ax.legend()
    ax.grid(True)

    plt.show()


def estimate_score(conn: Connection, song_id, level_id, elo):
    song_stats = get_song_stats(conn, song_id, level_id)
    if song_stats is None: return None

    diff_slope, miyabi_elo, certainty = song_stats
    return diff_slope * (elo - miyabi_elo) + 1000000




def random_color():
    hexadecimal_alphabets = '0123456789ABCDEF'
    return "#" + ''.join([random.choice(hexadecimal_alphabets) for j in range(6)])


