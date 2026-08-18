"""
Frontend Streamlit — Verificador de Conjuntos Numéricos
Deploy gratuito: https://streamlit.io/cloud

Reutiliza toda a lógica de conjunto_numerico.py e main.py.
Para rodar localmente:
    pip install streamlit
    streamlit run streamlit_app.py
"""

import io
import random
from datetime import datetime

import streamlit as st

from conjunto_numerico import ConjuntoNumerico
from main import (
    gerar_conjuntos,
    carregar_conjuntos_txt,
    verificar_contencao_dados,
)


# ====================================================================== #
#  Session state                                                          #
# ====================================================================== #

if "conjuntos_filtrados" not in st.session_state:
    st.session_state.conjuntos_filtrados = None   # lista de (nome, conj) ou None


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
    """Lê um UploadedFile do Streamlit e retorna lista de (nome, ConjuntoNumerico)."""
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
            st.warning(f"Linha ignorada (formato inválido): {linha}")
    return conjuntos


def highlight_coincidentes(ref: ConjuntoNumerico, conj: ConjuntoNumerico) -> str:
    """
    Retorna o conjunto base como string HTML com os números
    coincidentes com ref em laranja e negrito.
    """
    ref_set = set(str(e).zfill(len(str(max(abs(int(x)) for x in ref.elementos))))
                  for e in ref.elementos)
    largura = len(str(max(abs(int(e)) for e in conj.elementos)))
    partes = []
    for e in conj.elementos:
        s = str(int(e)).zfill(largura)
        if s in ref_set:
            partes.append(f"<span style='color:#e67e00;font-weight:bold'>{s}</span>")
        else:
            partes.append(s)
    return "{" + ", ".join(partes) + "}"


def gerar_txt_resultado(contem, refs, conjuntos) -> str:
    """Gera o texto de resultado para download."""
    linhas = []
    linhas.append("═" * 52)
    linhas.append("   VERIFICAÇÃO DE CONTENÇÃO  (ref ⊆ conjunto?)")
    linhas.append("═" * 52)
    linhas.append(f"  Referências      : {len(refs)}")
    linhas.append(f"  Conjuntos base   : {len(conjuntos)}")
    linhas.append(f"  Pares encontrados: {len(contem)}")
    linhas.append("")
    linhas.append("─" * 52)
    linhas.append(f"  ✔  ref ⊆ conjunto  ({len(contem)})")
    linhas.append("─" * 52)
    for n_par, (i_ref, ref, nome, conj) in enumerate(contem, start=1):
        linhas.append(f"  {n_par}. CR{i_ref} ⊆ {nome}")
        linhas.append(f"    CR{i_ref} = {ref}")
        linhas.append(f"    {nome}  = {conj}")
    return "\n".join(linhas)


# ====================================================================== #
#  Sidebar — Conjuntos Base                                               #
# ====================================================================== #

with st.sidebar:
    st.header("⚙️ Configuração")

    # ── Conjuntos base ─────────────────────────────────────────────────
    st.subheader("Conjuntos Base")

    conjuntos = None
    x_log = y_log = tam_log = "—"

    if st.session_state.conjuntos_filtrados is not None:
        n_filt = len(st.session_state.conjuntos_filtrados)
        st.success(f"🔄 Nova rodada: usando {n_filt} conjuntos filtrados da rodada anterior.")
        if st.button("✕ Cancelar — voltar ao modo normal"):
            st.session_state.conjuntos_filtrados = None
            st.rerun()
    else:
        modo_base = st.radio("Origem:", ["Gerar aleatoriamente", "Carregar arquivo .txt"],
                             key="modo_base")

        if modo_base == "Gerar aleatoriamente":
            n_base   = st.number_input("Quantidade de conjuntos (N)", min_value=1, value=10, step=1)
            x_base   = st.number_input("Início do intervalo (x)", value=1, step=1)
            y_base   = st.number_input("Fim do intervalo (y)", value=30, step=1)
            tam_base = st.number_input("Tamanho dos conjuntos", min_value=1, value=10, step=1)
            x_log, y_log, tam_log = x_base, y_base, tam_base
        else:
            arq_base = st.file_uploader("Arquivo .txt (conjuntos base)", type="txt",
                                        key="upload_base")

    st.divider()

    # ── Conjuntos de referência ────────────────────────────────────────
    st.subheader("Conjuntos de Referência")
    modo_ref = st.radio("Origem:", ["Gerar aleatoriamente", "Carregar arquivo .txt"],
                        key="modo_ref")

    refs = None

    if modo_ref == "Gerar aleatoriamente":
        x_ref   = st.number_input("Início do intervalo (x)", value=1, step=1, key="xr")
        y_ref   = st.number_input("Fim do intervalo (y)", value=25, step=1, key="yr")
        tam_ref = st.number_input("Tamanho dos conjuntos", min_value=1, value=8, step=1, key="tr")
        qtd_ref = st.number_input("Quantidade de referências", min_value=1, value=3, step=1)
    else:
        arq_ref = st.file_uploader("Arquivo .txt (referências)", type="txt",
                                   key="upload_ref")

    st.divider()
    executar = st.button("▶ Executar verificação", use_container_width=True, type="primary")


# ====================================================================== #
#  Execução principal                                                     #
# ====================================================================== #

if executar:

    erros = []

    # Valida e monta conjuntos base
    if st.session_state.conjuntos_filtrados is not None:
        conjuntos = st.session_state.conjuntos_filtrados
        x_log = y_log = tam_log = "filtrado"
    elif modo_base == "Gerar aleatoriamente":
        amp = int(y_base) - int(x_base) + 1
        if y_base <= x_base:
            erros.append("Fim do intervalo (y) deve ser maior que início (x) nos conjuntos base.")
        elif amp < tam_base:
            erros.append(f"Intervalo [{int(x_base)}, {int(y_base)}] tem {amp} inteiros, "
                         f"mas tamanho pedido é {int(tam_base)}.")
        else:
            conjuntos = gerar_conjuntos(int(n_base), int(x_base), int(y_base), int(tam_base))
    else:
        if not arq_base:
            erros.append("Selecione um arquivo .txt para os conjuntos base.")
        else:
            conjuntos = carregar_de_upload(arq_base)
            if not conjuntos:
                erros.append("Nenhum conjunto válido encontrado no arquivo base.")


    # Valida e monta referências
    if modo_ref == "Gerar aleatoriamente":
        amp_r = int(y_ref) - int(x_ref) + 1
        if y_ref <= x_ref:
            erros.append("Fim do intervalo (y) deve ser maior que início (x) nas referências.")
        elif amp_r < tam_ref:
            erros.append(f"Intervalo [{int(x_ref)}, {int(y_ref)}] tem {amp_r} inteiros, "
                         f"mas tamanho pedido é {int(tam_ref)}.")
        else:
            refs = []
            for _ in range(int(qtd_ref)):
                elementos = sorted(random.sample(range(int(x_ref), int(y_ref) + 1), int(tam_ref)))
                refs.append(ConjuntoNumerico(elementos))
    else:
        if not arq_ref:
            erros.append("Selecione um arquivo .txt para as referências.")
        else:
            refs_raw = carregar_de_upload(arq_ref)
            if not refs_raw:
                erros.append("Nenhum conjunto válido encontrado no arquivo de referência.")
            else:
                refs = [conj for _, conj in refs_raw]

    if erros:
        for e in erros:
            st.error(e)
        st.stop()

    # ── Cálculo ────────────────────────────────────────────────────────
    contem = []
    nao_contem_count = 0
    for i, ref in enumerate(refs, start=1):
        for nome, conj in conjuntos:
            if ref.subconjunto(conj):
                contem.append((i, ref, nome, conj))
            else:
                nao_contem_count += 1

    total_pares = len(refs) * len(conjuntos)

    # ── Métricas ────────────────────────────────────────────────────────
    st.subheader("📊 Resumo")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Conjuntos base", len(conjuntos))
    col2.metric("Referências",    len(refs))
    col3.metric("Total de pares", total_pares)
    col4.metric("✔ Contidos",     len(contem))

    # ── Tabela de resultados ────────────────────────────────────────────
    st.subheader(f"✔ Pares contidos — CR ⊆ Conjunto Base ({len(contem)})")

    if not contem:
        st.info("Nenhum par de contenção encontrado.")
    else:
        # Campo de busca
        busca = st.text_input("🔍 Filtrar por nome (CB ou CR):", placeholder="ex: CB5  ou  CR2")

        filtrados = contem
        if busca.strip():
            termo = busca.strip().upper()
            filtrados = [
                (i, ref, nome, conj) for i, ref, nome, conj in contem
                if termo in nome.upper() or termo in f"CR{i}"
            ]
            st.caption(f"{len(filtrados)} resultado(s) para: {busca.strip()}")

        for n_par, (i_ref, ref, nome, conj) in enumerate(filtrados, start=1):
            with st.expander(f"{n_par}. CR{i_ref} ⊆ {nome}", expanded=False):
                st.markdown(f"**CR{i_ref}** = `{ref}`")
                cb_html = highlight_coincidentes(ref, conj)
                st.markdown(f"**{nome}** = {cb_html}", unsafe_allow_html=True)

    # ── Nova rodada ─────────────────────────────────────────────────────
    if contem:
        st.divider()
        vistos = set()
        novos_base = []
        for _, _, nome, conj in contem:
            if nome not in vistos:
                novos_base.append((nome, conj))
                vistos.add(nome)
        n_novos = len(novos_base)
        if st.button(f"🔄 Nova rodada com os {n_novos} conjuntos que contêm a referência",
                     type="primary"):
            st.session_state.conjuntos_filtrados = novos_base
            st.rerun()

    # ── Downloads ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("⬇️ Downloads")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    col_d1, col_d2, col_d3 = st.columns(3)

    txt_exec = gerar_txt_resultado(contem, refs, conjuntos)
    col_d1.download_button(
        "📄 Resultado completo",
        data=txt_exec.encode("utf-8"),
        file_name=f"execucao_{timestamp}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    linhas_base = ["Conjuntos Base\n" + "─" * 52, f"{'Nome':<8} Elementos", "─" * 52]
    for nome, conj in conjuntos:
        linhas_base.append(f"{nome:<8} {conj}")
    col_d2.download_button(
        "📄 Conjuntos base",
        data="\n".join(linhas_base).encode("utf-8"),
        file_name=f"conjuntos_base_{timestamp}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    linhas_ref = ["Conjuntos de Referência\n" + "─" * 52, f"{'ID':<8} Elementos", "─" * 52]
    for i, ref in enumerate(refs, start=1):
        linhas_ref.append(f"CR{i:<6} {ref}")
    col_d3.download_button(
        "📄 Conjuntos referência",
        data="\n".join(linhas_ref).encode("utf-8"),
        file_name=f"conjuntos_ref_{timestamp}.txt",
        mime="text/plain",
        use_container_width=True,
    )
