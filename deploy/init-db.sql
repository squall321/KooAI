-- KooAI Database Initialization Script
-- PostgreSQL 16 with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS kooai;

-- Set search path
SET search_path TO kooai, public;

-- Create simulation_results table
CREATE TABLE IF NOT EXISTS simulation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    simulation_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',

    -- Indexes
    CONSTRAINT simulation_results_name_key UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS idx_simulation_results_created_at
    ON simulation_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_simulation_results_type
    ON simulation_results(simulation_type);
CREATE INDEX IF NOT EXISTS idx_simulation_results_metadata
    ON simulation_results USING gin(metadata);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_simulation_results_updated_at
    BEFORE UPDATE ON simulation_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA kooai TO kooai;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA kooai TO kooai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA kooai TO kooai;

-- Insert sample data (optional, for testing)
-- INSERT INTO simulation_results (name, simulation_type, metadata)
-- VALUES ('sample_simulation', 'CFD', '{"description": "Sample CFD simulation"}');

-- Display initialization result
DO $$
BEGIN
    RAISE NOTICE 'KooAI database initialized successfully!';
    RAISE NOTICE 'Schema: kooai';
    RAISE NOTICE 'Tables created: simulation_results';
END $$;
