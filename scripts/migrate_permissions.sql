-- Adds missing permission/aux columns to usuarios table if they do not exist
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nivel INTEGER DEFAULT 1;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS salario DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS pode_abastecer BOOLEAN DEFAULT FALSE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS pode_gerenciar_despesas BOOLEAN DEFAULT FALSE;
