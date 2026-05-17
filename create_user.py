import sys
import os
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = os.environ.get('DATABASE_URL', os.path.join(os.path.dirname(__file__), 'data', 'fi_tracker.db'))

def get_db():
    return sqlite3.connect(DATABASE)

def main():
    if len(sys.argv) < 4:
        print(f"Usage: python3 {sys.argv[0]} <email> <name> <password> [role]")
        sys.exit(1)
        
    email = sys.argv[1]
    name = sys.argv[2]
    password = sys.argv[3]
    role = sys.argv[4] if len(sys.argv) > 4 else 'user'
    
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)',
            (email, name, password_hash, role)
        )
        conn.commit()
        print(f"Successfully created user: {name} ({email}) with role '{role}'")
    except sqlite3.IntegrityError:
        print(f"Error: User with email {email} already exists.")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
