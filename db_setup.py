import sqlite3

def create_demo_db(path="example.db"):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS orders;

    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        created_at TEXT
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    INSERT INTO users (name, email, created_at) VALUES
      ('Alice','alice@example.com','2024-01-01'),
      ('Bob','bob@example.com','2024-02-10'),
      ('Eve','eve@example.com','2024-03-12');

    INSERT INTO orders (user_id, amount, status, created_at) VALUES
      (1, 99.95, 'paid', '2024-03-01'),
      (2, 24.50, 'pending','2024-04-02'),
      (1, 13.20, 'refunded','2024-05-03');
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_demo_db()
    print("Created example.db with demo tables")
