-- Adicionar campos de IVA na tabela de produtos
ALTER TABLE produtos
  ADD COLUMN IF NOT EXISTS taxa_iva double precision DEFAULT 0,
  ADD COLUMN IF NOT EXISTS codigo_imposto varchar(20);

-- Adicionar campos de IVA na tabela itens_venda
ALTER TABLE itens_venda
  ADD COLUMN IF NOT EXISTS taxa_iva double precision DEFAULT 0,
  ADD COLUMN IF NOT EXISTS base_iva double precision DEFAULT 0,
  ADD COLUMN IF NOT EXISTS valor_iva double precision DEFAULT 0;
