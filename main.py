import os
import sys
import random
import string
from datetime import datetime
from io import StringIO

from conjunto_numerico import ConjuntoNumerico


# ====================================================================== #
#  Utilitário de entrada                                                  #
# ====================================================================== #

def ler_inteiro(mensagem: str, minimo: int = None, maximo: int = None) -> int:
    """Lê um inteiro do terminal com validação."""
    while True:
        try:
            valor = int(input(mensagem))
            if minimo is not None and valor < minimo:
                print(f"  ✗ Digite um valor >= {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                print(f"  ✗ Digite um valor <= {maximo}.")
                continue
            return valor
        except ValueError:
            print("  ✗ Entrada inválida. Digite um número inteiro.")


# ====================================================================== #
#  Geração dos conjuntos                                                  #
# ====================================================================== #

def gerar_conjuntos(n: int, x: int, y: int, tamanho: int) -> list:
    """
    Gera N conjuntos com as regras:
      - Intervalo fixo [x, y] para todos os conjuntos
      - Tamanho de cada conjunto: informado pelo usuário
      - Elementos sorteados aleatoriamente dentro de [x, y]
        e ordenados de forma crescente

    Retorna lista de tuplas (nome, ConjuntoNumerico).
    """
    nomes = list(string.ascii_uppercase) #consertar para tirar letra do alphabeto e ser apenas
    conjuntos = []

    for i in range(n):
        nome = nomes[i] if i < 26 else f"C{i + 1}" 
        elementos = sorted(random.sample(range(x, y + 1), tamanho))
        conj = ConjuntoNumerico(elementos)
        conjuntos.append((nome, conj))

    return conjuntos


# ====================================================================== #
#  Exibição                                                               #
# ====================================================================== #

def exibir_conjuntos(conjuntos: list, x: int, y: int, tamanho: int):
    SEP = "─" * 52
    print("\n" + "═" * 52)
    print("   CONJUNTOS GERADOS")
    print("═" * 52)
    print(f"  Intervalo: [{x}, {y}]   Tamanho: {tamanho}")
    print(f"  {SEP}")
    print(f"  {'Nome':<6} Elementos")
    print(f"  {SEP}")
    for nome, conj in conjuntos:
        print(f"  {nome:<6} {conj}")


# ====================================================================== #
#  Verificação de contenção                                               #
# ====================================================================== #

def verificar_contencao(refs: list, conjuntos: list) -> None:
    """
    Verifica a contenção entre TODOS os conjuntos de referência e TODOS
    os conjuntos gerados anteriormente.

    Parâmetros:
      refs       — lista de ConjuntoNumerico de referência
      conjuntos  — lista de tuplas (nome, ConjuntoNumerico) geradas anteriormente

    Para cada par (ref_i, conj_j) verifica se ref_i ⊆ conj_j e exibe
    separadamente os pares que contêm e os que não contêm.
    """
    SEP = "─" * 52

    contem     = []   # lista de (i_ref, ref, nome_conj, conj)
    nao_contem = []   # idem

    for i, ref in enumerate(refs, start=1):
        for nome, conj in conjuntos:
            if ref.subconjunto(conj):
                contem.append((i, ref, nome, conj))
            else:
                nao_contem.append((i, ref, nome, conj))

    total_pares = len(refs) * len(conjuntos)

    # ── Cabeçalho ─────────────────────────────────────────────────────
    print("\n" + "═" * 52)
    print("   VERIFICAÇÃO DE CONTENÇÃO  (ref ⊆ conjunto?)")
    print("═" * 52)
    print(f"  Referências         : {len(refs)}")
    print(f"  Conjuntos           : {len(conjuntos)}")
    print(f"  Total de pares      : {total_pares}")
    print(f"  Pares que contêm    : {len(contem)}")
    print(f"  Pares que não contêm: {len(nao_contem)}")

    # ── Contêm ────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"  ✔  ref ⊆ conjunto  ({len(contem)})")
    print(SEP)
    if contem:
        for i_ref, ref, nome, conj in contem:
            print(f"  CR{i_ref} ⊆ {nome}")
            print(f"    CR{i_ref}   = {ref}")
            print(f"    conjunto = {conj}")
    else:
        print("  Nenhum par de contenção encontrado.")



if __name__ == "__main__":
    SEP = "─" * 52

    print("\n" + "═" * 52)
    print("   GERADOR DE CONJUNTOS NUMÉRICOS")
    print("═" * 52)

    n = ler_inteiro("\n  Quantos conjuntos? (N): ", minimo=1)

    print(f"\n{SEP}")
    print("  Intervalo [x, y] e tamanho dos conjuntos")
    print(SEP)

    x = ler_inteiro("  Início do intervalo (x): ")

    while True:
        y = ler_inteiro("  Fim do intervalo   (y): ", minimo=x + 2)
        tamanho = ler_inteiro("  Tamanho dos conjuntos : ", minimo=1)
        amplitude = y - x + 1
        if amplitude < tamanho:
            print(f"  ✗ O intervalo [{x}, {y}] tem {amplitude} inteiros mas o tamanho pedido é {tamanho}.")
        else:
            break

    print(f"\n  Gerando {n} conjunto(s) de tamanho {tamanho} no intervalo [{x}, {y}]...\n")

    conjuntos = gerar_conjuntos(n, x, y, tamanho)

    # ── Conjuntos de referência ────────────────────────────────────────
    print(f"\n{SEP}")
    print("  Qual o intervalo do conjunto de referência?")
    print(SEP)

    xr = ler_inteiro("  Início do intervalo (x): ")

    while True:
        yr = ler_inteiro("  Fim do intervalo   (y): ", minimo=xr + 2)
        tamanho_ref = ler_inteiro("  Tamanho dos conjuntos : ", minimo=1)
        amplitude_ref = yr - xr + 1
        if amplitude_ref < tamanho_ref:
            print(f"  ✗ O intervalo [{xr}, {yr}] tem {amplitude_ref} inteiros mas o tamanho pedido é {tamanho_ref}.")
        else:
            break

    qtd_refs = ler_inteiro("  Quantas vezes criar o conjunto de referência? ", minimo=1)

    refs = []
    for i in range(qtd_refs):
        elementos_ref = sorted(random.sample(range(xr, yr + 1), tamanho_ref))
        refs.append(ConjuntoNumerico(elementos_ref))

    # ── Captura toda a saída a partir daqui ───────────────────────────
    buffer = StringIO()
    tee = sys.stdout                          # guarda o stdout original

    class Tee:
        """Escreve simultaneamente no terminal e no buffer."""
        def write(self, msg):
            tee.write(msg)
            buffer.write(msg)
        def flush(self):
            tee.flush()

    sys.stdout = Tee()

    # ── Saída capturada ───────────────────────────────────────────────
    exibir_conjuntos(conjuntos, x, y, tamanho)

    print(f"\n  {qtd_refs} conjunto(s) de referência criado(s) com tamanho {tamanho_ref} no intervalo [{xr}, {yr}].")

    verificar_contencao(refs, conjuntos)

    print("\n\n" + "═" * 52)
    print("   PROGRAMA ENCERRADO")
    print("═" * 52 + "\n")

    # ── Restaura stdout e salva arquivo ───────────────────────────────
    sys.stdout = tee

    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "execucoes")
    os.makedirs(pasta, exist_ok=True)

    nome_arquivo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    caminho = os.path.join(pasta, nome_arquivo)

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(buffer.getvalue())

    print(f"  ✔ Resultado salvo em: execucoes/{nome_arquivo}")

    #fazer numeração dos pares | arrumar nomes e conjuntos iniciais | fazer base manual também | exibir como 01, 02, 03, 04, 05, 06, 07, 08, 09 | conjunto para inputar manualmente: 01, 02, 03, 04, 05, 06 | Salvar conjunto inicial | tentar resgatar a base inicial do programa antigo
    #serie de 15 = 01, 02, 03, 04, 05, 06, 07, 11, 12, 16, 17, 19, 21, 24, 25
