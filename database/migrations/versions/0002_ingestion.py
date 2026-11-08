"""Create provenance and immutable patent document versions."""

from alembic import op

revision = "0002_ingestion"
down_revision = "0001_enable_vector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE source_datasets (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            dataset_key text NOT NULL UNIQUE,
            name text NOT NULL,
            publisher text NOT NULL,
            official_url text,
            license_notes text,
            checked_at timestamptz NOT NULL,
            is_demo boolean NOT NULL
        )
    """)
    op.execute("""
        CREATE TABLE ingestion_batches (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            dataset_id uuid NOT NULL REFERENCES source_datasets(id),
            batch_key text NOT NULL,
            checksum text NOT NULL CHECK (checksum ~ '^[0-9a-f]{64}$'),
            parser_version text NOT NULL,
            status text NOT NULL CHECK (status IN ('processing', 'complete', 'partial', 'failed')),
            counts_jsonb jsonb NOT NULL DEFAULT '{}',
            started_at timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz,
            UNIQUE (dataset_id, batch_key, checksum, parser_version)
        )
    """)
    op.execute("""
        CREATE TABLE ingestion_artifacts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            batch_id uuid NOT NULL REFERENCES ingestion_batches(id),
            source_locator text NOT NULL,
            checksum text NOT NULL CHECK (checksum ~ '^[0-9a-f]{64}$'),
            object_key text NOT NULL,
            size_bytes bigint NOT NULL CHECK (size_bytes >= 0),
            status text NOT NULL CHECK (status IN ('parsed', 'partial', 'quarantined')),
            error_log text,
            UNIQUE (batch_id, source_locator)
        )
    """)
    op.execute("""
        CREATE TABLE patent_applications (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            jurisdiction text NOT NULL,
            application_no text NOT NULL,
            filing_date date,
            UNIQUE (jurisdiction, application_no)
        )
    """)
    op.execute("""
        CREATE TABLE patent_documents (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id uuid NOT NULL REFERENCES patent_applications(id),
            jurisdiction text NOT NULL,
            publication_no text NOT NULL,
            kind_code text NOT NULL,
            document_stage text NOT NULL CHECK (document_stage IN ('publication', 'grant')),
            publication_date date,
            title_zh text,
            title_en text,
            abstract_zh text,
            abstract_en text,
            metadata_jsonb jsonb NOT NULL DEFAULT '{}',
            source_hash text NOT NULL CHECK (source_hash ~ '^[0-9a-f]{64}$'),
            parser_version text NOT NULL,
            UNIQUE (jurisdiction, document_stage, publication_no, kind_code, source_hash, parser_version)
        )
    """)
    op.execute("""
        CREATE TABLE document_artifacts (
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            artifact_id uuid NOT NULL REFERENCES ingestion_artifacts(id),
            record_locator text NOT NULL,
            PRIMARY KEY (document_id, artifact_id, record_locator)
        )
    """)
    op.execute("""
        CREATE TABLE patent_classifications (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            scheme text NOT NULL,
            code text NOT NULL,
            version text NOT NULL DEFAULT '',
            UNIQUE (document_id, scheme, code, version)
        )
    """)
    op.execute("""
        CREATE TABLE patent_sections (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            section_type text NOT NULL,
            ordinal integer NOT NULL CHECK (ordinal >= 1),
            original_text text NOT NULL,
            source_locator_jsonb jsonb NOT NULL,
            UNIQUE (document_id, section_type, ordinal)
        )
    """)
    op.execute("""
        CREATE TABLE patent_claims (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            claim_number integer NOT NULL CHECK (claim_number >= 1),
            text text NOT NULL,
            independent_flag_nullable boolean,
            source_locator_jsonb jsonb NOT NULL,
            UNIQUE (document_id, claim_number)
        )
    """)
    op.create_index(
        "ix_patent_documents_application", "patent_documents", ["application_id"]
    )
    op.create_index(
        "ix_patent_documents_number", "patent_documents", ["publication_no"]
    )
    op.create_index(
        "ix_patent_documents_publication_date", "patent_documents", ["publication_date"]
    )
    op.create_index(
        "ix_patent_classifications_lookup", "patent_classifications", ["scheme", "code"]
    )
    op.create_index(
        "ix_document_artifacts_artifact", "document_artifacts", ["artifact_id"]
    )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade would discard imported data; preserve the ingestion schema."
    )
