import os
import sqlite3
import hashlib
import hmac

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_player.db")
ITERATIONS = 600_000


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
    
def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE (user_id, name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            playlist_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            PRIMARY KEY (playlist_id, path),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()



def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    ).hex()

def register_user(username, password):
    username = username.strip()
    if not username: 
        return False, "Username cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    salt = os.urandom(16)
    password_hash = hash_password(password, salt)

    conn = get_connection()
    try: 
        conn.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt.hex()),
        )
        conn.commit()
        return True, "Account created"
    except sqlite3.IntegrityError:
        return False, "Username already taken"
    finally:
        conn.close()

def verify_user(username, password):
    username = username.strip()

    conn = get_connection()
    try: 
        row = conn.execute(
            "SELECT password_hash, salt FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return False, "Invalid username or password"

    stored_hash, stored_salt = row
    attempt = hash_password(password, bytes.fromhex(stored_salt))

    if hmac.compare_digest(attempt, stored_hash):
        return True, "Login successful"
    return False, "Invalid username or password"

if __name__ == "__main__":
    init_db()
    print(register_user("testuser", "secret123"))   # expect True
    print(register_user("testuser", "secret123"))   # expect False (taken)
    print(register_user("", "secret123"))           # expect False (empty)
    print(register_user("bob", "123"))              # expect False (too short)
    print(verify_user("testuser", "secret123"))     # expect True
    print(verify_user("testuser", "wrongpass"))     # expect False
    print(verify_user("nobody", "secret123"))       # expect False

def get_user_id(username):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def add_favorite(user_id, path):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO favorites (user_id, path) VALUES (?, ?)",
            (user_id, path),
        )
        conn.commit()
    finally:
        conn.close()


def remove_favorite(user_id, path):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND path = ?",
            (user_id, path),
        )
        conn.commit()
    finally:
        conn.close()


def get_favorites(user_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT path FROM favorites WHERE user_id = ?", (user_id,)
        ).fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows}

def create_playlist(user_id, name):
    name = name.strip()
    if not name:
        return False, "Playlist name cannot be empty"
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO playlists (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
        conn.commit()
        return True, cursor.lastrowid
    except sqlite3.IntegrityError:
        return False, "You already have a playlist with that name"
    finally:
        conn.close()


def rename_playlist(user_id, playlist_id, new_name):
    new_name = new_name.strip()
    if not new_name:
        return False, "Playlist name cannot be empty"
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE playlists SET name = ? WHERE id = ? AND user_id = ?",
            (new_name, playlist_id, user_id),
        )
        conn.commit()
        return True, "Renamed"
    except sqlite3.IntegrityError:
        return False, "You already have a playlist with that name"
    finally:
        conn.close()


def delete_playlist(user_id, playlist_id):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM playlists WHERE id = ? AND user_id = ?",
            (playlist_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_playlists(user_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, name FROM playlists WHERE user_id = ? "
            "ORDER BY name COLLATE NOCASE",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()


def add_track_to_playlist(user_id, playlist_id, path):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO playlist_tracks (playlist_id, path) "
            "SELECT id, ? FROM playlists WHERE id = ? AND user_id = ?",
            (path, playlist_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def remove_track_from_playlist(user_id, playlist_id, path):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND path = ? "
            "AND playlist_id IN (SELECT id FROM playlists WHERE user_id = ?)",
            (playlist_id, path, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_playlist_paths(user_id, playlist_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT path FROM playlist_tracks WHERE playlist_id = ? "
            "AND playlist_id IN (SELECT id FROM playlists WHERE user_id = ?)",
            (playlist_id, user_id),
        ).fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows]