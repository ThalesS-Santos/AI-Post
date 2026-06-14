-- Compatibilidade para bancos que já aplicaram a migração antiga.
-- Remove a FK que impede o uso do DEMO_CLIENT_ID no fluxo de setup.
ALTER TABLE IF EXISTS embeddings_marca
    DROP CONSTRAINT IF EXISTS embeddings_marca_cliente_id_fkey;
