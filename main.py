import random
import string

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
      - Tamanho de cada conjunto: (y - x) elementos
      - Elementos sorteados aleatoriamente dentro de [x, y]
        e ordenados de forma crescente

    Retorna lista de tuplas (nome, ConjuntoNumerico).
    """
    nomes  = list(string.ascii_uppercase)
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

def exibir_conjuntos(conjuntos: list, x: int, y: int):
    #SEP = "─" * 52
    print("\n" + "═" * 52)
    print("   CONJUNTOS GERADOS")
    print("═" * 52)
    print(f"  Intervalo: [{x}, {y}]   Tamanho: {y - x}")
    #print(f"  {SEP}")
    print(f"  {'Nome':<6} Elementos")
    #print(f"  {SEP}")
    for nome, conj in conjuntos:
        print(f"  {nome:<6} {conj}")


def exibir_operacoes(conjuntos: list):
    if len(conjuntos) < 2:
        return
    SEP = "─" * 52
    print("\n" + "═" * 52)
    print("   OPERAÇÕES ENTRE PARES CONSECUTIVOS")
    print("═" * 52)
    for i in range(len(conjuntos) - 1):
        nA, A = conjuntos[i]
        nB, B = conjuntos[i + 1]
        print(f"\n{SEP}")
        print(f"  {nA} = {A}")
        print(f"  {nB} = {B}")

def verificar_contencao(ref: ConjuntoNumerico, conjuntos: list) -> None:
    """
    Verifica em quais conjuntos da lista o conjunto de referência está contido.
 
    Parâmetros:
      ref        — ConjuntoNumerico de referência
      conjuntos  — lista de tuplas (nome, ConjuntoNumerico) geradas anteriormente
 
    Exibe separadamente:
      • Conjuntos que CONTÊM ref (ref ⊆ conj)
      • Conjuntos que NÃO contêm ref
    """
    SEP = "─" * 52
 
    contem     = []
    nao_contem = []
 
    for nome, conj in conjuntos:
        if ref.subconjunto(conj):
            contem.append((nome, conj))
        else:
            nao_contem.append((nome, conj))
 
    # ── Cabeçalho ─────────────────────────────────────────────────────
    print("\n" + "═" * 52)
    print("   VERIFICAÇÃO DE CONTENÇÃO  (ref ⊆ conjunto?)")
    print("═" * 52)
    print(f"  Conjunto referência : {ref}")
    print(f"  Total comparados    : {len(conjuntos)}")
    print(f"  Contêm ref          : {len(contem)}")
    print(f"  Não contêm ref      : {len(nao_contem)}")
 
    # ── Contêm ────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"  ✔  ref ⊆ conjunto  ({len(contem)})")
    print(SEP)
    if contem:
        for nome, conj in contem:
            print(f"  {nome}")
            print(f"    ref      = {ref}")
            print(f"    conjunto = {conj}")
    else:
        print("  Nenhum conjunto contém o de referência.")
 
    # ── Não contêm ───────────────────────────────────────────────────
    # print(f"\n{SEP}")
    # print(f"  ✘  ref ⊄ conjunto  ({len(nao_contem)})")
    # print(SEP)
    # if nao_contem:
    #     for nome, conj in nao_contem:
    #         print(f"  {nome}")
    #         print(f"    ref      = {ref}")
    #         print(f"    conjunto = {conj}")
    #else:
        #print("  Todos os conjuntos contêm o de referência.")

# ====================================================================== #
#  Main                                                                   #
# ====================================================================== #

if __name__ == "__main__":
    SEP = "─" * 52

    print("\n" + "═" * 52)
    print("   GERADOR DE CONJUNTOS NUMÉRICOS")
    print("═" * 52)

    n = ler_inteiro("\n  Quantos conjuntos? (N): ", minimo=1, maximo=10000)

    print(f"\n{SEP}")
    print("  Intervalo [x, y]  —  cada conjunto terá (y - x) elementos")
    print(SEP)

    x = ler_inteiro("  Início do intervalo (x): ")

    while True:
        y = ler_inteiro("  Fim do intervalo   (y): ", minimo=x + 2)
        tamanho = ler_inteiro("  tamanho dos conjuntos: ")
        if y - x < 2:
            print("  ✗ y deve ser pelo menos x + 2 para haver aleatoriedade.")
        else:
            break

    print(f"\n  Gerando {n} conjunto(s) de tamanho {tamanho} no intervalo [{x}, {y}]...\n")

    conjuntos = gerar_conjuntos(n, x, y, tamanho)

    exibir_conjuntos(conjuntos, x, y)

    print(f"\n{SEP}")
    print("  Intervalo [x, y]  —  cada conjunto terá (y - x) elementos")
    print("\n Qual o intervalo do conjunto de intersecção?")
    print(SEP)

    x = ler_inteiro("  Início do intervalo (x): ")

    while True: #transformar em função depois 
        y = ler_inteiro("  Fim do intervalo   (y): ", minimo=x + 2)
        tamanho = ler_inteiro("  tamanho do conjunto: ")
        if y - x < 2:
            print("  ✗ y deve ser pelo menos x + 2 para haver aleatoriedade.")
        else:
            break

    conjunto_referencia = gerar_conjuntos(1, x, y, tamanho)
    verificar_contencao(conjunto_referencia[0][1], conjuntos)

    print("\n\n" + "═" * 52)
    print("   PROGRAMA ENCERRADO")
    print("═" * 52 + "\n")
