
def generate_elos(conn):
    cursor = conn.cursor()
    users = cursor.execute("SELECT user_id, user_name FROM users;").fetchall()
    user_elos = {}
    default_elos = {
        1: 1000.0,
        2: 1000.0,
        3: 1000.0,
        4: 1000.0
    }
    default_scores = {
        1: 0,
        2: 0,
        3: 0,
        4: 0
    }
    for (user_id, user_name) in users:
        user_elos[user_id] = default_elos.copy()  # mean ranking of 1000

    songs = cursor.execute("SELECT * FROM songs;").fetchall()

    for level_id in range(1, 4):
        for tourney_index in range(1, 10):  # number of tournaments. elos update at the end
            max_delta = 0
            average_delta = 0

            # initialise elo based scores
            user_scores_elo = {}
            for (user_id, user_name) in users:
                user_scores_elo[user_id] = []  # no gain nor loss in score
            # initialise position based scores
            user_scores_position = {}
            for (user_id, user_name) in users:
                user_scores_position[user_id] = []  # no gain nor loss in score

            # get predicted and actual win probabilities
            for (song_id, song_name) in songs:
                top_plays: list = cursor.execute("SELECT * FROM top_plays WHERE song_id=" + str(song_id) + " and level_id=" + str(level_id) + ";").fetchall()
                # plays below 2 won't be included anyways. below 4 are too unpredictable
                top_plays.sort(key=lambda play: play[3])

                # get the expected win probability based on elo and position
                for (i, user) in enumerate(top_plays):
                    win_probability_elo = 0.0
                    for opponent in top_plays:
                        if user == opponent: continue
                        win_probability_elo += 1.0 / (1 + pow(10, (user_elos[opponent[0]][level_id] - user_elos[user[0]][level_id]) / 400.0))
                    win_probability_elo = win_probability_elo / float(len(top_plays))
                    user_scores_elo[user[0]].append(win_probability_elo)
                    win_probability_position = i / float(len(top_plays))
                    user_scores_position[user[0]].append(win_probability_position)

            # now update elo based on discrepancy
            for user_id in user_elos:
                user_score_position = calculate_performance(user_scores_position[user_id])
                user_score_elo = calculate_performance(user_scores_elo[user_id])
                user_delta = user_score_position - user_score_elo
                max_delta = max(max_delta, user_delta)
                average_delta += user_delta
                user_elos[user_id][level_id] += 25 * user_delta

                cursor.execute("UPDATE users SET elo" + str(level_id) + " = " \
                               + str(int(user_elos[user_id][level_id])) + " WHERE user_id = " + str(user_id) + ";")
                average_delta /= len(user_elos)

    for (user_id, user_name) in users:
        elo = user_elos[user_id][3]
        print(user_name + ": " + str(elo))

    conn.commit()


def calculate_performance(scores: list[float]):
    scores.sort(key=lambda x: -x)  # sort largest to smallest
    final_score = 0
    for (i, score) in enumerate(scores):
        weighting = 1  # pow(0.95, i)
        final_score += score * weighting
    return final_score
