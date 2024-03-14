import numpy as np


def generate_elos(conn):
    cursor = conn.cursor()
    users = cursor.execute("SELECT user_id, user_name FROM users;").fetchall()

    songs = cursor.execute("SELECT song_id, song_name_jap FROM songs;").fetchall()

    for level_id in range(1, 5):

        user_score_pps = {}
        for (user_id, user_name) in users:
            user_score_pps[user_id] = []

        # get predicted and actual win probabilities
        for (song_id, song_name) in songs:
            calculate_song_pp(cursor, level_id, song_id, user_score_pps)
            # also include ura oni. if song doesn't exist there will be no plays for it
            if level_id == 4:
                calculate_song_pp(cursor, level_id, song_id, user_score_pps, is_ura=True)

        user_total_pps = {}
        for (user_id, user_name) in users:
            user_total_pps[user_id] = 0.

        # find the total pps
        for user_id in user_total_pps:
            user_total_pps[user_id] = calculate_total_pp(user_score_pps[user_id])

        values_list = list(filter(lambda val: val is not None, list(user_total_pps.values())))

        mean = np.mean(values_list)
        sd = np.std(values_list)
        print(f"mean {mean} sd {sd}")

        for user_id in user_total_pps:
            pp = user_total_pps[user_id]
            elo = None
            if pp is not None:
                z_value = (user_total_pps[user_id] - mean) / sd
                elo = 1000 + (z_value * 200 * (2**0.5))
            cursor.execute("UPDATE users SET elo" + str(level_id) + " = ? WHERE user_id = ?;",
                           (elo, user_id))

    # for (user_id, user_name) in users:
    #     elo = user_elos[user_id][3]
    #     print(user_name + ": " + str(elo))

    conn.commit()


def calculate_song_pp(cursor, level_id, song_id, user_song_pps, is_ura=False):
    top_plays: list = cursor.execute(
        "SELECT * FROM top_plays WHERE song_id=" + str(song_id) + " and level_id=" + str(level_id + int(is_ura)) + ";").fetchall()
    # plays below 2 won't be included anyways. below 4 are too unpredictable
    top_plays.sort(key=lambda play: play[3])
    # get the expected win probability based on elo and position
    for (i, user) in enumerate(top_plays):
        for opponent in top_plays:
            if user == opponent: continue
        win_probability_position = i / float(len(top_plays))
        user_song_pps[user[0]].append(win_probability_position)


def calculate_total_pp(scores: list[float]):
    if len(scores) < 3:
        return None
    scores.sort(key=lambda x: -x)  # sort largest to smallest
    final_score = 0
    for (i, score) in enumerate(scores):
        weighting = pow(0.95, i)
        final_score += score * weighting
    return final_score
