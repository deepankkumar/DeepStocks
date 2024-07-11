import bcrypt
import json

USERS_FILE = "db/users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}
    return users

def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file)

def add_user(username, password):
    users = load_users()
    if username in users:
        return False
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = hashed_pw
    save_users(users)
    return True

def authenticate_user(username, password):
    users = load_users()
    if username in users and bcrypt.checkpw(password.encode(), users[username].encode()):
        return True
    return False
