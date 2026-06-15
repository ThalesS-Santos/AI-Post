-- Cria uma função RPC específica para buscar apenas produtos relevantes (evitando misturar regras da marca)
CREATE OR REPLACE FUNCTION buscar_produtos_similares(
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
    WHERE em.cliente_id = cliente_uuid AND em.tipo = 'produto'
    ORDER BY em.vetor_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
