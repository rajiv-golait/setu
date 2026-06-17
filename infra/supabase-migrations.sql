-- DO NOT use alembic --sql output in the SQL Editor (it includes INFO log lines).
-- This file is the clean schema — same as supabase-schema.sql.
-- Run once in: Supabase Dashboard → SQL Editor → New query → Run

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

CREATE TABLE patients (
    id VARCHAR NOT NULL,
    display_name VARCHAR,
    lang_pref VARCHAR DEFAULT 'mr',
    patient_token VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE (patient_token)
);

CREATE TABLE documents (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    doc_type VARCHAR,
    storage_path VARCHAR NOT NULL,
    mime VARCHAR,
    source VARCHAR DEFAULT 'upload',
    status VARCHAR DEFAULT 'pending',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id)
);

CREATE TABLE extractions (
    id VARCHAR NOT NULL,
    document_id VARCHAR,
    provider VARCHAR,
    raw_json JSONB NOT NULL,
    overall_confidence NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(document_id) REFERENCES documents (id)
);

CREATE TABLE claims (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    document_id VARCHAR,
    claim_type VARCHAR NOT NULL,
    normalized_key VARCHAR NOT NULL,
    fields JSONB NOT NULL,
    confidence NUMERIC NOT NULL,
    observed_at DATE,
    needs_review BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id),
    FOREIGN KEY(document_id) REFERENCES documents (id)
);

CREATE INDEX ix_claims_grouping ON claims (patient_id, claim_type, normalized_key, observed_at);

CREATE TABLE current_truth (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    entry_type VARCHAR NOT NULL,
    normalized_key VARCHAR NOT NULL,
    value JSONB NOT NULL,
    confidence NUMERIC,
    state VARCHAR DEFAULT 'confirmed',
    source_claim_ids JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT uq_truth_entry UNIQUE (patient_id, entry_type, normalized_key),
    FOREIGN KEY(patient_id) REFERENCES patients (id)
);

CREATE TABLE briefs (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    brief_json JSONB NOT NULL,
    model VARCHAR,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id)
);

CREATE TABLE summaries (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    lang VARCHAR DEFAULT 'mr',
    summary_json JSONB NOT NULL,
    model VARCHAR,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id)
);

CREATE TABLE shares (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    token VARCHAR NOT NULL,
    snapshot_json JSONB NOT NULL,
    view_count INTEGER DEFAULT '0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id),
    UNIQUE (token)
);

CREATE TABLE referrals (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    brief_id VARCHAR,
    specialty VARCHAR NOT NULL,
    reason VARCHAR,
    snapshot_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id),
    FOREIGN KEY(brief_id) REFERENCES briefs (id)
);

INSERT INTO alembic_version (version_num) VALUES ('0001');

ALTER TABLE patients ADD COLUMN telegram_chat_id VARCHAR;
ALTER TABLE patients ADD CONSTRAINT uq_patients_telegram_chat_id UNIQUE (telegram_chat_id);
UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

CREATE TABLE consents (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    purpose VARCHAR NOT NULL,
    consent_text VARCHAR NOT NULL,
    lang VARCHAR DEFAULT 'mr',
    channel VARCHAR DEFAULT 'web',
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id)
);
CREATE INDEX ix_consents_patient_purpose ON consents (patient_id, purpose);
UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

CREATE TABLE reminders (
    id VARCHAR NOT NULL,
    patient_id VARCHAR,
    reminder_type VARCHAR NOT NULL,
    label VARCHAR NOT NULL,
    schedule JSONB NOT NULL,
    source_claim_id VARCHAR,
    needs_confirmation BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id)
);
CREATE INDEX ix_reminders_patient ON reminders (patient_id);
UPDATE alembic_version SET version_num='0004' WHERE alembic_version.version_num = '0003';

ALTER TABLE documents ADD COLUMN original_hash VARCHAR;
ALTER TABLE documents ADD COLUMN purged_at TIMESTAMP WITH TIME ZONE;
UPDATE alembic_version SET version_num='0005' WHERE alembic_version.version_num = '0004';

ALTER TABLE patients ADD COLUMN supabase_user_id VARCHAR;
CREATE UNIQUE INDEX ix_patients_supabase_user_id ON patients (supabase_user_id);
UPDATE alembic_version SET version_num='0006' WHERE alembic_version.version_num = '0005';

COMMIT;
