# Relatório do grupo — Transporte e Mobilidade Urbana

**Projeto Integrador "Números que Falam — Descobrindo o Brasil"** · Python e Matemática · Indicador 5
**Startup:** Rota Dados · **Integrantes:** Ana Karolina, Alvaro, Ana Clara Matias e Ingrid
**Fonte:** IBGE, Censo Demográfico 2022, SIDRA 10330, 10331, 10332 e 10295 (66,1 milhões de trabalhadores que se deslocam)

## 1. O pedido dos clientes
Fernando (Secretaria Nacional de Mobilidade Urbana), Ana (Goiânia), Luciene (Vitória), Pedrinho (Belo Horizonte) e
Lucas (Brasília) pediram uma avaliação dos modais de transporte mais utilizados por raça. Entregamos um painel no
Streamlit com upload de dados, filtros, KPIs, gráficos, estatística e notícias.

## 2. Respostas às perguntas
**P1. Mediana do tempo por meio de transporte e raça (Alvaro).** Metade dos trabalhadores leva até 21,2 minutos.
O transporte coletivo tem as viagens mais longas: BRT 63,9 min, trem ou metrô 63,5 min e ônibus 45,4 min, contra
19,0 min do automóvel. Em todos os meios principais, pessoas pretas levam mais tempo que brancas; no trem ou metrô
a diferença é de 14,2 minutos (71,7 × 57,5). Levam mais de 1 hora 15,1% das pessoas pretas e 9,2% das brancas.

**P2. Público × particular × ativo (Ana Karolina).** 48,8% usam transporte particular, 23,2% público e 24,3% ativo.
O modal predominante é o automóvel. Por raça: 32,0% das pessoas pretas usam transporte público, contra 19,5% das
brancas; o grupo preto é o único em que o ônibus é o meio mais comum. Dos passageiros de ônibus, 62,5% são pretos
ou pardos; dos usuários de automóvel, 59,4% são brancos.

**P3. Cidades com mais bicicleta (Ana Clara).** 6,3% dos trabalhadores vão de bicicleta. No ranking percentual
(municípios com pelo menos 10 mil trabalhadores) lideram Ubatuba (SP) 39,4%, Pompéu (MG) 39,0% e Taiobeiras (MG)
34,5%. O Rio de Janeiro tem o maior número absoluto (58.478), mas só 2,9% dos seus trabalhadores pedalam.

**Renda (Ingrid).** As viagens de mais de 1 hora caem de 13,5% (faixa de 1/4 a 1/2 salário mínimo) para 8,8% (mais
de 5 salários). O Censo não cruza meio de transporte com renda; pelo nível de instrução, 68,1% de quem tem superior
completo usa carro ou moto, contra 37,0% de quem não tem instrução.

## 3. Estatística (cada município é uma observação)
| Indicador | Municípios | Média | Mediana | Q1 | Q3 | IQR | Desvio padrão | Outliers |
|---|---|---|---|---|---|---|---|---|
| % transporte público | 1.796 | 12,6 | 9,0 | 3,4 | 18,3 | 15,0 | 11,8 | 68 |
| Mediana do tempo (min) | 1.804 | 17,0 | 15,1 | 13,1 | 19,1 | 6,0 | 6,1 | 92 |
| % bicicleta | 983 | 8,3 | 6,1 | 3,1 | 11,8 | 8,8 | 6,9 | 26 |
| Renda mediana per capita (R$) | 1.795 | 986 | 1.025 | 634 | 1.212 | 578 | 347 | 3 |

Outliers pela regra de 1,5 × IQR. Nos três primeiros indicadores a média é maior que a mediana: poucos municípios
com valores muito altos (metrópoles com metrô, cidades-dormitório, "cidades da bicicleta") puxam a média para cima,
então a mediana descreve melhor o município típico. Na renda acontece o contrário (média menor que a mediana), e a
moda é exatamente o salário mínimo de 2022 (R$ 1.212). Os maiores gargalos de tempo são cidades-dormitório:
em Francisco Morato (SP), 48,0% levam mais de 1 hora.

## 4. Recomendações
- **Fernando:** investir em velocidade, qualidade e preço do transporte coletivo reduz a desigualdade racial.
- **Ana e Lucas:** priorizar a ligação entre o entorno do Distrito Federal e os centros de emprego.
- **Luciene:** Vitória (6,2% de bicicleta) é plana e litorânea como as líderes do ranking: ciclovias e bicicletários.
- **Pedrinho:** Belo Horizonte tem o maior tempo mediano entre as quatro cidades (30,2 min) e só 0,7% de bicicleta.
- **Todos:** tarifa social e integração tarifária para as faixas de renda com mais viagens longas.

## 5. Limitações
O tempo vem em faixas (medianas estimadas); o Censo considera só o meio em que a pessoa passa mais tempo e só o
deslocamento para o trabalho; relações entre municípios não valem automaticamente para pessoas (falácia ecológica).
