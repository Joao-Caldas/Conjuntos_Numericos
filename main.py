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
    nomes = list(string.ascii_uppercase)
    conjuntos = []

    for i in range(n):
        nome = f"CB{i + 1}"
        elementos = sorted(random.sample(range(x, y + 1), tamanho))
        conj = ConjuntoNumerico(elementos)
        conjuntos.append((nome, conj))

    return conjuntos



# ====================================================================== #
#  Carregamento de conjuntos a partir de .txt                             #
# ====================================================================== #

def carregar_conjuntos_txt(caminho: str) -> list:
    """
    Lê um arquivo .txt e retorna lista de tuplas (nome, ConjuntoNumerico).

    Formatos aceitos por linha:
      CB1: 1, 3, 5, 7          -> nome explícito
      1, 3, 5, 7               -> nome gerado automaticamente (CB1, CB2...)
      # comentário             -> ignorado
      linha em branco          -> ignorada
    """
    conjuntos = []
    auto_index = 1

    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()

            # ignora comentários e linhas vazias
            if not linha or linha.startswith("#"):
                continue

            # formato "NOME: 1, 2, 3"
            if ":" in linha:
                partes = linha.split(":", 1)
                nome = partes[0].strip()
                nums = partes[1]
            else:
                nome = f"CB{auto_index}"
                nums = linha

            try:
                elementos = sorted({
                    int(n.strip().strip("{}"))
                    for n in nums.split(",")
                    if n.strip().strip("{}")
                })
                conjuntos.append((nome, ConjuntoNumerico(elementos)))
                auto_index += 1
            except ValueError:
                print(f"  ⚠ Linha ignorada (formato inválido): {linha}")

    return conjuntos

# ====================================================================== #
#  Exibição                                                               #
# ====================================================================== #

def exibir_conjuntos(conjuntos: list, x: int, y: int, tamanho: int):
    SEP = "─" * 52
    print("\n" + "═" * 52)
    print("   CONJUNTOS GERADOS")
    print("═" * 52)
    print(f"  Intervalo: [{x}, {y}]   Tamanho: {tamanho}") if tamanho != "arquivo" else print("  Conjuntos carregados de arquivo .txt")
    print(f"  {SEP}")
    print(f"  {'Nome':<6} Elementos")
    print(f"  {SEP}")
    for nome, conj in conjuntos:
        print(f"  {nome:<6} {conj}")


# ====================================================================== #
#  Verificação de contenção                                               #
# ====================================================================== #

def verificar_contencao_dados(refs: list, conjuntos: list) -> tuple:
    """
    Versão que RETORNA os dados em vez de imprimir (usada pelo Streamlit).
    Retorna (contem, nao_contem) como listas de (i_ref, ref, nome, conj).
    """
    contem, nao_contem = [], []
    for i, ref in enumerate(refs, start=1):
        for nome, conj in conjuntos:
            if ref.subconjunto(conj):
                contem.append((i, ref, nome, conj))
            else:
                nao_contem.append((i, ref, nome, conj))
    return contem, nao_contem


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
        for n_par, (i_ref, ref, nome, conj) in enumerate(contem, start=1):
            print(f"  {n_par}. CR{i_ref} ⊆ {nome}")
            print(f"    CR{i_ref} = {ref}")
            print(f"    {nome}  = {conj}")
    else:
        print("  Nenhum par de contenção encontrado.")




# ====================================================================== #
#  Main                                                                   #
# ====================================================================== #

if __name__ == "__main__":
    SEP = "─" * 52

    print("\n" + "═" * 52)
    print("   GERADOR DE CONJUNTOS NUMÉRICOS")
    print("═" * 52)

    print(f"\n{SEP}")
    print("  Conjuntos base")
    print(SEP)
    print("  [1] Gerar aleatoriamente")
    print("  [2] Carregar de arquivo .txt")
    opcao = ler_inteiro("\n  Escolha uma opção: ", minimo=1, maximo=2)

    if opcao == 1:
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
        x = y = tamanho = "—"   # apenas para o log do arquivo

    else:
        while True:
            caminho = input("\n  Caminho do arquivo .txt: ").strip()
            if os.path.isfile(caminho):
                break
            print(f"  ✗ Arquivo não encontrado: {caminho}")

        conjuntos = carregar_conjuntos_txt(caminho)

        if not conjuntos:
            print("  ✗ Nenhum conjunto válido encontrado no arquivo.")
            sys.exit(1)

        print(f"\n  {len(conjuntos)} conjunto(s) carregado(s) de '{caminho}'.")
        x = y = tamanho = "arquivo"   # apenas para o log

    # ── Conjuntos de referência ────────────────────────────────────────
    print(f"\n{SEP}")
    print("  Conjuntos de referência")
    print(SEP)
    print("  [1] Gerar aleatoriamente")
    print("  [2] Carregar de arquivo .txt")
    opcao_ref = ler_inteiro("\n  Escolha uma opção: ", minimo=1, maximo=2)

    if opcao_ref == 1:
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

        xr_log = f"[{xr}, {yr}]"
        tamanho_ref_log = tamanho_ref

    else:
        while True:
            caminho_ref = input("\n  Caminho do arquivo .txt: ").strip()
            if os.path.isfile(caminho_ref):
                break
            print(f"  ✗ Arquivo não encontrado: {caminho_ref}")

        refs_raw = carregar_conjuntos_txt(caminho_ref)

        if not refs_raw:
            print("  ✗ Nenhum conjunto válido encontrado no arquivo.")
            sys.exit(1)

        # renomear para CR1, CR2...
        refs = [conj for _, conj in refs_raw]
        print(f"\n  {len(refs)} conjunto(s) de referência carregado(s) de '{caminho_ref}'.")

        xr_log = "arquivo"
        tamanho_ref_log = "arquivo"

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

    if opcao_ref == 1:
        print(f"\n  {len(refs)} conjunto(s) de referência criado(s) com tamanho {tamanho_ref_log} no intervalo {xr_log}.")
    else:
        print(f"\n  {len(refs)} conjunto(s) de referência carregado(s) de arquivo.")

    verificar_contencao(refs, conjuntos)

    print("\n\n" + "═" * 52)
    print("   PROGRAMA ENCERRADO")
    print("═" * 52 + "\n")

    # ── Restaura stdout e salva arquivos ──────────────────────────────
    sys.stdout = tee

    base_dir  = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # pasta execuções — resultado completo
    pasta_exec = os.path.join(base_dir, "execucoes")
    os.makedirs(pasta_exec, exist_ok=True)
    arq_exec = os.path.join(pasta_exec, f"{timestamp}.txt")
    with open(arq_exec, "w", encoding="utf-8") as f:
        f.write(buffer.getvalue())

    # pasta conjuntos base
    pasta_base = os.path.join(base_dir, "conjuntos base")
    os.makedirs(pasta_base, exist_ok=True)
    arq_base = os.path.join(pasta_base, f"{timestamp}.txt")
    with open(arq_base, "w", encoding="utf-8") as f:
        f.write(f"Intervalo: [{x}, {y}]   Tamanho: {tamanho}\n") if tamanho != "arquivo" else f.write("Conjuntos carregados de arquivo .txt\n")
        f.write("─" * 52 + "\n")
        f.write(f"{'Nome':<8} Elementos\n")
        f.write("─" * 52 + "\n")
        for nome, conj in conjuntos:
            f.write(f"{nome:<8} {conj}\n")

    # pasta conjuntos referencia
    pasta_ref = os.path.join(base_dir, "conjuntos referencia")
    os.makedirs(pasta_ref, exist_ok=True)
    arq_ref = os.path.join(pasta_ref, f"{timestamp}.txt")
    with open(arq_ref, "w", encoding="utf-8") as f:
        cabecalho = f"Intervalo: {xr_log}   Tamanho: {tamanho_ref_log}"
        f.write(cabecalho + "\n")
        f.write("─" * 52 + "\n")
        f.write(f"{'ID':<8} Elementos\n")
        f.write("─" * 52 + "\n")
        for i, ref in enumerate(refs, start=1):
            f.write(f"CR{i:<6} {ref}\n")

    print(f"  ✔ Execução   salva em: execucoes/{timestamp}.txt")
    print(f"  ✔ Conj. base salvo em: conjuntos base/{timestamp}.txt")
    print(f"  ✔ Conj. ref  salvo em: conjuntos referencia/{timestamp}.txt")


# ====================================================================== #
#  Busca por coincidência parcial                                         #
# ====================================================================== #

def parsear_numeros(texto: str) -> set:
    """Converte string '01, 02, 03' em conjunto de inteiros {1, 2, 3}."""
    nums = set()
    for parte in texto.split(","):
        parte = parte.strip().strip("{}")
        if parte:
            nums.add(int(parte))
    return nums


def buscar_por_coincidencia(numeros: set, k: int, conjuntos: list) -> list:
    """
    Encontra conjuntos base que contêm EXATAMENTE k dos números informados.

    Parâmetros:
      numeros   — conjunto de inteiros a procurar
      k         — quantidade exata de coincidências exigida
      conjuntos — lista de tuplas (nome, ConjuntoNumerico)

    Retorna lista de (nome, conj, elementos_em_comum).
    """
    resultados = []
    for nome, conj in conjuntos:
        em_comum = sorted(set(conj.elementos) & numeros)
        if len(em_comum) == k:
            resultados.append((nome, conj, em_comum))
    return resultados


def buscar_grupos_e_verificar_contencao(numeros: set, k: int, conjuntos: list) -> list:
    """
    Busca parcial + verificação de contenção integradas.

    Passo 1 — Encontra todos os CBs com EXATAMENTE k coincidências com 'numeros'
              e agrupa os que têm os mesmos k elementos idênticos.

    Passo 2 — Para cada grupo único, verifica TODOS os conjuntos base (não só
              os encontrados no passo 1) e retorna quais contêm aquele grupo
              como subconjunto.

    Retorna lista de dicts ordenada por qtd de CBs que contêm (desc):
      {
        'grupo_elementos': tuple,          # os k elementos do grupo
        'cbs_busca'     : list of tuples,  # CBs que geraram o grupo (exatamente k)
        'cbs_contem'    : list of tuples,  # TODOS os CBs que contêm o grupo
      }
    """
    from itertools import groupby

    # ── Passo 1: CBs com exatamente k coincidências ──────────────────
    resultados_k = []
    for nome, conj in conjuntos:
        em_comum = sorted(set(conj.elementos) & numeros)
        if len(em_comum) == k:
            resultados_k.append((nome, conj, em_comum))

    resultados_k.sort(key=lambda x: x[2])  # ordena para o groupby

    # ── Passo 2: para cada grupo verifica TODOS os CBs ───────────────
    grupos_resultado = []
    for chave, grupo in groupby(resultados_k, key=lambda x: tuple(x[2])):
        membros_busca = list(grupo)
        ref = ConjuntoNumerico(list(chave))

        cbs_contem = []
        for nome, conj in conjuntos:          # percorre TODOS os 2000 CBs
            if ref.subconjunto(conj):
                cbs_contem.append((nome, conj))

        grupos_resultado.append({
            'grupo_elementos': chave,
            'cbs_busca'     : membros_busca,
            'cbs_contem'    : cbs_contem,
        })

    # Ordena por quantidade de CBs que contêm (maior primeiro)
    grupos_resultado.sort(key=lambda x: len(x['cbs_contem']), reverse=True)
    return grupos_resultado


def buscar_todos_grupos_possiveis(numeros: set, k: int, conjuntos: list) -> list:
    """
    Para cada CB, considera TODAS as sub-combinações de k elementos da
    sua interseção com 'numeros' (não apenas os que têm exatamente k).

    Um CB com interseção de tamanho m >= k contribui com C(m, k) grupos.

    Retorna lista de dicts ordenada por quantidade de CBs (desc):
      {
        'grupo_elementos': tuple,   # os k elementos do grupo
        'cbs_contem'     : list,    # (nome, conj) dos CBs que contêm o grupo
      }
    """
    from itertools import combinations
    from collections import defaultdict

    grupos_dict = defaultdict(list)

    for nome, conj in conjuntos:
        em_comum = sorted(set(conj.elementos) & numeros)
        if len(em_comum) >= k:
            for combo in combinations(em_comum, k):
                grupos_dict[combo].append((nome, conj))

    grupos = [
        {"grupo_elementos": chave, "cbs_contem": cbs}
        for chave, cbs in grupos_dict.items()
    ]
    grupos.sort(key=lambda x: len(x["cbs_contem"]), reverse=True)
    return grupos


def comparar_cbs_entre_si(k: int, conjuntos: list) -> list:
    """
    Compara todos os pares de CBs e agrupa os que compartilham
    EXATAMENTE k elementos idênticos entre si (interseção par a par).

    Parâmetros:
      k         — número exato de elementos em comum exigido
      conjuntos — lista de tuplas (nome, ConjuntoNumerico)

    Retorna lista de dicts ordenada por quantidade de pares (desc):
      {
        'elementos_comuns': tuple,            # os k elementos compartilhados
        'pares'           : [(ni,ci,nj,cj)],  # todos os pares que os compartilham
        'cbs'             : set,              # nomes únicos dos CBs envolvidos
      }
    """
    from itertools import combinations
    from collections import defaultdict

    grupos = defaultdict(list)

    for (nome_i, conj_i), (nome_j, conj_j) in combinations(conjuntos, 2):
        intersecao = set(conj_i.elementos) & set(conj_j.elementos)
        if len(intersecao) == k:
            chave = tuple(sorted(intersecao))
            grupos[chave].append((nome_i, conj_i, nome_j, conj_j))

    resultado = [
        {
            "elementos_comuns": chave,
            "pares"           : pares,
            "cbs"             : set(n for p in pares for n in (p[0], p[2])),
        }
        for chave, pares in grupos.items()
    ]
    resultado.sort(key=lambda x: len(x["pares"]), reverse=True)
    return resultado


def comparar_dois_conjuntos(k: int, conjuntos_a: list, conjuntos_b: list) -> list:
    """
    Compara cada CB do conjunto A contra cada CB do conjunto B,
    agrupando os pares que têm EXATAMENTE k elementos idênticos.

    Retorna lista de dicts ordenada por quantidade de pares (desc):
      {
        'elementos_comuns': tuple,
        'pares'           : [(nome_a, conj_a, nome_b, conj_b)],
        'cbs_a'           : set de nomes do conjunto A envolvidos,
        'cbs_b'           : set de nomes do conjunto B envolvidos,
      }
    """
    from collections import defaultdict

    grupos = defaultdict(list)

    for nome_a, conj_a in conjuntos_a:
        set_a = set(conj_a.elementos)
        for nome_b, conj_b in conjuntos_b:
            intersecao = set_a & set(conj_b.elementos)
            if len(intersecao) == k:
                chave = tuple(sorted(intersecao))
                grupos[chave].append((nome_a, conj_a, nome_b, conj_b))

    resultado = [
        {
            "elementos_comuns": chave,
            "pares"           : pares,
            "cbs_a"           : set(p[0] for p in pares),
            "cbs_b"           : set(p[2] for p in pares),
        }
        for chave, pares in grupos.items()
    ]
    resultado.sort(key=lambda x: len(x["pares"]), reverse=True)
    return resultado


def filtrar_cbs_por_grupo(grupo_elementos: set, conjuntos: list) -> list:
    """
    Retorna apenas os CBs que contêm todos os elementos do grupo como subconjunto.
    """
    ref = ConjuntoNumerico(sorted(grupo_elementos))
    return [(nome, conj) for nome, conj in conjuntos if ref.subconjunto(conj)]
