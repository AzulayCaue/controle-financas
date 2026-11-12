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


gastos = carregar()

while True:
    descricao = input("Descrição do gasto (ou 'sair'): ")

    if descricao == "sair":
        break

    valor = float(input("Valor: ").replace(",", "."))
    gastos.append({"descricao": descricao, "valor": valor})
    salvar(gastos)

print("\n--- Seus gastos ---")
total = 0
for gasto in gastos:
    print(f"{gasto['descricao']}: R$ {gasto['valor']:.2f}")
    total += gasto["valor"]

print(f"\nTotal: R$ {total:.2f}")