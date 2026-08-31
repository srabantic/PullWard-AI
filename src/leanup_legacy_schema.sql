-- Migration: Cleanup Legacy Tables
-- Target Version: 3.0.0

-- BREAKING CHANGE: Destructive DROP TABLE statement!
DROP TABLE user_sessions;

-- Another potential break:
DROP TABLE user_guilds;

CREATE TABLE active_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);