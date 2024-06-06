-- setup.sql
CREATE TABLE vectors (
    id SERIAL PRIMARY KEY,
    vector vector,  -- Using 'vector' type from pgvector
    metadata JSONB
);