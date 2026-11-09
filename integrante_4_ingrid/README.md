# Ingrid — Renda e desigualdade na mobilidade

**Projeto:** Números que Falam — Descobrindo o Brasil · Persona 5 (Transporte e Mobilidade Urbana)
**Pergunta da persona que esta parte responde:** complementa P1 e P2 — relação entre renda, tempo e modal
**Fonte:** IBGE, Censo Demográfico 2022 — SIDRA 10331, 10295, 10330 e 10332

## Arquivos
| Arquivo | O que é |
|---|---|
| `etl.py` | Coleta (API do SIDRA/IBGE) + tratamento + gravação da base tratada |
| `estatisticas.py` | Cálculos estatísticos (média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão, outliers) |
| `painel.py` | Tela no Streamlit no padrão do repositório Graficos: matplotlib + seaborn, 3 linhas de 3 gráficos com **Análise** embaixo de cada um, e uma linha de tabelas |
| `dados/` | Base IBGE tratada: `tempo_renda_raca_uf.csv`, `renda_municipio.csv`, `meio_municipio.csv.gz`, `instrucao_meio_raca_uf.csv` |
| `analise.md` | Análise descritiva com os resultados e as respostas às perguntas |

## Bibliotecas
`pandas`, `numpy`, `matplotlib`, `seaborn`, `streamlit` (e `requests` + `truststore` para a ETL)

## Como rodar (a partir da pasta do projeto, com o ambiente virtual ativo)
1. Baixar e tratar os dados (só precisa uma vez; os dados já estão em `dados/`):
   ```
   python -m integrante_4_ingrid.etl
   ```
2. Abrir o painel:
   ```
   streamlit run integrante_4_ingrid/painel.py
   ```

## Integração com o dashboard do grupo
O `painel.py` segue o padrão do grupo (`docs/padrao_integracao.md`): o `app.py` final chama
`carregar_dados()` e `render(dados, filtros)`.
