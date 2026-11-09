# Análise 03 — Mobilidade ativa e uso de bicicletas
**Responsável:** Ana Clara · **Código:** pasta `integrante_3_ana_clara/` (`etl.py`, `estatisticas.py`, `painel.py`)
**Fonte:** IBGE, Censo 2022, SIDRA 10330, nível **município** (5.570 municípios)

## 1. O que exatamente medimos
**% de trabalhadores cujo meio PRINCIPAL é a bicicleta.**
- **Numerador:** trabalhadores do município que vão principalmente de bicicleta.
- **Denominador:** todos os trabalhadores do município que se deslocam (entre quem declarou o meio).

Não confundir três medidas diferentes:
1. **Nº de ciclistas** (absoluto): favorece cidades grandes.
2. **% de trabalhadores ciclistas**: é a medida deste módulo e a do **ranking principal**.
3. **% de viagens por bicicleta**: o Censo **não** mede viagens.

**Corte mínimo:** o ranking usa municípios com **pelo menos 10.000 trabalhadores** (983 municípios). Em municípios minúsculos, poucas pessoas mudam muito o percentual, e o erro amostral é maior. O corte é ajustável no dashboard.

## 2. KPIs (Brasil)
| Indicador | Valor |
|---|---|
| % bicicleta no Brasil | **6,3%** (4,18 milhões de trabalhadores) |
| % a pé no Brasil | **18,0%** |
| Mobilidade ativa total | **24,3%** |
| Município com maior % de bicicleta | **Ubatuba (SP), 39,4%** |
| Município com mais ciclistas (absoluto) | **Rio de Janeiro (RJ), 58.478** (só 2,9% dos seus trabalhadores) |
| Destaque em mobilidade ativa total | **Toritama (PE), 65,5%** (61,1% a pé) |

Conferido no dado bruto: Ubatuba tem 14.861 ciclistas em um total oficial de 38.327 trabalhadores.

## 3. Ranking principal: % de bicicleta (pelo menos 10 mil trabalhadores)
| # | Município | % bicicleta | Ciclistas |
|---|---|---|---|
| 1 | Ubatuba (SP) | 39,4% | 14.862 |
| 2 | Pompéu (MG) | 39,0% | 4.660 |
| 3 | Taiobeiras (MG) | 34,5% | 3.782 |
| 4 | Matinhos (PR) | 34,2% | 4.886 |
| 5 | Pirapora (MG) | 33,4% | 7.202 |
| 6 | Peruíbe (SP) | 32,8% | 6.250 |
| 7 | Várzea da Palma (MG) | 31,8% | 3.389 |
| 8 | Capanema (PA) | 31,2% | 6.347 |
| 9 | Januária (MG) | 30,8% | 5.092 |
| 10 | Janaúba (MG) | 30,7% | 7.931 |

**Ranking absoluto** (outra história): Rio de Janeiro (58.478; 2,9%), Fortaleza (57.160; 7,3%), Belém (48.971; 12,1%), São Paulo (41.561; 1,0%) e Recife (35.338; 7,1%).
→ Os rankings são diferentes porque **cidades grandes têm muitos ciclistas só por terem muita gente**. É por isso que o ranking principal é o percentual.

Padrões: cidades **litorâneas planas** (Ubatuba, Matinhos, Peruíbe) e cidades médias do **norte de Minas** (Pompéu, Pirapora, Janaúba, Januária, Taiobeiras).

## 4. Regiões
| Região | % bicicleta | % a pé |
|---|---|---|
| Norte | **10,3** | 16,7 |
| Centro-Oeste | 7,6 | 11,5 |
| Nordeste | 7,0 | **24,0** |
| Sul | 5,6 | 17,3 |
| Sudeste | 5,4 | 16,8 |

## 5. Capitais das personas (ranking entre os 983 municípios)
| Cidade (gestor) | % bicicleta | % a pé | % ativo | Posição no ranking de bicicleta |
|---|---|---|---|---|
| Vitória (Luciene) | 6,2% | 14,5% | 20,7% | 484º |
| Goiânia (Ana) | 4,5% | 11,6% | 16,0% | 606º |
| Brasília (Lucas) | 2,5% | 8,5% | 11,0% | 784º |
| Belo Horizonte (Pedrinho) | **0,7%** | 14,3% | 15,0% | **956º** |

## 6. Estatística (983 municípios com pelo menos 10 mil trabalhadores)
| Medida | Valor |
|---|---|
| Média | 8,3% |
| Mediana | 6,1% |
| Moda (1 casa decimal) | 2,3% |
| Q1 / Q3 | 3,1% / 11,8% |
| IQR | 8,8 p.p. |
| Amplitude | 39,2 p.p. (0,2% a 39,4%) |
| Desvio padrão | 6,9 p.p. |
| Limite superior de outlier | 25,0% |
| Outliers | **26 municípios**: as "cidades da bicicleta" |

**Média × mediana:** a média (8,3%) é maior que a mediana (6,1%), e a moda (2,3%) é ainda menor. A maioria dos municípios usa pouco a bicicleta, e alguns poucos usam muito: é uma **assimetria à direita**. Os 26 outliers puxam a média para cima, então a mediana descreve melhor o município típico.

## 7. Limitações
- Só conta o meio em que a pessoa passa **mais tempo**: quem pedala até o ônibus não aparece como ciclista.
- O dado mede apenas o deslocamento para o **trabalho**. Lazer, estudo e compras ficam de fora.
- Infraestrutura (km de ciclovia) não está nesta base: falta essa informação para explicar as causas.

## 8. Recomendações
- **Luciene (Vitória):** a cidade já está acima de BH, Goiânia e Brasília. As referências são Ubatuba e Matinhos, cidades planas e litorâneas como Vitória. Ciclovias conectadas, bicicletários em terminais e integração com o ônibus.
- **Pedrinho (BH):** só 0,7% vão de bicicleta, o que deixa a cidade entre as últimas do ranking. O relevo pesa, mas 14,3% já vão a pé. Há espaço para bicicleta elétrica e compartilhada em trajetos curtos.
- **Onde o % a pé é alto** (Nordeste, 24%), os trajetos são curtos: há potencial para atrair ciclistas com segurança viária.

## 9. Como explicar em 30 segundos
"No Brasil, 6,3% dos trabalhadores vão de bicicleta. O Rio de Janeiro tem o maior número de ciclistas, mas isso é efeito do tamanho: lá, só 2,9% pedalam. No ranking percentual, o destaque é Ubatuba, com quase 40%. Belo Horizonte aparece entre as últimas, com 0,7%."
