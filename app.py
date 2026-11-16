import sqlite3
import csv
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


DB = Path(__file__).parent / "financas.db"
con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")
con.execute(
    """
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    """
)
con.execute(
    """
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria_id INTEGER NOT NULL REFERENCES categorias(id),
        valor_centavos INTEGER NOT NULL,
        data TEXT NOT NULL
    )
    """
)
con.commit()


def formatar(centavos):
    reais, cents = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{cents:02d}"


def ler_valor():
    while True:
        texto = input("Valor: ").replace(",", ".")
        try:
            valor = Decimal(texto)
        except InvalidOperation:
            print("Valor inválido. Digite um número, ex: 25,50")
            continue
        if not valor.is_finite():
            print("Digite um número válido.")
            continue
        centavos = int((valor * 100).to_integral_value(rounding=ROUND_HALF_UP))
        if centavos <= 0 or centavos > 10**12:
            print("O valor precisa estar entre R$ 0,01 e R$ 10 bilhões.")
            continue
        return centavos   


def ler_data():
    while True:
        texto = input("Data (AAAA-MM-DD, Enter = hoje): ")
        if texto == "":
            return date.today().isoformat()
        try:
            return date.fromisoformat(texto).isoformat()
        except ValueError:
            print("Data inválida. Use o formato 2026-11-12")


def ler_texto(pergunta):
    while True:
        texto = input(pergunta).strip()
        if texto:
            return texto
        print("Esse campo não pode ficar vazio.")


def obter_categoria_id(nome):
    # INSERT OR IGNORE: se o nome já existe (UNIQUE), ignora sem dar erro.
    con.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (nome,))
    return con.execute("SELECT id FROM categorias WHERE nome = ?", (nome,)).fetchone()[0]


def adicionar():
    descricao = ler_texto("Descrição: ")
    categoria = ler_texto("Categoria (ex: mercado, transporte): ").lower()
    valor = ler_valor()
    data = ler_data()
    categoria_id = obter_categoria_id(categoria)
    con.execute(
        "INSERT INTO gastos (descricao, categoria_id, valor_centavos, data) VALUES (?, ?, ?, ?)",
        (descricao, categoria_id, valor, data),
    )
    con.commit() #categoria nova + gasto entram juntos, na mesma transação
    print("Gasto registrado!")


def listar():
    linhas = con.execute(
        """
        SELECT g.id, g.data, g.descricao, c.nome, g.valor_centavos
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        ORDER BY g.data, g.id
        """
    ).fetchall()
    if not linhas:
        print("Nenhum gasto ainda.")
        return False
    for id_, data, descricao, categoria, valor in linhas:
        print(f"{id_}) {data} | {descricao} [{categoria}]: {formatar(valor)}")
    return True


def escolher_id():
    if not listar():
        return None
    texto = input("ID do gasto (Enter para cancelar): ")
    if texto == "":
        return None
    if not texto.isdigit():
        print("ID inválido.")
        return None
    existe = con.execute("SELECT 1 FROM gastos WHERE id = ?", (int(texto),)).fetchone()
    if not existe:
        print("Não existe gasto com esse ID.")
        return None
    return int(texto)


def resumo():
    mes_atual = date.today().strftime("%Y-%m")
    mes = input(f"Mês (AAAA-MM, Enter = {mes_atual}): ").strip() or mes_atual


    try:
        if len(mes) != 7:
            raise ValueError
        date.fromisoformat(mes + "-01")
    except ValueError:
        print("Mês inválido. Use AAAA-MM, ex: 2026-11")
        return

    linhas = con.execute(
        """
        SELECT c.nome, SUM(valor_centavos)
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        WHERE strftime('%Y-%m', g.data) = ?
        GROUP BY c.nome
        ORDER BY SUM(g.valor_centavos) DESC
        """,
        (mes,),
    ).fetchall()

    if not linhas:
        print("Nenhum gasto nesse mês.")
        return

    print(f"\n--- Resumo de {mes} ---")
    total = 0
    for categoria, soma in linhas:
        print(f"{categoria}: {formatar(soma)}")
        total += soma
    print(f"\nTotal do mês: {formatar(total)}")


def editar():
    id_ = escolher_id()
    if id_ is None:
        return
    descricao, categoria = con.execute(
        """
        SELECT g.descricao, c.nome
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        WHERE g.id = ?
        """, 
        (id_,)
    ).fetchone()

    print("Enter mantém o valor atual.")
    nova_descricao = input(f"Descrição [{descricao}]: ").strip() or descricao
    nova_categoria = input(f"Categoria [{categoria}]: ").strip().lower() or categoria
    con.execute(
        "UPDATE gastos SET descricao = ?, categoria_id = ? WHERE id = ?",
        (nova_descricao, obter_categoria_id(nova_categoria), id_),
    )
    if input("Alterar valor? (s/N): ").lower() == "s":
        con.execute(
            "UPDATE gastos SET valor_centavos = ? WHERE id = ?", (ler_valor(), id_)
        )
    if input("Alterar data? (s/N): ").lower() == "s":
        con.execute("UPDATE gastos SET data = ? WHERE id = ?", (ler_data(), id_))
    con.commit()
    print("Gasto atualizado!")


def apagar():
    id_ = escolher_id()
    if id_ is None:
        return
    con.execute("DELETE FROM gastos WHERE id = ?", (id_,))
    con.commit()
    print("Gasto apagado.")


def exportar():
    linhas = con.execute(
        """
        SELECT g.id, g.data, g.descricao, c.nome, g.valor_centavos
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        ORDER BY g.data, g.id
        """
    ).fetchall()
    if not linhas:
        print("Nenhum gasto para exportar.")
        return

    arquivo = Path(__file__).parent / "gastos_exportados.csv"
    with open(arquivo, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["id", "data", "descricao", "categoria", "valor"])
        for id_, data, descricao, categoria, valor in linhas:
            escritor.writerow([id_, data, descricao, categoria, f"{valor // 100},{valor % 100:02d}"])
    print(f"Exportado para: {arquivo}")


def main():
    try:
        while True:
            print("\n1) Adicionar Gasto")
            print("2) Listar gastos")
            print("3) Resumo do mês por categoria")
            print("4) Editar gasto")
            print("5) Apagar gasto")
            print("6) Exportar para CSV")
            print("7) Sair")
            opcao = input("Escolha: ")

            if opcao == "1":
                adicionar()
            elif opcao == "2":
                listar()
            elif opcao == "3":
                resumo()
            elif opcao == "4":
                editar()
            elif opcao == "5":
                apagar()
            elif opcao == "6":
                exportar()
            elif opcao == "7":
                break
            else:
                print("Opção inválida.")
    except (KeyboardInterrupt, EOFError):
        print("\nSaindo.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
