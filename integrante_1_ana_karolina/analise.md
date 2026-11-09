# Análise 01 — Meios de transporte por cor ou raça
**Responsável:** Ana Karolina · **Código:** pasta `integrante_1_ana_karolina/` (`etl.py`, `estatisticas.py`, `painel.py`)
**Fonte:** IBGE, Censo 2022, SIDRA 10330 (resultados preliminares da amostra)
**Universo:** 66,1 milhões de pessoas ocupadas de 10 anos ou mais que trabalham fora de casa e voltam ao domicílio 3 ou mais dias por semana, entre as que declararam o meio de transporte.

> Todos os números abaixo são do **Brasil** (dashboard sem filtros). Mudando os filtros, o dashboard recalcula tudo.

## 1. KPIs
| Indicador | Valor |
|---|---|
| Transporte público (ônibus, BRT, trem/metrô) | **23,2%** |
| Transporte particular (carro, moto) | **48,8%** |
| Transporte ativo (a pé, bicicleta) | **24,3%** |
| Outros (mototáxi, táxi, van, barco...) | 3,6% |
| Modal predominante (moda) | **Automóvel** |
| Grupo mais dependente do transporte público | **Preta (32,0%)** |
| Grupo que mais usa transporte particular | **Amarela (63,2%)** |

## 2. Respostas às perguntas
**Participação de cada grupo de transporte por cor ou raça (%)**

| Raça | Público | Particular | Ativo | Outros | Modal predominante |
|---|---|---|---|---|---|
| Branca | 19,5 | 56,6 | 20,5 | 3,4 | Automóvel (42,9%) |
| Preta | **32,0** | 36,1 | 28,0 | 3,9 | **Ônibus (29,4%)** |
| Parda | 24,7 | 44,1 | 27,3 | 3,9 | Automóvel (24,4%) |
| Amarela | 17,3 | **63,2** | 16,7 | 2,8 | Automóvel (56,3%) |
| Indígena | 16,8 | 33,8 | **42,2** | 7,2 | **A pé (33,6%)** |

1. **Qual grupo usa mais transporte público?** Pessoas pretas: 32,0%, contra 19,5% das brancas. A diferença é de 12,5 pontos percentuais.
2. **Qual grupo usa mais carro e moto?** Amarelas (63,2%) e brancas (56,6%).
3. **Há diferenças?** Sim, e grandes. O grupo preto é o **único cujo modal predominante é o ônibus**. O indígena é o único em que **ir a pé** é o principal.
4. **Modal predominante:** está na tabela acima.
5. **Quem são os usuários de cada meio?** Dos usuários de **automóvel**, 59,4% são brancos. Dos usuários de **ônibus**, 46,4% são pardos e 16,1% são pretos. Somados, 62,5% dos passageiros de ônibus são pretos ou pardos.

## 3. Estatística
O meio de transporte é uma variável **categórica**. Para ela, só fazem sentido a **moda** e os **percentuais**: não existe "média de ônibus".
Para calcular média, quartis, desvio padrão e outliers, usamos uma variável **numérica**: o *% de trabalhadores que usam transporte público em cada município*. Entram os 1.796 municípios com pelo menos 5.000 trabalhadores.

| Medida | Valor |
|---|---|
| Média | 12,6% |
| Mediana | 9,0% |
| Q1 / Q3 | 3,4% / 18,3% |
| IQR | 14,9 p.p. |
| Amplitude | 66,9 p.p. (de 0% a 66,9%) |
| Desvio padrão | 11,8 p.p. |
| Limite superior de outlier | 40,8% |
| Outliers | 68 municípios |

**Média × mediana:** a média (12,6%) é maior que a mediana (9,0%). Poucos municípios, em geral grandes cidades com metrô ou com uma rede de ônibus forte, têm valores muito altos e puxam a média para cima. A distribuição é **assimétrica à direita**, então a mediana descreve melhor o município típico. O desvio padrão alto mostra que o acesso ao transporte público é muito desigual pelo território.

## 4. Limitações
- O meio considerado é aquele em que a pessoa **passa mais tempo**. Quem usa bicicleta e depois ônibus aparece só em um deles.
- O Censo não informa o motivo da escolha. A diferença por raça está associada a renda, local de moradia e oferta de transporte, e esses fatores não são separados aqui.
- Os dados são estimativas da amostra do Censo, já expandidas pelo IBGE.

## 5. Recomendações (para os gestores)
- Melhorias na **qualidade e no preço do ônibus** beneficiam mais diretamente a população preta e parda, que é a maioria dos passageiros.
- A **mobilidade ativa** pesa muito para a população indígena: calçadas e trajetos seguros são política de equidade.

## 6. Como explicar em 30 segundos
"Quase metade dos brasileiros vai trabalhar de carro ou moto, mas isso muda muito por raça. Entre pessoas brancas, 56,6% usam transporte particular. Entre pessoas pretas, o meio mais comum é o ônibus, com 32% usando transporte público. Então investir no ônibus é também uma política de redução de desigualdade racial."
