-- Convert 'estoque' and 'estoque_minimo' to double precision (float)
-- Safe for re-run: USING is idempotent if already double precision
ALTER TABLE produtos ALTER COLUMN estoque TYPE double precision USING estoque::double precision;
ALTER TABLE produtos ALTER COLUMN estoque_minimo TYPE double precision USING estoque_minimo::double precision;

-- Ensure itens_venda has peso_kg as double precision (idempotent)
ALTER TABLE itens_venda ADD COLUMN IF NOT EXISTS peso_kg double precision DEFAULT 0;
