import getpass
import sys

from auth import hash_password
from database import get_db

def main():
    username = input("Admin username to update [owner]: ").strip() or "owner"
    pw1 = getpass.getpass("New password: ")
    pw2 = getpass.getpass("Confirm password: ")
    if pw1 != pw2:
        print("Passwords do not match")
        sys.exit(1)
    hashed = hash_password(pw1)
    with get_db() as db:
        cur = db.execute(
            "UPDATE admins SET password_hash = ? WHERE username = ?",
            (hashed, username),
        )
        if cur.rowcount == 0:
            db.execute(
                "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
                (username, hashed),
            )
            print(f"Inserted new admin '{username}'")
        else:
            print(f"Password updated for '{username}'")

if __name__ == "__main__":
    main()