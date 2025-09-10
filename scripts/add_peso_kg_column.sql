-- Adicionar coluna peso_kg se não existir
ALTER TABLE itens_venda ADD COLUMN IF NOT EXISTS peso_kg FLOAT DEFAULT 0.0;

-- Atualizar registros existentes
UPDATE itens_venda SET peso_kg = 0.0 WHERE peso_kg IS NULL;
