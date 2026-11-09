# Ana Clara — Mobilidade ativa e uso de bicicletas

**Projeto:** Números que Falam — Descobrindo o Brasil · Persona 5 (Transporte e Mobilidade Urbana)
**Pergunta da persona que esta parte responde:** P3 — quais cidades têm mais mobilidade ativa (bicicleta)
**Fonte:** IBGE, Censo Demográfico 2022 — SIDRA 10330 (municípios) e malha das UFs

## Arquivos
| Arquivo | O que é |
|---|---|
| `etl.py` | Coleta (API do SIDRA/IBGE) + tratamento + gravação da base tratada |
| `estatisticas.py` | Cálculos estatísticos (média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão, outliers) |
| `painel.py` | Tela no Streamlit no padrão do repositório Graficos: matplotlib + seaborn, 3 linhas de 3 gráficos com **Análise** embaixo de cada um, e uma linha de tabelas (estatística, capitais das personas, outliers) |
| `dados/` | Base IBGE tratada: `transporte_municipio.csv.gz` (o `mapa_uf.geojson` é baixado pela ETL, mas o painel não usa mais o mapa) |
| `analise.md` | Análise descritiva com os resultados e as respostas às perguntas |

## Bibliotecas
`pandas`, `numpy`, `matplotlib`, `seaborn`, `streamlit` (e `requests` + `truststore` para a ETL)

## Como rodar (a partir da pasta do projeto, com o ambiente virtual ativo)
1. Baixar e tratar os dados (só precisa uma vez; os dados já estão em `dados/`):
   ```
   python -m integrante_3_ana_clara.etl
   ```
2. Abrir o painel:
   ```
   streamlit run integrante_3_ana_clara/painel.py
   ```

## Integração com o dashboard do grupo
O `painel.py` segue o padrão do grupo (`docs/padrao_integracao.md`): o `app.py` final chama
`carregar_dados()` e `render(dados, filtros)`.
