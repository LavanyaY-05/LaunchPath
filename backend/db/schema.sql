-- LaunchPath Supabase Database Schema
-- Run this SQL in your Supabase SQL Editor to initialize pgvector & the documents table.

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table for storing chunked content and embeddings
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  domain TEXT NOT NULL,
  category TEXT,
  source_title TEXT NOT NULL,
  source_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, NOW()) NOT NULL
);

-- Full-text search GIN index
CREATE INDEX IF NOT EXISTS documents_fts_idx ON documents USING gin(to_tsvector('english', content));

-- Cosine vector index (HNSW for fast similarity search)
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents USING hnsw (embedding vector_cosine_ops);

-- Hybrid search function combining Vector Cosine Similarity and Postgres Full-Text Search via RRF
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 5,
  filter_domain TEXT DEFAULT NULL,
  rrf_k INT DEFAULT 60
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  domain TEXT,
  category TEXT,
  source_title TEXT,
  source_url TEXT,
  similarity FLOAT,
  fts_rank FLOAT,
  rrf_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH vector_matches AS (
    SELECT
      d.id,
      d.content,
      d.domain,
      d.category,
      d.source_title,
      d.source_url,
      1 - (d.embedding <=> query_embedding) AS similarity,
      ROW_NUMBER() OVER (ORDER BY d.embedding <=> query_embedding) AS v_rank
    FROM documents d
    WHERE (filter_domain IS NULL OR d.domain = filter_domain)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  fts_matches AS (
    SELECT
      d.id,
      d.content,
      d.domain,
      d.category,
      d.source_title,
      d.source_url,
      ts_rank_cd(to_tsvector('english', d.content), websearch_to_tsquery('english', query_text)) AS fts_rank,
      ROW_NUMBER() OVER (ORDER BY ts_rank_cd(to_tsvector('english', d.content), websearch_to_tsquery('english', query_text)) DESC) AS f_rank
    FROM documents d
    WHERE (filter_domain IS NULL OR d.domain = filter_domain)
      AND to_tsvector('english', d.content) @@ websearch_to_tsquery('english', query_text)
    ORDER BY fts_rank DESC
    LIMIT match_count * 2
  ),
  combined AS (
    SELECT
      coalesce(v.id, f.id) AS id,
      coalesce(v.content, f.content) AS content,
      coalesce(v.domain, f.domain) AS domain,
      coalesce(v.category, f.category) AS category,
      coalesce(v.source_title, f.source_title) AS source_title,
      coalesce(v.source_url, f.source_url) AS source_url,
      coalesce(v.similarity, 0.0) AS similarity,
      coalesce(f.fts_rank, 0.0) AS fts_rank,
      (coalesce(1.0 / (rrf_k + v.v_rank), 0.0) + coalesce(1.0 / (rrf_k + f.f_rank), 0.0)) AS rrf_score
    FROM vector_matches v
    FULL OUTER JOIN fts_matches f ON v.id = f.id
  )
  SELECT
    c.id,
    c.content,
    c.domain,
    c.category,
    c.source_title,
    c.source_url,
    c.similarity,
    c.fts_rank,
    c.rrf_score
  FROM combined c
  ORDER BY c.rrf_score DESC
  LIMIT match_count;
END;
$$;
