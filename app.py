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

        self._construir_ui()

    # ------------------------------------------------------------------ #
    #  Construção da interface                                            #
    # ------------------------------------------------------------------ #

    def _construir_ui(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

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

        # ── Área de saída ────────────────────────────────────────────────
        ttk.Label(container, text="Resultado:").pack(anchor="w")
        self.txt_saida = scrolledtext.ScrolledText(
            container, wrap="word", font=("Consolas", 16), height=24
        )
        self.txt_saida.pack(fill="both", expand=True, pady=(4, 0))

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

    # ------------------------------------------------------------------ #
    #  Leitura e validação dos campos                                     #
    # ------------------------------------------------------------------ #

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
            conjuntos, x, y, tamanho = self._obter_conjuntos_base()
            refs, xr_log, tamanho_ref_log = self._obter_conjuntos_referencia()
        except ValueError as e:
            messagebox.showerror("Entrada inválida", str(e))
            return

        self.txt_saida.delete("1.0", tk.END)
        self.btn_executar.config(state="disabled")
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

        try:
            exibir_conjuntos(conjuntos, x, y, tamanho)

            if xr_log != "arquivo":
                print(f"\n  {len(refs)} conjunto(s) de referência criado(s) "
                      f"com tamanho {tamanho_ref_log} no intervalo {xr_log}.")
            else:
                print(f"\n  {len(refs)} conjunto(s) de referência carregado(s) de arquivo.")

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

        finally:
            sys.stdout = stdout_original
            # Apenas entrega o resultado pronto pela fila — nenhuma
            # interação direta com a interface acontece aqui.
            self._fila_resultado.put((buffer.getvalue(), erro))

    def _verificar_resultado(self):
        """
        Roda na thread principal. Verifica periodicamente se a thread de
        trabalho já colocou um resultado na fila; quando colocar, atualiza
        a interface com segurança.
        """
        try:
            texto, erro = self._fila_resultado.get_nowait()
        except queue.Empty:
            self.after(100, self._verificar_resultado)
            return

        self.txt_saida.insert(tk.END, texto)
        if erro:
            self.txt_saida.insert(tk.END, f"\n  ✗ Erro durante a execução: {erro}\n")
        self.txt_saida.see(tk.END)

        self.btn_executar.config(state="normal")
        self.lbl_status.config(text="Erro." if erro else "Concluído.")

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
