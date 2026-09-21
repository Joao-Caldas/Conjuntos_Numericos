"""
Frontend (Tkinter) para o Verificador de Conjuntos Numéricos.

Reaproveita toda a lógica já existente em conjunto_numerico.py e main.py
(gerar_conjuntos, carregar_conjuntos_txt, exibir_conjuntos, verificar_contencao),
apenas substituindo a entrada/saída de terminal por uma interface gráfica.

Para executar:
    python app.py

Requer apenas a biblioteca padrão do Python (tkinter já vem incluso).
"""

import os
import re
import sys
import random
import queue
import threading
from io import StringIO
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from conjunto_numerico import ConjuntoNumerico
from main import (
    gerar_conjuntos,
    carregar_conjuntos_txt,
    exibir_conjuntos,
    verificar_contencao,
    verificar_contencao_dados,
    parsear_numeros,
    buscar_por_coincidencia,
    buscar_grupos_e_verificar_contencao,
    buscar_todos_grupos_possiveis,
    agrupar_cbs_por_subconjunto,
    comparar_dois_conjuntos,
    filtrar_cbs_por_grupo,
    extrair_cbs_do_texto,
)


# ====================================================================== #
#  Aplicação principal                                                    #
# ====================================================================== #

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Verificador de Conjuntos Numéricos")
        self.geometry("980x720")
        self.minsize(860, 600)

        # Fila usada para trazer o resultado da thread de trabalho
        # de volta para a thread principal (única que pode tocar widgets).
        self._fila_resultado = queue.Queue()
        self._conjuntos_filtrados = None
        self._contem_para_nova_rodada = []

        self._construir_ui()


    # ------------------------------------------------------------------ #
    #  Busca no resultado                                                 #
    # ------------------------------------------------------------------ #

    def _buscar(self, direcao: int = 1):
        """
        Destaca todas as ocorrências do termo no widget de saída.
        direcao=1 avança, direcao=-1 recua.
        """
        termo = self.ent_busca.get()

        # Limpa destaques anteriores
        self.txt_saida.tag_remove("busca", "1.0", tk.END)
        self.txt_saida.tag_remove("busca_atual", "1.0", tk.END)
        self._ocorrencias_busca = []
        self._idx_busca = -1

        if not termo:
            self.lbl_busca.config(text="")
            return

        # Encontra todas as ocorrências
        inicio = "1.0"
        while True:
            pos = self.txt_saida.search(termo, inicio, nocase=True, stopindex=tk.END)
            if not pos:
                break
            fim = f"{pos}+{len(termo)}c"
            self.txt_saida.tag_add("busca", pos, fim)
            self._ocorrencias_busca.append(pos)
            inicio = fim

        total = len(self._ocorrencias_busca)

        if total == 0:
            self.lbl_busca.config(text="Nenhum resultado.")
            return

        # Navega para a ocorrência na direção pedida
        self._idx_busca = (self._idx_busca + direcao) % total
        self._ir_para_ocorrencia()

    def _ir_para_ocorrencia(self):
        """Destaca e exibe a ocorrência atual."""
        self.txt_saida.tag_remove("busca_atual", "1.0", tk.END)

        pos = self._ocorrencias_busca[self._idx_busca]
        termo = self.ent_busca.get()
        fim = f"{pos}+{len(termo)}c"

        self.txt_saida.tag_add("busca_atual", pos, fim)
        self.txt_saida.see(pos)

        total = len(self._ocorrencias_busca)
        self.lbl_busca.config(text=f"{self._idx_busca + 1} / {total}")

    # ------------------------------------------------------------------ #
    #  Construção da interface                                            #
    # ------------------------------------------------------------------ #

    def _construir_ui(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        # ── Banner de nova rodada (escondido por padrão) ─────────────────
        self.frame_nova_rodada = tk.Frame(container, bg="#2ecc71", pady=8)
        self.lbl_nova_rodada = tk.Label(
            self.frame_nova_rodada,
            text="", bg="#2ecc71", fg="white",
            font=("Helvetica", 11, "bold")
        )
        self.lbl_nova_rodada.pack()
        # começa escondido
        self.frame_nova_rodada.pack_forget()

        # ── Duas colunas: Conjuntos Base | Conjuntos Referência ─────────
        colunas = ttk.Frame(container)
        colunas.pack(fill="x")
        colunas.columnconfigure(0, weight=1)
        colunas.columnconfigure(1, weight=1)

        self.painel_base = self._criar_painel_conjunto(
            colunas, titulo="Conjuntos Base", prefixo="base"
        )
        self.painel_base.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.painel_ref = self._criar_painel_conjunto(
            colunas, titulo="Conjuntos de Referência", prefixo="ref",
            campo_extra=("Quantidade de referências:", "qtd")
        )
        self.painel_ref.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # ── Botão executar ──────────────────────────────────────────────
        barra_acoes = ttk.Frame(container)
        barra_acoes.pack(fill="x", pady=10)

        self.btn_executar = ttk.Button(
            barra_acoes, text="▶  Executar verificação", command=self._executar
        )
        self.btn_executar.pack(side="left")

        self.lbl_status = ttk.Label(barra_acoes, text="Pronto.", foreground="#555")
        self.lbl_status.pack(side="left", padx=12)

        self.btn_nova_rodada = ttk.Button(
            barra_acoes, text="🔄 Nova rodada com conjuntos contidos",
            command=self._iniciar_nova_rodada, state="disabled"
        )
        self.btn_nova_rodada.pack(side="left", padx=(12, 0))

        self.btn_cancelar_rodada = ttk.Button(
            barra_acoes, text="✕ Cancelar nova rodada",
            command=self._cancelar_nova_rodada, state="disabled"
        )
        self.btn_cancelar_rodada.pack(side="left", padx=(4, 0))

        # ── Área de saída ────────────────────────────────────────────────
        # ── Busca por coincidência parcial ───────────────────────────────
        # frame_busca_parcial = ttk.LabelFrame(container, text="Busca por coincidência parcial", padding=8)
        # frame_busca_parcial.pack(fill="x", pady=(0, 6))

        # ttk.Label(frame_busca_parcial, text="Números (ex: 01, 02, 03):").grid(row=0, column=0, sticky="w", padx=(0, 6))
        # self.ent_parcial_nums = ttk.Entry(frame_busca_parcial, width=60)
        # self.ent_parcial_nums.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        # frame_busca_parcial.columnconfigure(1, weight=1)

        # ttk.Label(frame_busca_parcial, text="Coincidências exatas:").grid(row=0, column=2, sticky="w", padx=(0, 6))
        # self.ent_parcial_k = ttk.Entry(frame_busca_parcial, width=6)
        # self.ent_parcial_k.insert(0, "15")
        # self.ent_parcial_k.grid(row=0, column=3, sticky="w", padx=(0, 10))

        # ttk.Button(frame_busca_parcial, text="🔍 Buscar",
        #            command=self._buscar_parcial).grid(row=0, column=4, sticky="w", padx=(0,4))


        # ── Verificação de grupo manual ──────────────────────────────────
        frame_grupo_manual = ttk.LabelFrame(
            container, text="🎯 Verificar grupo específico", padding=8
        )
        frame_grupo_manual.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_grupo_manual, text="Números ou IDs (CB1, CB2...):").grid(
            row=0, column=0, sticky="w", padx=(0, 6)
        )
        self.ent_grupo_manual = ttk.Entry(frame_grupo_manual, width=60)
        self.ent_grupo_manual.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        frame_grupo_manual.columnconfigure(1, weight=1)

        ttk.Button(
            frame_grupo_manual, text="🎯 Verificar",
            command=self._verificar_grupo_manual
        ).grid(row=0, column=2, sticky="w")

        # ── Comparação entre CBs ─────────────────────────────────────────
        frame_comparar = ttk.LabelFrame(
            container, text="🔁 Comparação entre CBs (par a par)", padding=8
        )
        frame_comparar.pack(fill="x", pady=(0, 6))

        ttk.Label(frame_comparar, text="K idênticos exatos:").grid(row=0, column=0, sticky="w", padx=(0,6))
        self.ent_comp_k = ttk.Entry(frame_comparar, width=6)
        self.ent_comp_k.insert(0, "15")
        self.ent_comp_k.grid(row=0, column=1, sticky="w", padx=(0,10))

        ttk.Label(frame_comparar, text="Mostrar grupos com ≥ conjuntos:").grid(row=0, column=2, sticky="w", padx=(0,6))
        self.ent_comp_min = ttk.Entry(frame_comparar, width=6)
        self.ent_comp_min.insert(0, "2")
        self.ent_comp_min.grid(row=0, column=3, sticky="w", padx=(0,10))

        ttk.Button(
            frame_comparar, text="🔁 Comparar",
            command=self._comparar_cbs
        ).grid(row=0, column=4, sticky="w")

        # # ── Nova comparação a partir de grupo colado ─────────────────────
        # frame_nova_comp = ttk.LabelFrame(
        #     container, text="📋 Nova comparação a partir de grupo colado", padding=8
        # )
        # frame_nova_comp.pack(fill="x", pady=(0, 6))

        # ttk.Label(frame_nova_comp, text="Cole o grupo:").grid(row=0, column=0, sticky="w", padx=(0,6))
        # self.ent_grupo_colado = ttk.Entry(frame_nova_comp, width=55)
        # self.ent_grupo_colado.grid(row=0, column=1, sticky="ew", padx=(0,8))
        # frame_nova_comp.columnconfigure(1, weight=1)

        # ttk.Label(frame_nova_comp, text="Novo K:").grid(row=0, column=2, sticky="w", padx=(0,4))
        # self.ent_nova_k = ttk.Entry(frame_nova_comp, width=5)
        # self.ent_nova_k.insert(0, "14")
        # self.ent_nova_k.grid(row=0, column=3, sticky="w", padx=(0,8))

        # ttk.Label(frame_nova_comp, text="≥ conjuntos:").grid(row=0, column=4, sticky="w", padx=(0,4))
        # self.ent_nova_min = ttk.Entry(frame_nova_comp, width=5)
        # self.ent_nova_min.insert(0, "2")
        # self.ent_nova_min.grid(row=0, column=5, sticky="w", padx=(0,8))

        # ttk.Button(
        #     frame_nova_comp, text="🔁 Comparar grupo",
        #     command=self._nova_comp_grupo_colado
        # ).grid(row=0, column=6, sticky="w")

        # ── Label "Resultado:" + barra de busca na mesma linha ────────────
        barra_resultado = ttk.Frame(container)
        barra_resultado.pack(fill="x", pady=(0, 2))

        ttk.Label(barra_resultado, text="Resultado:").pack(side="left")

        self.lbl_busca = ttk.Label(barra_resultado, text="", foreground="#555")
        self.lbl_busca.pack(side="right", padx=(4, 0))

        ttk.Button(barra_resultado, text="▼", width=3,
                   command=lambda: self._buscar(direcao=1)).pack(side="right", padx=2)
        ttk.Button(barra_resultado, text="▲", width=3,
                   command=lambda: self._buscar(direcao=-1)).pack(side="right", padx=2)

        self.ent_busca = ttk.Entry(barra_resultado, width=25)
        self.ent_busca.pack(side="right", padx=(6, 4))
        self.ent_busca.bind("<Return>", lambda e: self._buscar(direcao=1))
        self.ent_busca.bind("<Shift-Return>", lambda e: self._buscar(direcao=-1))

        ttk.Label(barra_resultado, text="🔍 Buscar:").pack(side="right", padx=(8, 0))
        self.txt_saida = scrolledtext.ScrolledText(
            container, wrap="word", font=("Consolas", 10), height=24
        )
        self.txt_saida.pack(fill="both", expand=True, pady=(4, 0))
        self.txt_saida.tag_config("busca", background="#ffe066")
        self.txt_saida.tag_config("busca_atual", background="#ff9900")

        self._ocorrencias_busca = []
        self._idx_busca = -1

    def _criar_painel_conjunto(self, parent, titulo, prefixo, campo_extra=None):
        """
        Cria um painel (LabelFrame) com as opções de geração/carregamento
        de um conjunto de dados (base ou referência).
        """
        frame = ttk.LabelFrame(parent, text=titulo, padding=10)

        modo = tk.StringVar(value="random")
        setattr(self, f"modo_{prefixo}", modo)

        ttk.Radiobutton(
            frame, text="Gerar aleatoriamente", variable=modo, value="random",
            command=lambda: self._alternar_modo(prefixo)
        ).grid(row=0, column=0, sticky="w", columnspan=2)

        ttk.Radiobutton(
            frame, text="Carregar de arquivo .txt", variable=modo, value="file",
            command=lambda: self._alternar_modo(prefixo)
        ).grid(row=1, column=0, sticky="w", columnspan=2)

        # ── Sub-painel: geração aleatória ────────────────────────────
        frame_random = ttk.Frame(frame)
        setattr(self, f"frame_random_{prefixo}", frame_random)

        linha = 0
        if prefixo == "base":
            ttk.Label(frame_random, text="Quantidade de conjuntos (N):").grid(
                row=linha, column=0, sticky="w", pady=2
            )
            ent_n = ttk.Entry(frame_random, width=10)
            ent_n.grid(row=linha, column=1, sticky="w", pady=2)
            setattr(self, f"ent_{prefixo}_n", ent_n)
            linha += 1

        ttk.Label(frame_random, text="Início do intervalo (x):").grid(
            row=linha, column=0, sticky="w", pady=2
        )
        ent_x = ttk.Entry(frame_random, width=10)
        ent_x.grid(row=linha, column=1, sticky="w", pady=2)
        setattr(self, f"ent_{prefixo}_x", ent_x)
        linha += 1

        ttk.Label(frame_random, text="Fim do intervalo (y):").grid(
            row=linha, column=0, sticky="w", pady=2
        )
        ent_y = ttk.Entry(frame_random, width=10)
        ent_y.grid(row=linha, column=1, sticky="w", pady=2)
        setattr(self, f"ent_{prefixo}_y", ent_y)
        linha += 1

        ttk.Label(frame_random, text="Tamanho dos conjuntos:").grid(
            row=linha, column=0, sticky="w", pady=2
        )
        ent_tam = ttk.Entry(frame_random, width=10)
        ent_tam.grid(row=linha, column=1, sticky="w", pady=2)
        setattr(self, f"ent_{prefixo}_tamanho", ent_tam)
        linha += 1

        if campo_extra:
            label_extra, chave_extra = campo_extra
            ttk.Label(frame_random, text=label_extra).grid(
                row=linha, column=0, sticky="w", pady=2
            )
            ent_extra = ttk.Entry(frame_random, width=10)
            ent_extra.grid(row=linha, column=1, sticky="w", pady=2)
            setattr(self, f"ent_{prefixo}_{chave_extra}", ent_extra)
            linha += 1

        frame_random.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # ── Sub-painel: carregar arquivo ─────────────────────────────
        frame_file = ttk.Frame(frame)
        setattr(self, f"frame_file_{prefixo}", frame_file)

        ttk.Label(frame_file, text="Arquivo .txt:").grid(row=0, column=0, sticky="w")
        ent_arquivo = ttk.Entry(frame_file, width=32)
        ent_arquivo.grid(row=1, column=0, sticky="w", pady=2)
        setattr(self, f"ent_{prefixo}_arquivo", ent_arquivo)

        ttk.Button(
            frame_file, text="Procurar...",
            command=lambda: self._procurar_arquivo(ent_arquivo)
        ).grid(row=1, column=1, sticky="w", padx=(6, 0))

        frame_file.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        frame_file.grid_remove()   # começa escondido (modo padrão = random)

        return frame

    # ------------------------------------------------------------------ #
    #  Eventos de interface                                               #
    # ------------------------------------------------------------------ #

    def _alternar_modo(self, prefixo):
        """Mostra o sub-painel correspondente ao modo escolhido (random/file)."""
        modo = getattr(self, f"modo_{prefixo}").get()
        frame_random = getattr(self, f"frame_random_{prefixo}")
        frame_file = getattr(self, f"frame_file_{prefixo}")

        if modo == "random":
            frame_file.grid_remove()
            frame_random.grid()
        else:
            frame_random.grid_remove()
            frame_file.grid()

    def _procurar_arquivo(self, entry: ttk.Entry):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo .txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            entry.delete(0, tk.END)
            entry.insert(0, caminho)


    def _iniciar_nova_rodada(self):
        """
        Esconde o painel base, exibe banner verde com os CBs filtrados
        e aguarda o usuário configurar novas referências.
        """
        try:
            self._conjuntos_filtrados = list(self._contem_para_nova_rodada)
            n = len(self._conjuntos_filtrados)

            # Esconde painel base e mostra banner
            self.painel_base.grid_remove()
            nomes = ", ".join(nome for nome, _ in self._conjuntos_filtrados[:6])
            if n > 6:
                nomes += f" ... (+{n - 6})"
            self.lbl_nova_rodada.config(
                text=f"🔄 Nova rodada — {n} conjuntos base filtrados: {nomes}"
            )
            self.frame_nova_rodada.pack(fill="x", before=self.painel_ref.master, pady=(0, 6))

            self.btn_nova_rodada.state(["disabled"])
            self.btn_cancelar_rodada.state(["!disabled"])
            self.lbl_status.config(
                text=f"✔ {n} conjuntos filtrados. Configure as novas referências e execute."
            )
            self.txt_saida.delete("1.0", tk.END)

        except Exception as e:
            messagebox.showerror("Erro na nova rodada", str(e))

    def _cancelar_nova_rodada(self):
        """Restaura o painel base e volta ao modo normal."""
        self._conjuntos_filtrados = None
        self._contem_para_nova_rodada = []

        # Mostra painel base e esconde banner
        self.frame_nova_rodada.pack_forget()
        self.painel_base.grid()

        self.btn_cancelar_rodada.state(["disabled"])
        self.btn_nova_rodada.state(["disabled"])
        self.btn_nova_rodada.config(text="🔄 Nova rodada com conjuntos contidos")
        self.lbl_status.config(text="Pronto.")


    # ------------------------------------------------------------------ #
    #  Busca por coincidência parcial                                     #
    # ------------------------------------------------------------------ #





    def _nova_comp_grupo_colado(self):
        """
        Filtra os CBs que contêm o grupo colado e compara entre si com novo K.
        """
        if not hasattr(self, "_conjuntos_atuais") or not self._conjuntos_atuais:
            messagebox.showwarning("Atenção", "Execute a verificação principal primeiro.")
            return

        texto = self.ent_grupo_colado.get().strip()
        if not texto:
            messagebox.showwarning("Atenção", "Cole um grupo no campo.")
            return

        try:
            k_nova  = int(self.ent_nova_k.get().strip())
            mn_nova = int(self.ent_nova_min.get().strip())
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        conjuntos = self._conjuntos_atuais
        cbs_filt  = extrair_cbs_do_texto(texto, conjuntos)

        if not cbs_filt:
            messagebox.showinfo("Resultado",
                "Nenhum CB encontrado no texto colado.\n\n"
                "Formatos aceitos:\n"
                "• Bloco completo do output (com CB447 × CB694 ...)\n"
                "• Lista de IDs: CB1, CB2, CB3, ...\n"
                "• Números: 01, 02, 03, ...")
            return

        n_f = len(cbs_filt)
        self.txt_saida.delete("1.0", tk.END)
        self.btn_executar.state(["disabled"])
        self.lbl_status.config(
            text=f"{n_f} CBs contêm o grupo. Comparando {n_f*(n_f-1)//2:,} pares com K={k_nova}..."
        )

        import threading, queue as _q
        fila = _q.Queue()

        def _trabalho():
            grupos = []
            try:
                grupos = agrupar_cbs_por_subconjunto(k_nova, cbs_filt, min_cbs=1)
            except Exception:
                pass
            finally:
                fila.put((grupos, k_nova, mn_nova, cbs_filt))

        threading.Thread(target=_trabalho, daemon=True).start()

        def _poll():
            try:
                grupos, _k, _mn, _cbs = fila.get_nowait()
            except __import__("queue").Empty:
                self.after(200, _poll)
                return

            SEP      = "─" * 52
            filtrados = [g for g in grupos if len(g["cbs"]) >= _mn]
            total_p   = sum(len(g.get("lista_cbs", [])) for g in grupos)
            self.txt_saida.tag_config("grupo_header",
                foreground="#1a6fbe", font=("Consolas", 10, "bold"))
            self.txt_saida.tag_config("parcial_match",
                foreground="#e67e00", font=("Consolas", 10, "bold"))

            w = lambda t, tag="": self.txt_saida.insert(tk.END, t, tag)

            w("\n" + "═" * 52 + "\n")
            w("   NOVA COMPARAÇÃO — GRUPO COLADO\n")
            w("═" * 52 + "\n")
            nomes_filt = ', '.join(n for n, _ in _cbs)
            w(f"  CBs selecionados ({len(_cbs)}): {nomes_filt}\n")
            w(f"  Novo K          : {_k}\n")
            w(f"  Grupos únicos   : {len(grupos):,}\n")
            w(f"  Total membros   : {total_p:,}\n")
            w(f"  Exibindo (≥{_mn} conjuntos): {len(filtrados):,}\n")

            if not filtrados:
                w("\n  Nenhum grupo com esse critério.\n")
            else:
                larg = len(str(max(e for g in filtrados for e in g["elementos_comuns"])))
                for g_idx, grupo in enumerate(filtrados, start=1):
                    chave  = grupo["elementos_comuns"]
                    cbs_g  = sorted(grupo["cbs"])
                    ch_str = "{" + ", ".join(str(x).zfill(larg) for x in chave) + "}"
                    w(f"\n{SEP}\n")
                    w(f"  Grupo {g_idx}  —  {ch_str}\n", "grupo_header")
                    w(f"  {len(cbs_g)} conjuntos: {', '.join(cbs_g)}\n", "grupo_header")
                    w(f"{SEP}\n")
                    for nome, conj in grupo.get("lista_cbs", []):
                        w(f"\n  {nome}\n")
                        w(f"    {nome} = {{")
                        larg2 = len(str(max(abs(int(e)) for e in conj.elementos)))
                        for idx2, e in enumerate(conj.elementos):
                            s   = str(int(e)).zfill(larg2)
                            tag = "parcial_match" if int(e) in set(chave) else ""
                            w(s, tag)
                            if idx2 < len(conj.elementos) - 1:
                                w(", ")
                        w("}\n")

            self.txt_saida.see("1.0")
            self.btn_executar.state(["!disabled"])
            self.lbl_status.config(
                text=f"Nova comparação: {len(_cbs)} CBs filtrados · "
                     f"{len(grupos):,} grupos · {len(filtrados)} exibidos (≥{_mn} conjuntos)."
            )

        self.after(200, _poll)

    def _comparar_cbs(self):
        """Compara entre si os CBs atualmente carregados (conjunto ativo)."""
        if not hasattr(self, "_conjuntos_atuais") or not self._conjuntos_atuais:
            messagebox.showwarning("Atenção", "Execute a verificação principal primeiro.")
            return
        try:
            k  = int(self.ent_comp_k.get().strip())
            mn = int(self.ent_comp_min.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "K e mínimo de conjuntos devem ser inteiros.")
            return

        conjuntos = self._conjuntos_atuais
        n = len(conjuntos)
        self.txt_saida.delete("1.0", tk.END)
        self.btn_executar.state(["disabled"])
        self.lbl_status.config(text=f"Agrupando subconjuntos de {n} CBs com K={k}... aguarde.")

        import threading, queue as _q
        fila = _q.Queue()

        def _trabalho():
            grupos = []
            erro_msg = ""
            try:
                grupos = agrupar_cbs_por_subconjunto(k, conjuntos, min_cbs=1)
            except Exception as e:
                erro_msg = str(e)
            finally:
                fila.put((grupos, k, mn, erro_msg))

        threading.Thread(target=_trabalho, daemon=True).start()

        def _poll():
            try:
                grupos, _k, _mn, _erro = fila.get_nowait()
            except __import__("queue").Empty:
                self.after(300, _poll)
                return
            if _erro:
                messagebox.showwarning("Erro", _erro)
            else:
                self._renderizar_comparacao(grupos, _k, _mn, conjuntos)
            self.btn_executar.state(["!disabled"])

        self.after(300, _poll)

    def _renderizar_comparacao(self, grupos, k, min_cbs, conjuntos):
        SEP = "─" * 52
        filtrados = [g for g in grupos if len(g["cbs"]) >= min_cbs]
        total_membros = sum(len(g.get("lista_cbs", [])) for g in grupos)

        self.txt_saida.tag_config("grupo_header",
            foreground="#1a6fbe", font=("Consolas", 10, "bold"))
        self.txt_saida.tag_config("parcial_match",
            foreground="#e67e00", font=("Consolas", 10, "bold"))

        w = lambda t, tag="": self.txt_saida.insert(tk.END, t, tag)

        w("\n" + "═" * 52 + "\n")
        w("   COMPARAÇÃO ENTRE CBs (PAR A PAR)\n")
        w("═" * 52 + "\n")
        w(f"  K idênticos exatos       : {k}\n")
        w(f"  Total de CBs: {len(conjuntos)}\n")
        w(f"  Grupos únicos encontrados: {len(grupos):,}\n")
        w(f"  Total de membros nos grupos: {total_membros:,}\n")
        w(f"  Exibindo grupos com ≥ {min_cbs} conjuntos: {len(filtrados):,}\n")

        if not filtrados:
            w("\n  Nenhum grupo com esse critério.\n")
        else:
            larg = len(str(max(e for g in filtrados for e in g["elementos_comuns"])))
            for g_idx, grupo in enumerate(filtrados, start=1):
                chave  = grupo["elementos_comuns"]
                membros = grupo.get("lista_cbs", [])
                cbs    = sorted(grupo["cbs"])
                ch_str = "{" + ", ".join(str(x).zfill(larg) for x in chave) + "}"

                w(f"\n{SEP}\n")
                w(f"  Grupo {g_idx}  —  {ch_str}\n", "grupo_header")
                w(f"  {len(cbs)} conjuntos: {', '.join(cbs)}\n", "grupo_header")
                w(f"{SEP}\n")

                for nome, conj in membros:
                    w(f"\n  {nome}\n")
                    w(f"    {nome} = {{")
                    larg2 = len(str(max(abs(int(e)) for e in conj.elementos)))
                    for idx2, e in enumerate(conj.elementos):
                        s   = str(int(e)).zfill(larg2)
                        tag = "parcial_match" if int(e) in set(chave) else ""
                        w(s, tag)
                        if idx2 < len(conj.elementos) - 1:
                            w(", ")
                    w("}\n")

        self.txt_saida.see("1.0")
        self.lbl_status.config(
            text=f"Comparação: {len(grupos):,} grupos · exibindo {len(filtrados):,} com ≥{min_cbs} conjuntos."
        )

    def _verificar_grupo_manual(self):
        """
        Aceita:
          • CB IDs  → define esses CBs como novo conjunto base
          • Números → verifica quais CBs os contêm (comportamento original)
        """
        if not hasattr(self, "_conjuntos_atuais") or not self._conjuntos_atuais:
            messagebox.showwarning("Atenção", "Execute a verificação principal primeiro.")
            return

        texto = self.ent_grupo_manual.get().strip()
        if not texto:
            messagebox.showwarning("Atenção", "Digite ou cole os dados no campo.")
            return

        import re as _re
        tem_ids = bool(_re.search(r"CB\d+", texto))

        if tem_ids:
            # CB IDs → atualiza conjunto base
            cbs = extrair_cbs_do_texto(texto, self._conjuntos_atuais)
            if not cbs:
                messagebox.showwarning("Atenção", "Nenhum CB reconhecido no texto colado.")
                return

            self._conjuntos_atuais = cbs
            nomes = ", ".join(n for n, _ in cbs)
            self.txt_saida.delete("1.0", tk.END)
            w = lambda t, tag="": self.txt_saida.insert(tk.END, t, tag)
            self.txt_saida.tag_config("grupo_header",
                foreground="#1a6fbe", font=("Consolas", 10, "bold"))
            w("\n" + "═" * 52 + "\n")
            w("   NOVO CONJUNTO BASE DEFINIDO\n")
            w("═" * 52 + "\n")
            w(f"  {len(cbs)} conjuntos selecionados:\n", "grupo_header")
            w(f"  {nomes}\n")
            w("\n  ✔ Todas as operações agora usam esses CBs.\n")
            w("    (busca parcial, comparação, etc.)\n")
            self.txt_saida.see("1.0")
            self.lbl_status.config(
                text=f"Novo conjunto base: {len(cbs)} CB(s) — {nomes[:60]}{'...' if len(nomes)>60 else ''}"
            )

        else:
            # Números → verifica contenção (comportamento original)
            try:
                nums_gm = parsear_numeros(texto)
                ref_gm  = ConjuntoNumerico(sorted(nums_gm))
            except ValueError as e:
                messagebox.showerror("Entrada inválida", str(e))
                return

            conjuntos   = self._conjuntos_atuais
            encontrados = [(nome, conj) for nome, conj in conjuntos if ref_gm.subconjunto(conj)]

            SEP      = "─" * 52
            larg_gm  = len(str(max(nums_gm))) if nums_gm else 2
            grupo_str = "{" + ", ".join(str(x).zfill(larg_gm) for x in sorted(nums_gm)) + "}"

            self.txt_saida.delete("1.0", tk.END)
            self.txt_saida.tag_config("parcial_match",
                foreground="#e67e00", font=("Consolas", 10, "bold"))
            self.txt_saida.tag_config("grupo_header",
                foreground="#1a6fbe", font=("Consolas", 10, "bold"))

            w = lambda t, tag="": self.txt_saida.insert(tk.END, t, tag)

            w("\n" + "═" * 52 + "\n")
            w("   VERIFICAÇÃO DE GRUPO ESPECÍFICO\n")
            w("═" * 52 + "\n")
            w(f"  Grupo     : {grupo_str}\n")
            w(f"  Tamanho   : {len(nums_gm)} elementos\n")
            w(f"  Verificado em: {len(conjuntos)} CBs\n")
            w(f"  CBs que contêm: {len(encontrados)}\n")
            w(SEP + "\n")

            if not encontrados:
                w("\n  Nenhum CB contém esse grupo.\n")
            else:
                for i, (nome, conj) in enumerate(encontrados, start=1):
                    w(f"\n  {i}. {nome}\n")
                    w(f"    conjunto = {{")
                    larg = len(str(max(abs(int(e)) for e in conj.elementos)))
                    for j, e in enumerate(conj.elementos):
                        s   = str(int(e)).zfill(larg)
                        tag = "parcial_match" if int(e) in nums_gm else ""
                        w(s, tag)
                        if j < len(conj.elementos) - 1:
                            w(", ")
                    w("}\n")
                    em_str = ", ".join(str(x).zfill(larg_gm) for x in sorted(nums_gm))
                    w(f"    em comum  = {{{em_str}}}\n")

            self.txt_saida.see("1.0")
            self.lbl_status.config(
                text=f"Grupo: {len(encontrados)} CB(s) contêm o grupo (de {len(conjuntos)})."
            )

    def _buscar_parcial(self):
        """
        1. Encontra CBs com exatamente K coincidências.
        2. Agrupa os que têm os mesmos K elementos.
        3. Para cada grupo, verifica TODOS os CBs (não só os encontrados)
           e exibe quais os contêm como subconjunto.
        """
        if not hasattr(self, "_conjuntos_atuais") or not self._conjuntos_atuais:
            messagebox.showwarning("Atenção", "Execute a verificação principal primeiro.")
            return

        texto = self.ent_parcial_nums.get().strip()
        if not texto:
            messagebox.showwarning("Atenção", "Digite os números para buscar.")
            return

        try:
            numeros = parsear_numeros(texto)
            k = int(self.ent_parcial_k.get().strip())
        except ValueError as e:
            messagebox.showerror("Entrada inválida", str(e))
            return

        if k < 1 or k > len(numeros):
            messagebox.showerror("Entrada inválida",
                f"Mínimo deve estar entre 1 e {len(numeros)}.")
            return

        conjuntos = self._conjuntos_atuais

        self.txt_saida.delete("1.0", tk.END)
        self.btn_executar.state(["disabled"])
        self.lbl_status.config(text="Buscando grupos e verificando contenção em todos os CBs...")

        import threading, queue as _q
        fila = _q.Queue()

        def _trabalho():
            import sys, io
            buf = io.StringIO()
            orig = sys.stdout
            sys.stdout = buf
            grupos = []
            try:
                grupos = buscar_todos_grupos_possiveis(numeros, k, conjuntos)
            except Exception as e:
                print(f"\n  ✗ Erro: {e}")
            finally:
                sys.stdout = orig
                fila.put((buf.getvalue(), grupos, numeros, k))

        threading.Thread(target=_trabalho, daemon=True).start()

        def _poll():
            try:
                _, grupos, _numeros, _k = fila.get_nowait()
            except __import__("queue").Empty:
                self.after(150, _poll)
                return

            self._renderizar_grupos_parciais(grupos, _numeros, _k, conjuntos)
            self.btn_executar.state(["!disabled"])

        self.after(150, _poll)

    def _renderizar_grupos_parciais(self, grupos, numeros, k, conjuntos):
        """Renderiza o resultado de buscar_grupos_e_verificar_contencao."""
        SEP  = "─" * 52

        self.txt_saida.tag_config("parcial_match",
            foreground="#e67e00", font=("Consolas", 10, "bold"))
        self.txt_saida.tag_config("grupo_header",
            foreground="#1a6fbe", font=("Consolas", 10, "bold"))

        w = lambda t, tag="": self.txt_saida.insert(tk.END, t, tag)

        n_total_cbs  = len(conjuntos)
        n_grupos     = len(grupos)
        total_contem = sum(len(g["cbs_contem"]) for g in grupos)
        larg_num     = len(str(max(numeros))) if numeros else 2

        w("\n" + "═" * 52 + "\n")
        w("   BUSCA PARCIAL — TODOS OS GRUPOS POSSÍVEIS\n")
        w("═" * 52 + "\n")
        w(f"  Números buscados ({len(numeros)}): {sorted(numeros)}\n")
        w(f"  K (coincidências exatas)    : {k}\n")
        w(f"  Total de CBs verificados    : {n_total_cbs}\n")
        w(f"  Grupos únicos encontrados   : {n_grupos}\n")
        w(f"  Total pares contidos (CR⊆CB): {total_contem}\n")

        if not grupos:
            w("\n  Nenhum grupo encontrado com esse critério.\n")
            self.lbl_status.config(text="Busca parcial: nenhum resultado.")
            self.txt_saida.see("1.0")
            return

        n_par = 0
        for g_idx, grupo in enumerate(grupos, start=1):
            chave        = grupo["grupo_elementos"]
            cbs_busca    = grupo["cbs_busca"]
            cbs_contem   = grupo["cbs_contem"]

            larg_c    = len(str(max(chave))) if chave else 2
            chave_str = "{" + ", ".join(str(x).zfill(larg_c) for x in chave) + "}"

            w(f"\n{SEP}\n")
            w(f"  Grupo {g_idx}  —  {chave_str}\n", "grupo_header")
            n_superconj = len([c for c in cbs_contem
                               if c[0] not in {m[0] for m in cbs_busca}])
            w(f"  CBs com exatamente {k}: {len(cbs_busca)}"
              f"  |  superconjuntos que também contêm: {n_superconj}"
              f"  |  total que contêm: {len(cbs_contem)} (de {len(conjuntos)})\n",
              "grupo_header")
            w(f"{SEP}\n")

            for nome, conj in cbs_contem:
                n_par += 1
                w(f"\n  {n_par}. {nome}\n")
                w(f"    conjunto = {{")
                larg = len(str(max(abs(int(e)) for e in conj.elementos)))
                for i, e in enumerate(conj.elementos):
                    s   = str(int(e)).zfill(larg)
                    tag = "parcial_match" if int(e) in set(chave) else ""
                    w(s, tag)
                    if i < len(conj.elementos) - 1:
                        w(", ")
                w("}\n")
                em_str = ", ".join(str(x).zfill(larg_num) for x in chave)
                w(f"    em comum  = {{{em_str}}}\n")

        self.txt_saida.see("1.0")
        self.lbl_status.config(
            text=f"Busca parcial: {n_grupos} grupo(s) · {total_busca} CBs com {k} exatas · "
                 f"{total_contem} pares contidos em todos os {n_total_cbs} CBs."
        )


    def _ler_int(self, entry: ttk.Entry, nome_campo: str) -> int:
        texto = entry.get().strip()
        if not texto:
            raise ValueError(f"Preencha o campo '{nome_campo}'.")
        try:
            return int(texto)
        except ValueError:
            raise ValueError(f"O campo '{nome_campo}' deve ser um número inteiro.")

    def _obter_conjuntos_base(self):
        modo = self.modo_base.get()

        if modo == "random":
            n = self._ler_int(self.ent_base_n, "Quantidade de conjuntos (N)")
            x = self._ler_int(self.ent_base_x, "Início do intervalo (x)")
            y = self._ler_int(self.ent_base_y, "Fim do intervalo (y)")
            tamanho = self._ler_int(self.ent_base_tamanho, "Tamanho dos conjuntos")

            if y - x + 1 < tamanho:
                raise ValueError(
                    f"O intervalo [{x}, {y}] tem {y - x + 1} inteiros, "
                    f"mas o tamanho pedido é {tamanho}."
                )
            if n < 1:
                raise ValueError("A quantidade de conjuntos deve ser >= 1.")

            conjuntos = gerar_conjuntos(n, x, y, tamanho)
            return conjuntos, x, y, tamanho

        else:
            caminho = self.ent_base_arquivo.get().strip()
            if not caminho or not os.path.isfile(caminho):
                raise ValueError("Selecione um arquivo .txt válido para os conjuntos base.")
            conjuntos = carregar_conjuntos_txt(caminho)
            if not conjuntos:
                raise ValueError("Nenhum conjunto válido encontrado no arquivo base.")
            return conjuntos, "arquivo", "arquivo", "arquivo"

    def _obter_conjuntos_referencia(self):
        modo = self.modo_ref.get()

        if modo == "random":
            x = self._ler_int(self.ent_ref_x, "Início do intervalo (x)")
            y = self._ler_int(self.ent_ref_y, "Fim do intervalo (y)")
            tamanho = self._ler_int(self.ent_ref_tamanho, "Tamanho dos conjuntos")
            qtd = self._ler_int(self.ent_ref_qtd, "Quantidade de referências")

            if y - x + 1 < tamanho:
                raise ValueError(
                    f"O intervalo [{x}, {y}] tem {y - x + 1} inteiros, "
                    f"mas o tamanho pedido é {tamanho}."
                )
            if qtd < 1:
                raise ValueError("A quantidade de referências deve ser >= 1.")

            refs = []
            for _ in range(qtd):
                elementos = sorted(random.sample(range(x, y + 1), tamanho))
                refs.append(ConjuntoNumerico(elementos))

            return refs, f"[{x}, {y}]", tamanho

        else:
            caminho = self.ent_ref_arquivo.get().strip()
            if not caminho or not os.path.isfile(caminho):
                raise ValueError("Selecione um arquivo .txt válido para os conjuntos de referência.")
            refs_raw = carregar_conjuntos_txt(caminho)
            if not refs_raw:
                raise ValueError("Nenhum conjunto válido encontrado no arquivo de referência.")
            refs = [conj for _, conj in refs_raw]
            return refs, "arquivo", "arquivo"

    # ------------------------------------------------------------------ #
    #  Execução                                                            #
    # ------------------------------------------------------------------ #

    def _executar(self):
        # Valida os campos ANTES de travar a interface / abrir thread
        try:
            if self._conjuntos_filtrados is not None:
                conjuntos = self._conjuntos_filtrados
                x = y = tamanho = "filtrado"
            else:
                conjuntos, x, y, tamanho = self._obter_conjuntos_base()
            refs, xr_log, tamanho_ref_log = self._obter_conjuntos_referencia()
        except ValueError as e:
            messagebox.showerror("Entrada inválida", str(e))
            return

        self.txt_saida.delete("1.0", tk.END)
        self.btn_executar.state(["disabled"])
        self.lbl_status.config(text="Processando...")

        thread = threading.Thread(
            target=self._executar_em_thread,
            args=(conjuntos, x, y, tamanho, refs, xr_log, tamanho_ref_log),
            daemon=True,
        )
        thread.start()

        # A thread NUNCA toca em widgets — apenas a thread principal,
        # que faz o polling da fila de resultado a cada 100 ms.
        self.after(100, self._verificar_resultado)

    def _executar_em_thread(self, conjuntos, x, y, tamanho, refs, xr_log, tamanho_ref_log):
        """
        Executa todo o processamento pesado em segundo plano.
        IMPORTANTE: esta função não deve, em nenhuma hipótese, acessar
        widgets do Tkinter diretamente — apenas o stdout (redirecionado
        para um buffer em memória) e o disco.
        """
        buffer = StringIO()
        stdout_original = sys.stdout
        sys.stdout = buffer
        erro = None
        contem_dados = []

        try:
            exibir_conjuntos(conjuntos, x, y, tamanho)

            if xr_log != "arquivo":
                print(f"\n  {len(refs)} conjunto(s) de referência criado(s) "
                      f"com tamanho {tamanho_ref_log} no intervalo {xr_log}.")
            else:
                print(f"\n  {len(refs)} conjunto(s) de referência carregado(s) de arquivo.")

            contem_dados, _ = verificar_contencao_dados(refs, conjuntos)
            verificar_contencao(refs, conjuntos)

            print("\n\n" + "═" * 52)
            print("   PROGRAMA ENCERRADO")
            print("═" * 52 + "\n")

            caminhos = self._salvar_resultados(buffer, conjuntos, x, y, tamanho,
                                                 refs, xr_log, tamanho_ref_log)

            print(f"  ✔ Execução   salva em: {caminhos['exec']}")
            print(f"  ✔ Conj. base salvo em: {caminhos['base']}")
            print(f"  ✔ Conj. ref  salvo em: {caminhos['ref']}")

        except Exception as e:
            erro = str(e)
            contem_dados = []

        finally:
            sys.stdout = stdout_original
            self._fila_resultado.put((buffer.getvalue(), erro, contem_dados, conjuntos))

    def _verificar_resultado(self):
        """
        Roda na thread principal. Verifica periodicamente se a thread de
        trabalho já colocou um resultado na fila; quando colocar, atualiza
        a interface com segurança.
        """
        try:
            texto, erro, contem_dados, conjuntos_atuais = self._fila_resultado.get_nowait()
        except queue.Empty:
            self.after(100, self._verificar_resultado)
            return

        self._inserir_com_destaque(texto)
        if erro:
            self.txt_saida.insert(tk.END, f"\n  ✗ Erro durante a execução: {erro}\n")
        self.txt_saida.see(tk.END)

        self.btn_executar.state(["!disabled"])
        self.lbl_status.config(text="Erro." if erro else "Concluído.")
        if not erro:
            self._conjuntos_atuais = conjuntos_atuais

        # Habilita nova rodada se houver conjuntos contidos
        if not erro and contem_dados:
            # Extrai conjuntos base únicos que contêm alguma referência
            vistos = set()
            self._contem_para_nova_rodada = []
            for _, _, nome, conj in contem_dados:
                if nome not in vistos:
                    self._contem_para_nova_rodada.append((nome, conj))
                    vistos.add(nome)
            n = len(self._contem_para_nova_rodada)
            self.btn_nova_rodada.state(["!disabled"])
            self.btn_nova_rodada.config(text=f"🔄 Nova rodada com conjuntos contidos ({n})")
        else:
            self.btn_nova_rodada.state(["disabled"])
            self.btn_nova_rodada.config(text="🔄 Nova rodada com conjuntos contidos")

    def _inserir_com_destaque(self, texto: str):
        """
        Insere o texto na área de saída linha a linha.
        Quando encontra um par CR / CB na seção de contenção,
        pinta de laranja os números do CB que coincidem com o CR.
        """
        self.txt_saida.tag_config(
            "coincide",
            foreground="#e67e00",
            font=("Consolas", 10, "bold"),
        )

        cr_atual: set = set()

        for linha in texto.split("\n"):
            # Detecta linha de referência:  "    CR3 = {01, 02, ...}"
            m_cr = re.match(r'(\s+CR\d+\s*=\s*\{)([^}]*)(\})', linha)
            # Detecta linha de base:        "    CB12  = {01, 02, ...}"
            m_cb = re.match(r'(\s+CB\d+\s*=\s*\{)([^}]*)(\})', linha)

            if m_cr:
                # Memoriza os elementos do CR atual para comparar com o CB
                cr_atual = {n.strip() for n in m_cr.group(2).split(",") if n.strip()}
                self.txt_saida.insert(tk.END, linha + "\n")

            elif m_cb and cr_atual:
                # Prefixo antes do '{'
                self.txt_saida.insert(tk.END, m_cb.group(1))

                numeros = [n.strip() for n in m_cb.group(2).split(",") if n.strip()]
                for i, num in enumerate(numeros):
                    tag = "coincide" if num in cr_atual else ""
                    self.txt_saida.insert(tk.END, num, tag)
                    if i < len(numeros) - 1:
                        self.txt_saida.insert(tk.END, ", ")

                self.txt_saida.insert(tk.END, m_cb.group(3) + "\n")

            else:
                # Linha normal — sem destaque, zera o CR memorizado
                if not linha.strip().startswith("CR"):
                    cr_atual = set()
                self.txt_saida.insert(tk.END, linha + "\n")

    # ------------------------------------------------------------------ #
    #  Persistência em arquivos                                           #
    # ------------------------------------------------------------------ #

    def _salvar_resultados(self, buffer, conjuntos, x, y, tamanho,
                            refs, xr_log, tamanho_ref_log):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        pasta_exec = os.path.join(base_dir, "execucoes")
        os.makedirs(pasta_exec, exist_ok=True)
        arq_exec = os.path.join(pasta_exec, f"{timestamp}.txt")
        with open(arq_exec, "w", encoding="utf-8") as f:
            f.write(buffer.getvalue())

        pasta_base = os.path.join(base_dir, "conjuntos base")
        os.makedirs(pasta_base, exist_ok=True)
        arq_base = os.path.join(pasta_base, f"{timestamp}.txt")
        with open(arq_base, "w", encoding="utf-8") as f:
            if tamanho != "arquivo":
                f.write(f"Intervalo: [{x}, {y}]   Tamanho: {tamanho}\n")
            else:
                f.write("Conjuntos carregados de arquivo .txt\n")
            f.write("─" * 52 + "\n")
            f.write(f"{'Nome':<8} Elementos\n")
            f.write("─" * 52 + "\n")
            for nome, conj in conjuntos:
                f.write(f"{nome:<8} {conj}\n")

        pasta_ref = os.path.join(base_dir, "conjuntos referencia")
        os.makedirs(pasta_ref, exist_ok=True)
        arq_ref = os.path.join(pasta_ref, f"{timestamp}.txt")
        with open(arq_ref, "w", encoding="utf-8") as f:
            f.write(f"Intervalo: {xr_log}   Tamanho: {tamanho_ref_log}\n")
            f.write("─" * 52 + "\n")
            f.write(f"{'ID':<8} Elementos\n")
            f.write("─" * 52 + "\n")
            for i, ref in enumerate(refs, start=1):
                f.write(f"CR{i:<6} {ref}\n")

        return {
            "exec": f"execucoes/{timestamp}.txt",
            "base": f"conjuntos base/{timestamp}.txt",
            "ref":  f"conjuntos referencia/{timestamp}.txt",
        }


# ====================================================================== #
#  Entrada do programa                                                    #
# ====================================================================== #

if __name__ == "__main__":
    app = App()
    app.mainloop()
