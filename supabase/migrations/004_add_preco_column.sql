-- Adiciona a coluna preco para armazenar o preço dos produtos
ALTER TABLE embeddings_marca ADD COLUMN IF NOT EXISTS preco VARCHAR(50) DEFAULT '';
