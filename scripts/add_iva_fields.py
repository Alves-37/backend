import psycopg2

DATABASE_URL = "postgresql://postgres:yjZJwfkbcNTlNUNQUjbHoRpUtVtGVkpQ@gondola.proxy.rlwy.net:20145/railway"

def add_iva_fields():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        sql = """
        -- Adicionar campos de IVA na tabela de produtos
        ALTER TABLE produtos
          ADD COLUMN IF NOT EXISTS taxa_iva DOUBLE PRECISION DEFAULT 0,
          ADD COLUMN IF NOT EXISTS codigo_imposto VARCHAR(20);

        -- Adicionar campos de IVA na tabela itens_venda
        ALTER TABLE itens_venda
          ADD COLUMN IF NOT EXISTS taxa_iva DOUBLE PRECISION DEFAULT 0,
          ADD COLUMN IF NOT EXISTS base_iva DOUBLE PRECISION DEFAULT 0,
          ADD COLUMN IF NOT EXISTS valor_iva DOUBLE PRECISION DEFAULT 0;
        """

        cursor.execute(sql)
        conn.commit()

        print("✔ Campos de IVA adicionados com sucesso (produtos e itens_venda).")

    except Exception as e:
        print("❌ Erro ao adicionar campos de IVA:", e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    add_iva_fields()
