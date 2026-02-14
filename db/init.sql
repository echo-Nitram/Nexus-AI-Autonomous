-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- The tables are created by SQLAlchemy on app startup (via init_db)
-- This script only handles extensions and custom functions

-- Create index function for vector similarity search
-- This will be applied after tables are created
DO $$
BEGIN
    -- Check if agent_thoughts table exists before creating index
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'agent_thoughts') THEN
        CREATE INDEX IF NOT EXISTS idx_agent_thoughts_embedding
        ON agent_thoughts USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    END IF;
END $$;
