from dataclasses import dataclass
from sqlite3 import Connection
import wcwidth

def get_scoreboard_data(conn: Connection, song_id, level_id):
    song_name_jap, song_name_eng = conn.execute(
        "SELECT song_name_jap, song_name_eng FROM songs where song_id=?",
        (song_id,)
    ).fetchone()

    top_plays = conn.execute(
        "SELECT user_id, score FROM top_plays WHERE song_id = ? and level_id=?",
        (song_id,level_id)
    )
    scoreboard = []
    for user_id, score in top_plays:
        user_name, = conn.execute("SELECT user_name FROM users WHERE user_id=?", (user_id,)).fetchone()
        scoreboard.append(ScoreboardEntry(
            user_id,
            user_name,
            score
        ))
    scoreboard = sorted(scoreboard, key=lambda entry: -entry.score)
    print(f"Leaderboard for {song_name_eng} ({song_name_jap}, lvl {level_id}):")
    for i, score in enumerate(scoreboard, start=1):
        print(f"#{i:>2}) {left_pad(score.user_name, 12)} | {score.score:<7}")

@dataclass
class ScoreboardEntry:
    user_id: int
    user_name: str
    score: int


def left_pad(text, length):
    size = wcwidth.wcswidth(text)
    return ' ' * (length-size) + text
