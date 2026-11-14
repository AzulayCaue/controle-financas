import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


DB = Path(__file__).parent / "financas.db"
con = sqlite3.connect(DB)
con.execute(
    """
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria TEXT NOT NULL,
        valor_centavos INTEGER NOT NULL,
        data TEXT NOT NULL
    )
    """
)
con.commit()


def formatar(centavos):
    return f"R$ {centavos / 100:.2f}"


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


def adicionar():
    descricao = ler_texto("Descrição: ")
    categoria = ler_texto("Categoria (ex: mercado, transporte): ").lower()
    valor = ler_valor()
    data = ler_data()
    con.execute(
        "INSERT INTO gastos (descricao, categoria, valor_centavos, data) VALUES (?, ?, ?, ?)",
        (descricao, categoria, valor, data),
    )
    con.commit()
    print("Gasto registrado!")


def listar():
    linhas = con.execute(
        "SELECT id, data, descricao, categoria, valor_centavos FROM gastos ORDER BY data, id"
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
        SELECT categoria, SUM(valor_centavos)
        FROM gastos
        WHERE strftime('%Y-%m', data) = ?
        GROUP BY categoria
        ORDER BY SUM(valor_centavos) DESC
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
        "SELECT descricao, categoria FROM gastos WHERE id = ?", (id_,)
    ).fetchone()

    print("Enter mantém o valor atual.")
    nova_descricao = input(f"Descrição [{descricao}]: ").strip() or descricao
    nova_categoria = input(f"Categoria [{categoria}]: ").strip().lower() or categoria
    con.execute(
        "UPDATE gastos SET descricao = ?, categoria = ? WHERE id = ?",
        (nova_descricao, nova_categoria, id_),
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


def main():
    try:
        while True:
            print("\n1) Adicionar Gasto")
            print("2) Listar gastos")
            print("3) Resumo do mês por categoria")
            print("4) Editar gasto")
            print("5) Apagar gasto")
            print("6) Sair")
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
                break
            else:
                print("Opção inválida.")
    except (KeyboardInterrupt, EOFError):
        print("\nSaindo.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
