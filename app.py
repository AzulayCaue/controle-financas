import json
import os

ARQUIVO = "gastos.json"


def carregar():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar(gastos):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(gastos, f, ensure_ascii=False, indent=2)


def adicionar(gastos):
    descricao = input("Descrição: ")
    categoria = input("Categoria (ex: mercado, transporte): ").lower()
    valor = float(input("Valor: ").replace(",", "."))
    gastos.append({"descricao": descricao, "categoria": categoria, "valor": valor})
    salvar(gastos)
    print("Gasto registrado!")


def listar(gastos):
    if not gastos:
        print("Nenhum gasto ainda.")
        return
    for gasto in gastos:
        categoria = gasto.get("categoria", "sem categoria")
        print(f"{gasto['descricao']} [{categoria}]: R$ {gasto['valor']:.2f}")


def resumo(gastos):
    totais = {}
    for gasto in gastos:
        categoria = gasto.get("categoria", "sem categoria")
        totais[categoria] = totais.get(categoria, 0) + gasto["valor"]
    for categoria, total in totais.items():
        print(f"{categoria}: R$ {total:.2f}")
    print(f"\nTotal geral: R$ {sum(totais.values()):.2f}")


gastos = carregar()

while True:
    print("\n1) Adicionar gasto")
    print("2) Listar gastos")
    print("3) Resumo por categoria")
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