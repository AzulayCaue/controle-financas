def obter_categoria_id(con, nome):
    # INSERT OR IGNORE: se o nome já existe (UNIQUE), ignora sem dar erro.
    con.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (nome,))
    return con.execute(
        "SELECT id FROM categorias WHERE nome = ?", (nome,)
    ).fetchone()[0]


def adicionar_gasto(con, descricao, categoria, valor_centavos, data):
    categoria = categoria.strip().lower() #normalização é regra de negócio: fica aqui
    # 'with con:' faz commit se der certo e rollback se der erro.
    # Categoria nova + gasto entram juntos, na mesma transação.
    with con:
        categoria_id = obter_categoria_id(con, categoria)
        con.execute(
            "INSERT INTO gastos (descricao, categoria_id, valor_centavos, data) "
            "VALUES (?, ?, ?, ?)",
            (descricao, categoria_id, valor_centavos, data),
        )


def listar_gastos(con):
    return con.execute(
        """
        SELECT g.id, g.data, g.descricao, c.nome, g.valor_centavos
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        ORDER BY g.data, g.id
        """
    ).fetchall()


def gasto_existe(con, gasto_id):
    return con.execute(
        "SELECT 1 FROM gastos WHERE id = ?", (gasto_id,)
    ).fetchone() is not None


def resumo_por_categoria(con, mes):
    # mes no formato "AAAA-MM", já validado por quem chama
    return con.execute(
        """
        SELECT c.nome, SUM(g.valor_centavos)
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        WHERE strftime('%Y-%m', g.data) = ?
        GROUP BY c.nome
        ORDER BY SUM(g.valor_centavos) DESC
        """,
        (mes,),
    ).fetchall()

