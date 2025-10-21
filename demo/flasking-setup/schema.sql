CREATE DATABASE IF NOT EXISTS database;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    display_name VARCHAR(50), 
    email VARCHAR(100) NOT NULL UNIQUE,
    CONSTRAINT valid_email CHECK (email LIKE '%_@_%._%'), -- Basic email format validation
    password_hash VARCHAR(100) NOT NULL
);

-- sqlite3 database.db "read schema.sql"