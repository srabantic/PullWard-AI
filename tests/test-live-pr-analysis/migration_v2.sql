-- ==============================================================================
-- Migration Script: Database Schema Cleanup (High Risk Test)
-- ==============================================================================

-- Safe operation: create table
CREATE TABLE IF NOT EXISTS new_audit_records (
    id SERIAL PRIMARY KEY,
    details TEXT NOT NULL
);

-- ❌ 1. Destructive DROP TABLE Statement
DROP TABLE legacy_user_accounts;

-- ❌ 2. Destructive DROP COLUMN Statement
ALTER TABLE customer_profiles DROP COLUMN billing_address;

-- ❌ 3. Destructive DROP DATABASE Statement
DROP DATABASE staging_environment_db;

-- ❌ 4. Destructive DROP INDEX Statement
DROP INDEX idx_customer_email;
