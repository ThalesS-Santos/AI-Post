-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela central do motor RAG
CREATE TABLE IF NOT EXISTS embeddings_marca (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- O app usa um DEMO_CLIENT_ID fixo, então a FK para auth.users bloqueia o save.
    cliente_id      UUID NOT NULL,
    tipo            VARCHAR(50) NOT NULL CHECK (tipo IN ('regra_marca', 'produto')),
    texto_base      TEXT NOT NULL,
    url_imagem      VARCHAR(255) DEFAULT '',
    vetor_embedding VECTOR(768),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Índice HNSW para busca vetorial rápida (pula vizinhos improváveis)
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON embeddings_marca
    USING hnsw (vetor_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_embeddings_cliente_id
    ON embeddings_marca (cliente_id);

-- Função RPC: busca os N registros com maior similaridade de cosseno
CREATE OR REPLACE FUNCTION buscar_contexto_similar(
    cliente_uuid   UUID,
    query_embedding VECTOR(768),
    match_count    INT DEFAULT 3
)
RETURNS TABLE (
    id          UUID,
    tipo        VARCHAR(50),
    texto_base  TEXT,
    url_imagem  VARCHAR(255),
    similaridade FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.id,
        em.tipo,
        em.texto_base,
        em.url_imagem,
        1 - (em.vetor_embedding <=> query_embedding) AS similaridade
    FROM embeddings_marca em
    WHERE em.cliente_id = cliente_uuid
    ORDER BY em.vetor_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Row Level Security: cada usuário vê apenas seus dados
ALTER TABLE embeddings_marca ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_data"
    ON embeddings_marca FOR ALL
    USING (auth.uid() = cliente_id);

-- Auto-atualiza updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_embeddings_updated_at
    BEFORE UPDATE ON embeddings_marca
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Bucket para fotos de produtos (criar via dashboard ou CLI)
-- supabase storage create catalogo-produtos --public
