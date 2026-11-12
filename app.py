import json
import os
from datetime import date

ARQUIVO = "gastos.json"


def carregar():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar(gastos):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(gastos, f, ensure_ascii=False, indent=2)


def ler_valor():
    while True:
        texto = input("Valor: ").replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("Valor inválido. Digite um número, ex: 25,50")
            continue
        if valor <= 0:
            print("O valor precisa ser maior que zero.")
            continue
        return valor


def ler_data():
    while True:
        texto = input("Data (AAAA-MM-DD, Enter = hoje): ")
        if texto == "":
            return date.today().isoformat()
        try:
            return date.fromisoformat(texto).isoformat()
        except ValueError:
            print("Data inválida. Use o formato 2026-11-12")


def adicionar(gastos):
    descricao = input("Descrição: ")
    categoria = input("Categoria (ex: mercado, transporte): ").lower()
    valor = ler_valor()
    data = ler_data()
    gastos.append(
        {"descricao": descricao, "categoria": categoria, "valor": valor, "data": data}
    )
    salvar(gastos)
    print("Gasto registrado!")


def listar(gastos):
    if not gastos:
        print("Nenhum gasto ainda.")
        return
    for i, gasto in enumerate(gastos, start=1):
        data = gasto.get("data", "sem data")
        categoria = gasto.get("categoria", "sem categoria")
        print(f"{i}) {data} | {gasto['descricao']} [{categoria}]: R$ {gasto['valor']:.2f}")


def resumo(gastos):
    mes_atual = date.today().strftime("%Y-%m")
    mes = input(f"Mês (AAAA-MM, Enter = {mes_atual}): ") or mes_atual

    totais = {}
    for gasto in gastos:
        if not gasto.get("data", "").startswith(mes):
            continue
        categoria = gasto.get("categoria", "sem categoria")
        totais[categoria] = totais.get(categoria, 0) + gasto["valor"]

    if not totais:
        print("Nenhum gasto nesse mês.")
        return

    print(f"\n--- Resumo de {mes} ---")
    for categoria, total in totais.items():
        print(f"{categoria}: R$ {total:.2f}")
    print(f"\nTotal do mês: R$ {sum(totais.values()):.2f}")

def escolher(gastos):
    listar(gastos)
    if not gastos:
        return None
    texto = input("Número do gasto (Enter para cancelar): ")
    if texto == "":
        return None
    if not texto.isdigit() or not 1 <= int(texto) <= len(gastos):
        print("Número inválido.")
        return None
    return int(texto) - 1


def apagar(gastos):
    i = escolher(gastos)
    if i is None:
        return
    removido = gastos.pop(i)
    salvar(gastos)
    print(f"Apagado: {removido['descricao']}")


def editar(gastos):
    i = escolher(gastos)
    if i is None:
        return
    gasto = gastos[i]
    print("Enter mantém o valor atual.")
    descricao = input(f"Descrição [{gasto['descricao']}]: ")
    categoria = input(f"Categoria [{gasto.get('categoria', '')}]: ").lower()
    if descricao:
        gasto["descricao"] = descricao
    if categoria:
        gasto["categoria"] = categoria
    if input("Alterar valor? (s/N): ").lower() == "s":
        gasto["valor"] = ler_valor()
    if input("Alterar data? (s/N): ").lower() == "s":
        gasto["data"] = ler_data()
    salvar(gastos)
    print("Gasto atualizado!")

gastos = carregar()

while True:
    print("\n1) Adicionar gasto")
    print("2) Listar gastos")
    print("3) Resumo do mês por categoria")
    print("4) Editar gasto")
    print("5) Apagar gasto")
    print("6) Sair")
    opcao = input("Escolha: ")

    if opcao == "1":
        adicionar(gastos)
    elif opcao == "2":
        listar(gastos)
    elif opcao == "3":
        resumo(gastos)
    elif opcao == "4":
        editar(gastos)
    elif opcao == "5":
        apagar(gastos)
    elif opcao == "6":
        break
    else:
        print("Opção inválida.")