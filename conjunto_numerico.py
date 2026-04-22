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
        return f"{{{', '.join(map(str, self.elementos))}}}"

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

    # ------------------------------------------------------------------ #
    #  Operações de pertinência e conjuntos                                #
    # ------------------------------------------------------------------ #

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

    def diferenca(self, outro: "ConjuntoNumerico") -> "ConjuntoNumerico":
        """Retorna A - B (diferença: elementos em A mas não em B)."""
        return ConjuntoNumerico(list(set(self.elementos) - set(outro.elementos)))

    def diferenca_simetrica(self, outro: "ConjuntoNumerico") -> "ConjuntoNumerico":
        """Retorna A △ B (elementos em A ou B, mas não em ambos)."""
        return ConjuntoNumerico(list(set(self.elementos) ^ set(outro.elementos)))

    def subconjunto(self, outro: "ConjuntoNumerico") -> bool:
        """Verifica se este conjunto é subconjunto de 'outro' (A ⊆ B)."""
        return set(self.elementos).issubset(set(outro.elementos))

    def superconjunto(self, outro: "ConjuntoNumerico") -> bool:
        """Verifica se este conjunto é superconjunto de 'outro' (A ⊇ B)."""
        return set(self.elementos).issuperset(set(outro.elementos))

    def disjunto(self, outro: "ConjuntoNumerico") -> bool:
        """Verifica se os conjuntos são disjuntos (A ∩ B = ∅)."""
        return self.intersecao(outro).tamanho == 0

    def complemento(self, universal: "ConjuntoNumerico") -> "ConjuntoNumerico":
        """Retorna o complemento de A em relação ao conjunto universal U."""
        return universal.diferenca(self)

    # ------------------------------------------------------------------ #
    #  Estatística                                                         #
    # ------------------------------------------------------------------ #

    def media(self) -> float:
        """Retorna a média aritmética dos elementos."""
        if not self.elementos:
            raise ValueError("Conjunto vazio não possui média.")
        return self.soma / self.tamanho

    def mediana(self) -> float:
        """Retorna a mediana dos elementos."""
        if not self.elementos:
            raise ValueError("Conjunto vazio não possui mediana.")
        meio = self.tamanho // 2
        if self.tamanho % 2 == 0:
            return (self.elementos[meio - 1] + self.elementos[meio]) / 2
        return float(self.elementos[meio])

    def variancia(self, populacional: bool = True) -> float:
        """
        Retorna a variância dos elementos.
        populacional=True  → divide por N   (variância populacional)
        populacional=False → divide por N-1 (variância amostral)
        """
        if self.tamanho < 2:
            raise ValueError("Necessário ao menos 2 elementos.")
        mu = self.media()
        divisor = self.tamanho if populacional else self.tamanho - 1
        return sum((x - mu) ** 2 for x in self.elementos) / divisor

    def desvio_padrao(self, populacional: bool = True) -> float:
        """Retorna o desvio padrão (raiz quadrada da variância)."""
        return math.sqrt(self.variancia(populacional))

    def moda(self) -> list:
        """Retorna o(s) valor(es) mais frequente(s). Em conjuntos todos aparecem 1×."""
        from collections import Counter
        contagem = Counter(self.elementos)
        freq_max = max(contagem.values())
        return [k for k, v in contagem.items() if v == freq_max]

    # ------------------------------------------------------------------ #
    #  Teoria dos números                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def mdc(a: int, b: int) -> int:
        """Máximo Divisor Comum entre a e b."""
        return math.gcd(a, b)

    @staticmethod
    def mmc(a: int, b: int) -> int:
        """Mínimo Múltiplo Comum entre a e b."""
        return math.lcm(a, b)

    def eh_primo(self, n: int) -> bool:
        """Verifica se n é primo."""
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    def primos_do_conjunto(self) -> "ConjuntoNumerico":
        """Retorna um novo conjunto apenas com os primos do conjunto atual."""
        primos = [e for e in self.elementos if isinstance(e, int) and self.eh_primo(e)]
        return ConjuntoNumerico(primos) if primos else ConjuntoNumerico([0])

