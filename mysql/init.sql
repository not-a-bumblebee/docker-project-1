CREATE DATABASE IF NOT EXISTS analytics_db;
USE analytics_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create course grades table
CREATE TABLE IF NOT EXISTS course_grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course VARCHAR(255) NOT NULL,
    grade FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


REVOKE ALL PRIVILEGES ON analytics_db.* FROM 'appuser'@'%';

GRANT SELECT, INSERT, UPDATE ON analytics_db.users         TO 'appuser'@'%';  -- auth service: log in, seed admin
GRANT SELECT, INSERT, UPDATE ON analytics_db.course_grades TO 'appuser'@'%';  -- web app inserts, analytics reads