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
    for gasto in gastos:
        data = gasto.get("data", "sem data")
        categoria = gasto.get("categoria", "sem categoria")
        print(f"{data} | {gasto['descricao']} [{categoria}]: R$ {gasto['valor']:.2f}")


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


gastos = carregar()

while True:
    print("\n1) Adicionar gasto")
    print("2) Listar gastos")
    print("3) Resumo do mês por categoria")
    print("4) Sair")
    opcao = input("Escolha: ")

    if opcao == "1":
        adicionar(gastos)
    elif opcao == "2":
        listar(gastos)
    elif opcao == "3":
        resumo(gastos)
    elif opcao == "4":
        break
    else:
        print("Opção inválida.")