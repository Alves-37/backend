import psycopg2

DATABASE_URL = "postgresql://postgres:yjZJwfkbcNTlNUNQUjbHoRpUtVtGVkpQ@gondola.proxy.rlwy.net:20145/railway"

def add_column():
    try:
        # Conectar ao banco
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Script SQL para adicionar a coluna
        sql = """
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS pode_fazer_devolucao BOOLEAN DEFAULT FALSE;
        """

        cursor.execute(sql)
        conn.commit()

        print("✔ Coluna 'pode_fazer_devolucao' adicionada (ou já existia).")

    except Exception as e:
        print("❌ Erro ao adicionar coluna:", e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    add_column()
