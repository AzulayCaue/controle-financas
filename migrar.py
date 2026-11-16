import sqlite3
from pathlib import Path

PASTA = Path(__file__).parent
DB = PASTA / "financas.db"
BACKUP = PASTA / "financas_backup.db"

# Normaliza o texto da categoria: minúsculo, sem espaços nas pontas,
# e vazio/NULL vira "sem categoria".
NORMALIZA = "COALESCE(NULLIF(LOWER(TRIM({col})), ''), 'sem categoria')"


def colunas(con, tabela):
    # PRAGMA table_info devolve (cid, nome, tipo, notnull, default, pk)
    return [linha[1] for linha in con.execute(f"PRAGMA table_info({tabela})")]


def migrar():
    if not DB.exists():
        print("financas.db não existe: nada para migrar (o app.py cria o banco novo).")
        return
    if not BACKUP.exists():
        print("Backup não encontrado. Rode antes, no terminal:")
        print("  copy financas.db financas_backup.db")
        return

    # isolation_level=None: eu controlo a transação na mão (BEGIN/COMMIT/ROLLBACK)
    con = sqlite3.connect(DB, isolation_level=None)
    try:
        cols = colunas(con, "gastos")
        if not cols:
            print("Tabela gastos não existe: nada para migrar.")
            return
        if "categoria_id" in cols:
            print("Banco já está no esquema novo. Nada a fazer.")
            return
        if "categoria" not in cols:
            print(f"Esquema inesperado em gastos: {cols}")
            return

        # Precisa ser ANTES do BEGIN: dentro de uma transação esse PRAGMA é ignorado.
        con.execute("PRAGMA foreign_keys = OFF")
        con.execute("BEGIN")
        try:
            antes = con.execute("SELECT COUNT(*) FROM gastos").fetchone()[0]

            # 1) tabela de categorias
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                )
                """
            )

            # 2) uma linha por categoria distinta que já existe nos gastos
            con.execute(
                f"""
                INSERT OR IGNORE INTO categorias (nome)
                SELECT DISTINCT {NORMALIZA.format(col='categoria')} FROM gastos
                """
            )

            # 3) tabela gastos nova, já com a chave estrangeira
            con.execute(
                """
                CREATE TABLE gastos_novo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
                    valor_centavos INTEGER NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )

            # 4) copia os dados trocando o texto pelo id da categoria (mantém os ids dos gastos)
            con.execute(
                f"""
                INSERT INTO gastos_novo (id, descricao, categoria_id, valor_centavos, data)
                SELECT g.id, g.descricao, c.id, g.valor_centavos, g.data
                FROM gastos g
                JOIN categorias c ON c.nome = {NORMALIZA.format(col='g.categoria')}
                """
            )

            # 5) conferências: se algo estiver errado, levanta erro e cai no ROLLBACK
            depois = con.execute("SELECT COUNT(*) FROM gastos_novo").fetchone()[0]
            if antes != depois:
                raise RuntimeError(f"Contagem diferente: {antes} antes, {depois} depois.")

            # 6) troca a tabela velha pela nova
            con.execute("DROP TABLE gastos")
            con.execute("ALTER TABLE gastos_novo RENAME TO gastos")

            problemas = con.execute("PRAGMA foreign_key_check").fetchall()
            if problemas:
                raise RuntimeError(f"Violações de chave estrangeira: {problemas}")

            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            print("Erro: nada foi alterado no banco (ROLLBACK).")
            raise

        print(f"Migração concluída: {depois} gastos.")
        for nome, qtd in con.execute(
            """
            SELECT c.nome, COUNT(*) FROM gastos g
            JOIN categorias c ON c.id = g.categoria_id
            GROUP BY c.nome ORDER BY c.nome
            """
        ):
            print(f"  {nome}: {qtd}")
    finally:
        con.close()


if __name__ == "__main__":
    migrar()