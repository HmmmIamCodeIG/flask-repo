CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT
); 

CREATE TABLE IF NOT EXISTS ProgressLogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    image_path TEXT
);

CREATE TABLE IF NOT EXISTS TestResults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    date TEXT NOT NULL
);

-- sqlite3 database.db ".read schema.sql"