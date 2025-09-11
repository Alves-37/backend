-- Adicionar coluna usuario_id à tabela vendas
ALTER TABLE vendas ADD COLUMN usuario_id UUID;

-- Adicionar foreign key constraint
ALTER TABLE vendas ADD CONSTRAINT fk_vendas_usuario_id 
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id);

-- Criar índice para melhor performance
CREATE INDEX idx_vendas_usuario_id ON vendas(usuario_id);

-- Comentário explicativo
COMMENT ON COLUMN vendas.usuario_id IS 'ID do usuário que realizou a venda';
