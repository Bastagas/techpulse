-- ─────────────────────────────────────────────────────────────
-- TechPulse — Migration 003 : table alerts
-- Alertes email : une offre correspond aux critères → envoyer mail
-- ─────────────────────────────────────────────────────────────

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alerts (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    email               VARCHAR(255) NOT NULL,
    token               CHAR(32) UNIQUE NOT NULL,       -- pour unsubscribe
    filter_keyword      VARCHAR(200) NULL,
    filter_city         VARCHAR(100) NULL,
    filter_tech         VARCHAR(100) NULL,              -- canonical_name
    filter_contract     VARCHAR(50)  NULL,
    filter_salary_min   INT          NULL,
    is_active           BOOLEAN      DEFAULT TRUE,
    created_at          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    last_notified_at    DATETIME     NULL,
    notification_count  INT          DEFAULT 0,
    last_offers_count   INT          DEFAULT 0,
    INDEX idx_alerts_email   (email),
    INDEX idx_alerts_active  (is_active),
    INDEX idx_alerts_token   (token)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
