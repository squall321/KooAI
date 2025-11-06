-- Initialize database for KooAI

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create uuid extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Print confirmation
DO $$
BEGIN
    RAISE NOTICE 'KooAI database initialized successfully';
END $$;
