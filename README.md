# Verificador de Conjuntos Numéricos

Verifica se conjuntos de referência estão contidos em conjuntos base.

## Arquivos do projeto

| Arquivo | Descrição |
|---|---|
| `conjunto_numerico.py` | Classe com toda a lógica matemática |
| `main.py` | Lógica de geração, carregamento e verificação |
| `app.py` | Interface desktop (Tkinter) |
| `streamlit_app.py` | Interface web (Streamlit) |
| `requirements.txt` | Dependências para deploy |
| `exemplo_conjuntos_base.txt` | Exemplo de arquivo de entrada |

---

## Rodar como app desktop (Tkinter)

```bash
python app.py
```

Não precisa instalar nada além do Python padrão.

---

## Rodar como app web (Streamlit)

### Localmente

```bash
pip install streamlit
streamlit run streamlit_app.py
```

### Deploy gratuito no Streamlit Cloud

1. Crie uma conta em https://streamlit.io/cloud  
2. Suba todos os arquivos do projeto num repositório GitHub  
3. No Streamlit Cloud clique em **"New app"**  
4. Aponte para o repositório e selecione `streamlit_app.py` como arquivo principal  
5. Clique em **Deploy** — a URL pública é gerada automaticamente

> O `requirements.txt` já está configurado, o Streamlit Cloud instala tudo sozinho.

---

## Formato do arquivo .txt de entrada

```
# Linhas começando com # são comentários
# Formato com nome explícito:
CB1: 1, 3, 5, 7, 9
# Formato sem nome (recebe CB1, CB2... automaticamente):
1, 3, 5, 7, 9
```
