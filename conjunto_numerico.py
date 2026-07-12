import math
from typing import Union


class ConjuntoNumerico:
    """
    Representa um conjunto numérico com atributos e operações matemáticas.
    Suporta operações de conjuntos, combinatória e estatística.
    """

    def __init__(self, elementos: list):
        """
        Inicializa o conjunto com uma lista de números.
        Duplicatas são removidas automaticamente (propriedade de conjunto).
        """
        if not all(isinstance(e, (int, float)) for e in elementos):
            raise TypeError("Todos os elementos devem ser numéricos.")

        self.elementos = sorted(set(elementos))
        self._atualizar_atributos()

    # ------------------------------------------------------------------ #
    #  Atualização interna dos atributos derivados                         #
    # ------------------------------------------------------------------ #

    def _atualizar_atributos(self):
        """Recalcula os atributos sempre que o conjunto é modificado."""
        self.tamanho    = len(self.elementos)
        self.minimo     = min(self.elementos) if self.elementos else None
        self.maximo     = max(self.elementos) if self.elementos else None
        self.range      = (self.maximo - self.minimo) if self.elementos else None
        self.soma       = sum(self.elementos)
        self.quantidade = self.tamanho          # alias semântico

    # ------------------------------------------------------------------ #
    #  Representação                                                       #
    # ------------------------------------------------------------------ #

    def __repr__(self):
        return f"ConjuntoNumerico({self.elementos})"

    def __str__(self):
        if not self.elementos:
            return "{}"
        largura = len(str(max(abs(int(e)) for e in self.elementos)))
        return "{" + ", ".join(str(int(e)).zfill(largura) for e in self.elementos) + "}"

    # ------------------------------------------------------------------ #
    #  Combinatória                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def fatorial(n: int) -> int:
        """Retorna n! (n fatorial). n deve ser inteiro não-negativo."""
        if not isinstance(n, int) or n < 0:
            raise ValueError("O fatorial só é definido para inteiros não-negativos.")
        return math.factorial(n)

    @staticmethod
    def permutacao(n: int, r: int) -> int:
        """
        Permutação P(n, r) = n! / (n - r)!
        Quantidade de arranjos de r elementos escolhidos de n.
        """
        if r > n:
            raise ValueError("r não pode ser maior que n.")
        return math.factorial(n) // math.factorial(n - r)

    @staticmethod
    def combinacao(n: int, r: int) -> int:
        """
        Combinação C(n, r) = n! / (r! * (n - r)!)
        Quantidade de subconjuntos de tamanho r escolhidos de n.
        """
        if r > n:
            raise ValueError("r não pode ser maior que n.")
        return math.comb(n, r)

    def permutacao_do_conjunto(self, r: int) -> int:
        """P(tamanho, r) usando o tamanho do próprio conjunto."""
        return self.permutacao(self.tamanho, r)

    def combinacao_do_conjunto(self, r: int) -> int:
        """C(tamanho, r) usando o tamanho do próprio conjunto."""
        return self.combinacao(self.tamanho, r)

    def pertence(self, x: Union[int, float]) -> bool:
        """Verifica se x ∈ conjunto."""
        return x in self.elementos

    def nao_pertence(self, x: Union[int, float]) -> bool:
        """Verifica se x ∉ conjunto."""
        return x not in self.elementos

    def uniao(self, outro: "ConjuntoNumerico") -> "ConjuntoNumerico":
        """Retorna A ∪ B (união dos dois conjuntos)."""
        return ConjuntoNumerico(list(set(self.elementos) | set(outro.elementos)))

    def intersecao(self, outro: "ConjuntoNumerico") -> "ConjuntoNumerico":
        """Retorna A ∩ B (interseção dos dois conjuntos)."""
        return ConjuntoNumerico(list(set(self.elementos) & set(outro.elementos)))

    def subconjunto(self, outro: "ConjuntoNumerico") -> bool:
        """Verifica se este conjunto é subconjunto de 'outro' (A ⊆ B)."""
        return set(self.elementos).issubset(set(outro.elementos))

    def superconjunto(self, outro: "ConjuntoNumerico") -> bool:
        """Verifica se este conjunto é superconjunto de 'outro' (A ⊇ B)."""
        return set(self.elementos).issuperset(set(outro.elementos))

    # ------------------------------------------------------------------ #
    #  Manipulação do conjunto                                             #
    # ------------------------------------------------------------------ #

    def adicionar(self, x: Union[int, float]):
        """Adiciona um elemento ao conjunto (se já não existir)."""
        if x not in self.elementos:
            self.elementos = sorted(self.elementos + [x])
            self._atualizar_atributos()

    def remover(self, x: Union[int, float]):
        """Remove um elemento do conjunto."""
        if x not in self.elementos:
            raise ValueError(f"{x} não pertence ao conjunto.")
        self.elementos.remove(x)
        self._atualizar_atributos()

    def esta_vazio(self) -> bool:
        """Retorna True se o conjunto é vazio (∅)."""
        return self.tamanho == 0

    def resumo(self) -> str:
        """Exibe um resumo estatístico do conjunto."""
        if not self.elementos:
            return "Conjunto vazio."
        linhas = [
            f"Conjunto  : {self}",
            f"Tamanho   : {self.tamanho}",
            f"Mínimo    : {self.minimo}",
            f"Máximo    : {self.maximo}",
            f"Range     : {self.range}",
            f"Soma      : {self.soma}",
            f"Média     : {self.media():.4f}",
            f"Mediana   : {self.mediana()}",
            f"Desv. Pad.: {self.desvio_padrao():.4f}",
        ]
        return "\n".join(linhas)
