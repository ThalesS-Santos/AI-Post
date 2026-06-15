-- Migration 005: Adiciona coluna metadata para salvar dados estruturados de setup da marca
ALTER TABLE embeddings_marca
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
