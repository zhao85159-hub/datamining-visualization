-- =====================================================================
--  Web-Based LinkedIn Job Postings Analysis and Management System
--  MySQL 8.0 schema (normalised to Third Normal Form, utf8mb4)
--
--  This DDL is the production target described in the report.  For
--  zero-configuration development and the automated test-suite the same
--  SQLAlchemy models are materialised against SQLite (see app/config.py).
--  Apply with:  mysql -u root -p < schema.sql
-- =====================================================================
CREATE DATABASE IF NOT EXISTS linkedin_jobs
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE linkedin_jobs;

-- ---------------------------------------------------------------------
--  companies
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    company_id     BIGINT       NOT NULL,
    name           VARCHAR(255),
    description    TEXT,
    company_size   INT,
    country        VARCHAR(64),
    state          VARCHAR(128),
    city           VARCHAR(128),
    address        VARCHAR(255),
    url            VARCHAR(512),
    employee_count INT,
    follower_count INT,
    PRIMARY KEY (company_id),
    KEY ix_companies_name (name),
    KEY ix_companies_country (country)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  skills (controlled vocabulary / dataset taxonomy)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
    skill_abr  VARCHAR(16)  NOT NULL,
    skill_name VARCHAR(128),
    PRIMARY KEY (skill_abr),
    KEY ix_skills_name (skill_name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  postings (fact table)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS postings (
    job_id                     BIGINT       NOT NULL,
    title                      VARCHAR(512),
    description                TEXT,
    company_id                 BIGINT,
    location                   VARCHAR(255),
    min_salary                 FLOAT,
    med_salary                 FLOAT,
    max_salary                 FLOAT,
    normalized_salary          FLOAT,
    pay_period                 VARCHAR(32),
    currency                   VARCHAR(8),
    formatted_work_type        VARCHAR(64),
    formatted_experience_level VARCHAR(64),
    remote_allowed             TINYINT(1)   DEFAULT 0,
    views                      INT,
    applies                    INT,
    listed_time                DATETIME,
    job_category               VARCHAR(64),
    PRIMARY KEY (job_id),
    KEY ix_postings_title (title),
    KEY ix_postings_company (company_id),
    KEY ix_postings_location (location),
    KEY ix_postings_salary (normalized_salary),
    KEY ix_postings_work_type (formatted_work_type),
    KEY ix_postings_experience (formatted_experience_level),
    KEY ix_postings_remote (remote_allowed),
    KEY ix_postings_listed (listed_time),
    KEY ix_postings_category (job_category),
    FULLTEXT KEY ft_postings_text (title, description),
    CONSTRAINT fk_postings_company FOREIGN KEY (company_id)
        REFERENCES companies (company_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  job_skills (bridge table resolving the postings <-> skills M:N)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_skills (
    job_id    BIGINT      NOT NULL,
    skill_abr VARCHAR(16) NOT NULL,
    PRIMARY KEY (job_id, skill_abr),
    KEY ix_job_skills_skill (skill_abr),
    CONSTRAINT fk_js_job   FOREIGN KEY (job_id)    REFERENCES postings (job_id) ON DELETE CASCADE,
    CONSTRAINT fk_js_skill FOREIGN KEY (skill_abr) REFERENCES skills (skill_abr) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  company_specialities
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_specialities (
    id         INT          NOT NULL AUTO_INCREMENT,
    company_id BIGINT       NOT NULL,
    speciality VARCHAR(255),
    PRIMARY KEY (id),
    KEY ix_spec_company (company_id),
    CONSTRAINT fk_spec_company FOREIGN KEY (company_id)
        REFERENCES companies (company_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  users (authentication / RBAC)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INT         NOT NULL AUTO_INCREMENT,
    username      VARCHAR(64) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(16)  DEFAULT 'user',
    created_at    DATETIME,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB;
