# Análise 04 — Renda e desigualdade na mobilidade
**Responsável:** Ingrid · **Código:** pasta `integrante_4_ingrid/` (`etl.py`, `estatisticas.py`, `painel.py`)
**Fontes:** IBGE, Censo 2022: SIDRA 10331 (tempo × raça × renda), 10295 (renda per capita por município) e 10332 (meio × instrução × raça)

## 1. Limitação central (falar isso logo no início da apresentação)
O Censo 2022 **não publica uma tabela de meio de transporte × renda das pessoas**. Conferimos o catálogo inteiro do SIDRA. Por isso o módulo tem **três partes**, cada uma com seu tipo de conclusão:

| Parte | Dado | Conclusão permitida |
|---|---|---|
| A) Tempo × renda | 10331 (pessoas) | Sobre **pessoas** |
| B) Renda do município × modal | 10295 + 10330 | Sobre **municípios** (cuidado com a falácia ecológica) |
| C) Instrução × modal | 10332 (pessoas) | Sobre pessoas, mas por **instrução** (um proxy, não a renda) |

**Falácia ecológica:** "municípios mais ricos usam mais carro" **não** prova que "pessoas mais ricas usam mais carro". Uma cidade rica pode ter muitos moradores pobres que andam de ônibus.

## 2. Parte A: tempo × renda (Brasil)
| Renda domiciliar per capita | Pessoas | Mediana estimada | % acima de 1 h | % acima de 2 h |
|---|---|---|---|---|
| Sem rendimento | 19 mil | 22,9 min | 14,1% | 3,0% |
| Até 1/4 SM | 2,3 mi | 22,7 min | 11,8% | 1,9% |
| 1/4 a 1/2 SM | 8,5 mi | **23,3 min** | **13,5%** | 2,2% |
| 1/2 a 1 SM | 20,8 mi | 22,8 min | 13,4% | 2,0% |
| 1 a 2 SM | 22,6 mi | 21,3 min | 12,4% | 1,7% |
| 2 a 3 SM | 7,5 mi | 19,7 min | 11,0% | 1,5% |
| 3 a 5 SM | 5,1 mi | 19,1 min | 10,0% | 1,4% |
| Mais de 5 SM | 3,8 mi | 19,3 min | **8,8%** | 1,3% |

**Leitura:** a partir de 1/4 SM, quanto **maior a renda, menor a proporção de viagens acima de 1 hora**: o valor cai de 13,5% para 8,8%. A diferença entre a faixa "até 1/4 SM" e a faixa "mais de 5 SM" é de **2,9 p.p.** Atenção: a faixa mais pobre (até 1/4 SM) tem menos viagens longas que a seguinte, provavelmente porque inclui mais trabalhadores rurais e de cidades pequenas, com trajetos curtos. A relação não é perfeitamente linear. A faixa "sem rendimento" tem só 19 mil pessoas, então deve ser lida com cautela.

## 3. Parte B: renda do município × modal (1.796 municípios com pelo menos 5 mil trabalhadores)
| Correlação de Pearson (r) | Valor | Leitura |
|---|---|---|
| Renda mediana × % transporte particular | **r = 0,34** | fraca e positiva |
| Renda mediana × % transporte público | **r = 0,18** | muito fraca e positiva |

Os dois resultados são positivos. Isso parece contraditório, mas ilustra a falácia ecológica: municípios mais ricos tendem a ser **cidades maiores**, que têm mais carros **e também mais ônibus** que cidades pequenas, onde se vai a pé ou de moto. A renda do município não separa "quem usa ônibus" de "quem usa carro". O tamanho e a oferta de transporte da cidade também pesam.

## 4. Parte C: instrução × modal (proxy socioeconômico, Brasil)
| Nível de instrução | Público | Particular | Ativo |
|---|---|---|---|
| Sem instrução / fund. incompleto | 21,5% | 37,0% | **36,5%** |
| Fund. completo / médio incompleto | 25,5% | 40,2% | 30,0% |
| Médio completo / sup. incompleto | **27,3%** | 46,8% | 22,1% |
| Superior completo | 16,0% | **68,1%** | 12,7% |

**Leitura:** com superior completo, **68,1%** usam carro ou moto, contra 37,0% de quem não tem instrução. O transporte público atinge seu maior uso no **ensino médio** (27,3%). Os menos escolarizados **andam mais a pé** (36,5%).

## 5. Respostas às perguntas
1. **Menor renda usa mais transporte público?** Não temos o dado direto. Pelo proxy de instrução, os grupos intermediários são os que mais usam ônibus, e os de menor instrução vão mais a pé.
2. **Maior renda usa mais carro?** Pelo proxy, sim: 68,1% entre quem tem superior completo. Entre municípios, a correlação é só fraca (r = 0,34).
3. **Diferença de tempo por renda?** Sim. A mediana cai de cerca de 23 min nas faixas mais baixas para cerca de 19 min nas mais altas, e as viagens acima de 1 h caem de 13,5% para 8,8%.
4. **Maior dependência do transporte público:** a faixa de instrução média (27,3%). No Brasil todo, o grupo racial mais dependente é o preto (ver a análise da Ana Karolina).
5. **Há desigualdade?** Sim: no tempo de viagem e no acesso ao carro.

## 6. Estatística: renda domiciliar per capita mediana dos municípios (R$)
| Medida | Valor |
|---|---|
| Média | R$ 986 |
| Mediana | R$ 1.025 |
| Moda | **R$ 1.212** (o salário mínimo de 2022) |
| Q1 / Q3 | R$ 634 / R$ 1.212 |
| IQR | R$ 578 |
| Amplitude | R$ 2.200 (R$ 300 a R$ 2.500) |
| Desvio padrão | R$ 346 |
| Limite superior de outlier | R$ 2.080 |
| Outliers | 3 municípios |

**Média × mediana:** aqui a média é **menor** que a mediana. Há muitos municípios com renda muito baixa (cauda à esquerda), que puxam a média para baixo. A **moda** e o **Q3** são exatamente o **salário mínimo** (R$ 1.212): muitos domicílios vivem de rendas iguais a 1 SM (aposentadorias, BPC, salários mínimos), então a mediana de muitos municípios "empilha" nesse valor. **Lição:** nem toda variável de renda é assimétrica à direita. Sempre olhar os números antes de afirmar.

## 7. Recomendações
- **Tarifa social e integração tarifária** para as faixas de 1/4 a 1 SM, que concentram as viagens longas.
- Ligar **periferias aos centros de emprego**, porque o tempo maior das faixas baixas tem relação com a distância de moradia.

## 8. Como explicar em 30 segundos
"Quem ganha menos passa mais tempo no trânsito: 13,5% da faixa de 1/4 a 1/2 salário mínimo leva mais de uma hora, contra 8,8% de quem ganha mais de 5 salários. O Censo não cruza meio de transporte com renda. Por isso usamos a escolaridade: com superior completo, 68% vão de carro ou moto. E mostramos por que não dá para tirar conclusões sobre pessoas a partir da média dos municípios."
