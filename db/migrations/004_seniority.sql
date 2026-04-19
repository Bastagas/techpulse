-- Migration 004 : ajout colonne seniority (junior/mid/senior/lead)

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Idempotent : ne rajoute pas la colonne si elle existe déjà
SET @col_exists = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'offers' AND column_name = 'seniority'
);

SET @query = IF(@col_exists = 0,
    'ALTER TABLE offers ADD COLUMN seniority VARCHAR(20) NULL, ADD INDEX idx_offers_seniority (seniority)',
    'SELECT "seniority column already exists" AS info');

PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
