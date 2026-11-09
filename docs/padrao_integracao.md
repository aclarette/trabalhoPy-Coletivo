# Padrão de integração do grupo

Cada integrante tem uma pasta `integrante_N_nome/` com:

| Arquivo | Papel |
|---|---|
| `etl.py` | Baixa (API do SIDRA) e trata a base do IBGE; grava em `dados/` |
| `estatisticas.py` | Cálculos: média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão, outliers |
| `painel.py` | Tela no Streamlit, com duas funções obrigatórias (abaixo) |
| `analise.md` | Análise descritiva e respostas às perguntas |

## As duas funções que o `app.py` chama
```python
dados = painel.carregar_dados()      # lê as bases tratadas da pasta dados/
painel.render(dados, filtros)        # desenha a página com os filtros da barra lateral
```

## O dicionário `filtros` (montado pelo `app.py`)
| Chave | Valor | Quem usa |
|---|---|---|
| `regiao` | nome da região ou `None` (Brasil) | todos |
| `uf` | sigla da UF ou `None` | todos |
| `racas` | lista de cor ou raça | todos |
| `meios` | lista de meios de transporte | páginas 1 e 2 |
| `rendas` | lista de faixas de renda | página 4 (parte A) |
| `minimo` | mínimo de trabalhadores por município | todos |

## Padrão visual (repositório Graficos)
- `matplotlib` + `seaborn`, paleta `Set2`, cores `#4c72b0` e `#2b5c8f`, título em negrito tamanho 14.
- Linhas de `st.columns(3)`; embaixo de cada gráfico, um `st.write("**Análise:** ...")` calculado dos dados.
- Cada `painel.py` também roda sozinho: `streamlit run integrante_N_nome/painel.py`.

## Upload
O `app.py` reconhece um arquivo enviado pelas colunas e troca a base correspondente antes de chamar o `render`.
A lista de bases e colunas obrigatórias está em `BASES`, no `app.py`.
