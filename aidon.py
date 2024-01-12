import os

from paramiko import SSHClient, AutoAddPolicy


def get_aidon_user_ids():

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(os.environ["AIDON_URL"], username='ubuntu', key_filename='./res/aidon.pem')
    stdin, stdout, stderr = client.exec_command(
        "cd ai_don_discord_py; sqlite3 discordUserData.db 'select donder_id from userData'"
    )

    # Print output of command. Will wait for command to finish.
    user_id_strings = stdout.read().decode("utf-8").split('\n')[:-1]
    user_ids = []
    for user_id_string in user_id_strings:
        user_ids.append(int(user_id_string))

    # Because they are file objects, they need to be closed
    stdin.close()
    stdout.close()
    stderr.close()

    # Close the client itself
    client.close()
    return user_ids


if __name__ == "__main__":
    user_ids = get_aidon_user_ids()
