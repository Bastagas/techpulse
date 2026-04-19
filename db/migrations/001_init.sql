-- ─────────────────────────────────────────────────────────────
-- TechPulse — Migration 001 : schéma initial
-- Cible : MySQL 8.0+
-- ─────────────────────────────────────────────────────────────

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET foreign_key_checks = 0;

-- ───────── Table : companies ─────────
CREATE TABLE IF NOT EXISTS companies (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(255)  NOT NULL,
    slug            VARCHAR(255)  UNIQUE,
    website         VARCHAR(500)  NULL,
    sector          VARCHAR(100)  NULL,
    size_range      VARCHAR(50)   NULL,
    city            VARCHAR(100)  NULL,
    lat             DECIMAL(9, 6) NULL,
    lng             DECIMAL(9, 6) NULL,
    logo_url        VARCHAR(500)  NULL,
    first_seen_at   DATETIME      NULL,
    last_seen_at    DATETIME      NULL,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_companies_name (name),
    INDEX idx_companies_city (city)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ───────── Table : technologies (référentiel canonique) ─────────
CREATE TABLE IF NOT EXISTS technologies (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    canonical_name  VARCHAR(100) UNIQUE NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    category        ENUM('language','framework','database','cloud','tool','library','methodology') NOT NULL,
    aliases         JSON NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tech_category (category)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ───────── Table : offers ─────────
CREATE TABLE IF NOT EXISTS offers (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    company_id          BIGINT NOT NULL,
    source              ENUM('france_travail','hellowork','apec','wttj') NOT NULL,
    source_offer_id     VARCHAR(255) NOT NULL,
    source_url          VARCHAR(1000) NOT NULL,
    title               VARCHAR(500)  NOT NULL,
    description         TEXT          NULL,
    description_html    MEDIUMTEXT    NULL,
    contract_type       VARCHAR(50)   NULL,
    experience_level    VARCHAR(50)   NULL,
    remote_policy       VARCHAR(50)   NULL,
    salary_min          INT           NULL,
    salary_max          INT           NULL,
    salary_currency     CHAR(3)       DEFAULT 'EUR',
    city                VARCHAR(100)  NULL,
    department_code     VARCHAR(5)    NULL,
    lat                 DECIMAL(9, 6) NULL,
    lng                 DECIMAL(9, 6) NULL,
    posted_at           DATETIME      NULL,
    scraped_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,
    fingerprint         CHAR(64)      NOT NULL,
    is_active           BOOLEAN       DEFAULT TRUE,
    created_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_offers_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE RESTRICT,
    UNIQUE KEY uq_offers_source (source, source_offer_id),
    INDEX idx_offers_fingerprint (fingerprint),
    INDEX idx_offers_posted (posted_at),
    INDEX idx_offers_city (city),
    INDEX idx_offers_active (is_active),
    FULLTEXT KEY ft_offers_title_desc (title, description)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ───────── Table : offer_technologies (N↔N avec score) ─────────
CREATE TABLE IF NOT EXISTS offer_technologies (
    offer_id            BIGINT      NOT NULL,
    technology_id       INT         NOT NULL,
    confidence_score    DECIMAL(3, 2) DEFAULT 1.00,
    extracted_by        VARCHAR(20) DEFAULT 'regex',
    PRIMARY KEY (offer_id, technology_id),
    CONSTRAINT fk_ot_offer      FOREIGN KEY (offer_id)      REFERENCES offers(id)       ON DELETE CASCADE,
    CONSTRAINT fk_ot_technology FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE CASCADE,
    INDEX idx_ot_technology (technology_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ───────── Table : scrape_runs (traçabilité) ─────────
CREATE TABLE IF NOT EXISTS scrape_runs (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    spider          VARCHAR(50) NOT NULL,
    started_at      DATETIME    NOT NULL,
    finished_at     DATETIME    NULL,
    status          ENUM('running','success','partial','failed') NOT NULL DEFAULT 'running',
    pages_fetched   INT         DEFAULT 0,
    offers_found    INT         DEFAULT 0,
    offers_new      INT         DEFAULT 0,
    offers_updated  INT         DEFAULT 0,
    errors_count    INT         DEFAULT 0,
    error_log       TEXT        NULL,
    INDEX idx_runs_spider_date (spider, started_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

SET foreign_key_checks = 1;
