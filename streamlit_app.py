"""
Frontend Streamlit — Verificador de Conjuntos Numéricos
Deploy gratuito: https://streamlit.io/cloud

Para rodar localmente:
    pip install streamlit
    streamlit run streamlit_app.py
"""

import random
from datetime import datetime

import streamlit as st

from conjunto_numerico import ConjuntoNumerico
from main import (
    gerar_conjuntos,
    carregar_conjuntos_txt,
    verificar_contencao_dados,
    parsear_numeros,
    buscar_grupos_e_verificar_contencao,
)


# ====================================================================== #
#  Session state — persiste entre reruns                                  #
# ====================================================================== #

def init_state():
    defaults = {
        "conjuntos"          : None,   # lista de (nome, ConjuntoNumerico)
        "refs"               : None,   # lista de ConjuntoNumerico
        "conjuntos_filtrados": None,   # nova rodada
        "resultado_contem"   : None,   # pares contidos da última execução
        "grupos_parciais"    : None,   # resultado da última busca parcial
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ====================================================================== #
#  Configuração da página                                                 #
# ====================================================================== #

st.set_page_config(
    page_title="Verificador de Conjuntos",
    page_icon="🔢",
    layout="wide",
)

st.title("🔢 Verificador de Conjuntos Numéricos")
st.caption("Verifica se conjuntos de referência estão contidos em conjuntos base.")


# ====================================================================== #
#  Helpers                                                                #
# ====================================================================== #

def carregar_de_upload(uploaded_file) -> list:
    conteudo = uploaded_file.read().decode("utf-8")
    conjuntos = []
    auto_index = 1
    for linha in conteudo.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if ":" in linha:
            partes = linha.split(":", 1)
            nome, nums = partes[0].strip(), partes[1]
        else:
            nome, nums = f"CB{auto_index}", linha
        try:
            elementos = sorted({
                int(n.strip().strip("{}"))
                for n in nums.split(",")
                if n.strip().strip("{}")
            })
            conjuntos.append((nome, ConjuntoNumerico(elementos)))
            auto_index += 1
        except ValueError:
            st.warning(f"Linha ignorada: {linha}")
    return conjuntos


def highlight_html(elementos_conj, elementos_ref: set) -> str:
    larg = len(str(max(abs(int(e)) for e in elementos_conj)))
    partes = []
    for e in elementos_conj:
        s = str(int(e)).zfill(larg)
        if int(e) in elementos_ref:
            partes.append(f"<span style='color:#e67e00;font-weight:bold'>{s}</span>")
        else:
            partes.append(s)
    return "{" + ", ".join(partes) + "}"


def gerar_txt_resultado(contem, refs, conjuntos) -> str:
    linhas = [
        "═" * 52,
        "   VERIFICAÇÃO DE CONTENÇÃO  (ref ⊆ conjunto?)",
        "═" * 52,
        f"  Referências      : {len(refs)}",
        f"  Conjuntos base   : {len(conjuntos)}",
        f"  Pares encontrados: {len(contem)}",
        "",
        "─" * 52,
        f"  ✔  ref ⊆ conjunto  ({len(contem)})",
        "─" * 52,
    ]
    for n_par, (i_ref, ref, nome, conj) in enumerate(contem, start=1):
        linhas.append(f"  {n_par}. CR{i_ref} ⊆ {nome}")
        linhas.append(f"    CR{i_ref} = {ref}")
        linhas.append(f"    {nome}  = {conj}")
    return "\n".join(linhas)


# ====================================================================== #
#  Sidebar — configuração                                                 #
# ====================================================================== #

with st.sidebar:
    st.header("⚙️ Configuração")

    # ── Conjuntos base ─────────────────────────────────────────────────
    st.subheader("Conjuntos Base")

    if st.session_state.conjuntos_filtrados is not None:
        n_filt = len(st.session_state.conjuntos_filtrados)
        st.success(f"🔄 Nova rodada: {n_filt} conjuntos filtrados.")
        if st.button("✕ Cancelar nova rodada"):
            st.session_state.conjuntos_filtrados = None
            st.rerun()
        modo_base = "__filtrado__"
    else:
        modo_base = st.radio(
            "Origem:", ["Gerar aleatoriamente", "Carregar arquivo .txt"],
            key="modo_base"
        )
        if modo_base == "Gerar aleatoriamente":
            n_base   = st.number_input("Quantidade (N)",       min_value=1, value=10,  step=1)
            x_base   = st.number_input("Início do intervalo (x)", value=1,  step=1)
            y_base   = st.number_input("Fim do intervalo (y)",    value=30, step=1)
            tam_base = st.number_input("Tamanho dos conjuntos",  min_value=1, value=10, step=1)
        else:
            arq_base = st.file_uploader("Arquivo .txt", type="txt", key="upload_base")

    st.divider()

    # ── Conjuntos de referência ────────────────────────────────────────
    st.subheader("Conjuntos de Referência")
    modo_ref = st.radio(
        "Origem:", ["Gerar aleatoriamente", "Carregar arquivo .txt"],
        key="modo_ref"
    )
    if modo_ref == "Gerar aleatoriamente":
        x_ref   = st.number_input("Início do intervalo (x)", value=1,  step=1, key="xr")
        y_ref   = st.number_input("Fim do intervalo (y)",    value=25, step=1, key="yr")
        tam_ref = st.number_input("Tamanho dos conjuntos",   min_value=1, value=8, step=1, key="tr")
        qtd_ref = st.number_input("Quantidade de referências", min_value=1, value=3, step=1)
    else:
        arq_ref = st.file_uploader("Arquivo .txt", type="txt", key="upload_ref")

    st.divider()
    executar = st.button("▶ Executar verificação", use_container_width=True, type="primary")


# ====================================================================== #
#  Execução principal                                                     #
# ====================================================================== #

if executar:
    erros = []

    # ── Monta conjuntos base ───────────────────────────────────────────
    if modo_base == "__filtrado__":
        conjuntos_exec = st.session_state.conjuntos_filtrados
    elif modo_base == "Gerar aleatoriamente":
        amp = int(y_base) - int(x_base) + 1
        if y_base <= x_base:
            erros.append("y deve ser maior que x nos conjuntos base.")
        elif amp < tam_base:
            erros.append(f"Intervalo [{int(x_base)},{int(y_base)}] tem {amp} inteiros, tamanho pedido {int(tam_base)}.")
        else:
            conjuntos_exec = gerar_conjuntos(int(n_base), int(x_base), int(y_base), int(tam_base))
    else:
        if not arq_base:
            erros.append("Selecione um arquivo .txt para os conjuntos base.")
        else:
            conjuntos_exec = carregar_de_upload(arq_base)
            if not conjuntos_exec:
                erros.append("Nenhum conjunto válido no arquivo base.")

    # ── Monta referências ──────────────────────────────────────────────
    if modo_ref == "Gerar aleatoriamente":
        amp_r = int(y_ref) - int(x_ref) + 1
        if y_ref <= x_ref:
            erros.append("y deve ser maior que x nas referências.")
        elif amp_r < tam_ref:
            erros.append(f"Intervalo [{int(x_ref)},{int(y_ref)}] tem {amp_r} inteiros, tamanho pedido {int(tam_ref)}.")
        else:
            refs_exec = [
                ConjuntoNumerico(sorted(random.sample(range(int(x_ref), int(y_ref)+1), int(tam_ref))))
                for _ in range(int(qtd_ref))
            ]
    else:
        if not arq_ref:
            erros.append("Selecione um arquivo .txt para as referências.")
        else:
            refs_raw = carregar_de_upload(arq_ref)
            if not refs_raw:
                erros.append("Nenhum conjunto válido no arquivo de referência.")
            else:
                refs_exec = [c for _, c in refs_raw]

    if erros:
        for e in erros:
            st.error(e)
        st.stop()

    # ── Cálculo ────────────────────────────────────────────────────────
    with st.spinner("Verificando contenção..."):
        contem, _ = verificar_contencao_dados(refs_exec, conjuntos_exec)

    # Persiste no session_state
    st.session_state.conjuntos      = conjuntos_exec
    st.session_state.refs           = refs_exec
    st.session_state.resultado_contem = contem
    st.session_state.grupos_parciais  = None  # limpa busca anterior


# ====================================================================== #
#  Exibição do resultado da verificação principal                         #
# ====================================================================== #

if st.session_state.resultado_contem is not None:
    contem    = st.session_state.resultado_contem
    conjuntos = st.session_state.conjuntos
    refs      = st.session_state.refs

    st.subheader("📊 Resumo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conjuntos base",  len(conjuntos))
    c2.metric("Referências",     len(refs))
    c3.metric("Total de pares",  len(refs) * len(conjuntos))
    c4.metric("✔ Contidos",      len(contem))

    st.subheader(f"✔ Pares contidos — CR ⊆ CB ({len(contem)})")

    if not contem:
        st.info("Nenhum par de contenção encontrado.")
    else:
        busca = st.text_input("🔍 Filtrar por nome:", placeholder="CB5 ou CR2", key="busca_cont")
        filtrados = contem
        if busca.strip():
            t = busca.strip().upper()
            filtrados = [(i, r, n, c) for i, r, n, c in contem
                         if t in n.upper() or t in f"CR{i}"]
            st.caption(f"{len(filtrados)} resultado(s) para: {busca.strip()!r}")

        for n_par, (i_ref, ref, nome, conj) in enumerate(filtrados, start=1):
            with st.expander(f"{n_par}. CR{i_ref} ⊆ {nome}", expanded=False):
                st.markdown(f"**CR{i_ref}** = `{ref}`")
                html = highlight_html(conj.elementos, set(ref.elementos))
                st.markdown(f"**{nome}** = {html}", unsafe_allow_html=True)

    # ── Nova rodada ────────────────────────────────────────────────────
    if contem:
        st.divider()
        vistos, novos_base = set(), []
        for _, _, nome, conj in contem:
            if nome not in vistos:
                novos_base.append((nome, conj))
                vistos.add(nome)
        if st.button(
            f"🔄 Nova rodada com os {len(novos_base)} conjuntos que contêm a referência",
            type="primary", key="btn_nova_rodada"
        ):
            st.session_state.conjuntos_filtrados = novos_base
            st.session_state.resultado_contem    = None
            st.session_state.grupos_parciais     = None
            st.rerun()

    # ── Downloads ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("⬇️ Downloads")
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cd1, cd2, cd3 = st.columns(3)

    cd1.download_button("📄 Resultado completo",
        data=gerar_txt_resultado(contem, refs, conjuntos).encode(),
        file_name=f"execucao_{ts}.txt", mime="text/plain",
        use_container_width=True)

    linhas_base = ["Conjuntos Base\n" + "─"*52, f"{'Nome':<8} Elementos", "─"*52]
    for nome, conj in conjuntos:
        linhas_base.append(f"{nome:<8} {conj}")
    cd2.download_button("📄 Conjuntos base",
        data="\n".join(linhas_base).encode(),
        file_name=f"conjuntos_base_{ts}.txt", mime="text/plain",
        use_container_width=True)

    linhas_ref = ["Conjuntos de Referência\n" + "─"*52, f"{'ID':<8} Elementos", "─"*52]
    for i, ref in enumerate(refs, start=1):
        linhas_ref.append(f"CR{i:<6} {ref}")
    cd3.download_button("📄 Conjuntos referência",
        data="\n".join(linhas_ref).encode(),
        file_name=f"conjuntos_ref_{ts}.txt", mime="text/plain",
        use_container_width=True)


# ====================================================================== #
#  Busca por coincidência parcial                                         #
# ====================================================================== #

st.divider()
st.subheader("🔍 Busca por coincidência parcial")
st.caption("Encontra grupos com exatamente K coincidências e verifica contenção em TODOS os CBs.")

col_n, col_k, col_b = st.columns([5, 1, 1])
with col_n:
    texto_parcial = st.text_input(
        "Números (ex: 01, 02, 03 ...):",
        placeholder="01, 02, 03, 04, 05, 06, 07, 08, 09, 10",
        key="parcial_nums"
    )
with col_k:
    k_parcial = st.number_input("Exatas (K)", min_value=1, value=5, step=1, key="parcial_k")
with col_b:
    st.write(""); st.write("")
    buscar_parcial = st.button("🔍 Buscar", key="btn_parcial", use_container_width=True)

if buscar_parcial:
    if not texto_parcial.strip():
        st.warning("Digite os números para buscar.")
    elif st.session_state.conjuntos is None:
        st.warning("Execute a verificação principal primeiro para carregar os conjuntos base.")
    else:
        try:
            numeros_p = parsear_numeros(texto_parcial)
            k_val     = int(k_parcial)
            if k_val < 1 or k_val > len(numeros_p):
                st.error(f"K deve estar entre 1 e {len(numeros_p)}.")
                st.stop()

            with st.spinner(f"Buscando em {len(st.session_state.conjuntos)} CBs..."):
                grupos_p = buscar_grupos_e_verificar_contencao(
                    numeros_p, k_val, st.session_state.conjuntos
                )
            st.session_state.grupos_parciais = {
                "grupos"  : grupos_p,
                "numeros" : numeros_p,
                "k"       : k_val,
            }
        except ValueError as e:
            st.error(f"Entrada inválida: {e}")

# Exibe resultados da busca parcial (persiste entre reruns)
if st.session_state.grupos_parciais is not None:
    gp      = st.session_state.grupos_parciais
    grupos_p = gp["grupos"]
    numeros_p = gp["numeros"]
    k_val    = gp["k"]
    total_cbs = len(st.session_state.conjuntos)

    total_busca  = sum(len(g["cbs_busca"])  for g in grupos_p)
    total_contem = sum(len(g["cbs_contem"]) for g in grupos_p)

    st.subheader("📊 Resultado da busca parcial")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"CBs com exatamente {k_val}", total_busca)
    c2.metric("Grupos únicos",               len(grupos_p))
    c3.metric("Total CBs verificados",        total_cbs)
    c4.metric("Pares contidos (CR⊆CB)",       total_contem)

    if not grupos_p:
        st.info("Nenhum grupo encontrado.")
    else:
        larg_num = len(str(max(numeros_p))) if numeros_p else 2

        for g_idx, grupo in enumerate(grupos_p, start=1):
            chave      = grupo["grupo_elementos"]
            cbs_busca  = grupo["cbs_busca"]
            cbs_contem = grupo["cbs_contem"]

            larg_c    = len(str(max(chave))) if chave else 2
            chave_str = "{" + ", ".join(str(x).zfill(larg_c) for x in chave) + "}"

            nomes_busca = {m[0] for m in cbs_busca}
            n_super     = len([c for c in cbs_contem if c[0] not in nomes_busca])

            label = (
                f"Grupo {g_idx} — {chave_str} "
                f"| {len(cbs_busca)} com exatamente {k_val} "
                f"| +{n_super} superconjuntos "
                f"| {len(cbs_contem)} total (de {total_cbs})"
            )

            with st.expander(label, expanded=False):
                for nome, conj in cbs_contem:
                    html = highlight_html(conj.elementos, set(chave))
                    em_str = "{" + ", ".join(str(x).zfill(larg_num) for x in chave) + "}"
                    st.markdown(f"**{nome}** = {html}", unsafe_allow_html=True)
                    st.caption(f"em comum = {em_str}")
