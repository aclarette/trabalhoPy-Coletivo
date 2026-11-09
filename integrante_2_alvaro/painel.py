"""
PAINEL — ALVARO — TEMPO DE DESLOCAMENTO ATÉ O TRABALHO
======================================================

Responde à PERGUNTA 1 da persona: mediana do tempo de deslocamento por meio de transporte × raça.
O IBGE dá o tempo em FAIXAS, então a mediana é ESTIMADA (estatística para dados agrupados):
    Mediana ≈ Li + ((n/2 − Fant) / fi) × h
Para média, quartis, desvio padrão e outliers usamos a mediana estimada de CADA município.

Rodar SOZINHO (a partir da pasta do projeto):
    streamlit run integrante_2_alvaro/painel.py

No dashboard do grupo, o app.py chama:  carregar_dados()  e  render(dados, filtros)
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from integrante_2_alvaro import estatisticas as E
from integrante_2_alvaro.etl import GRUPO_MODAL, MEIOS, PASTA_DADOS, RACAS, REGIOES, TEMPO_FAIXAS

FONTE = "Fonte: IBGE, Censo Demográfico 2022, SIDRA 10330."
MIN_PESSOAS = 1_000  # combinações com menos pessoas que isso ficam de fora (estimativa instável)
GRUPOS = ["Público", "Particular", "Ativo", "Outros"]
CORES_GRUPO = dict(zip(GRUPOS, sns.color_palette("Set2", len(GRUPOS))))
CORES_RACA = dict(zip(RACAS, sns.color_palette("Set2", len(RACAS))))
CORES_REGIAO = dict(zip(REGIOES, sns.color_palette("Set2", len(REGIOES))))


# ---------------- DADOS ----------------
@st.cache_data
def carregar_dados() -> dict:
    return {
        "uf": pd.read_csv(PASTA_DADOS / "tempo_meio_raca_uf.csv", dtype={"cod_ibge": str}),
        "municipio": pd.read_csv(PASTA_DADOS / "tempo_raca_municipio.csv.gz", dtype={"cod_ibge": str}),
    }


def selecionar(dados: dict, filtros: dict) -> pd.DataFrame:
    """Linhas do território (Brasil, região ou UF) com os filtros de raça e de meio de transporte."""
    base = dados["uf"]
    if filtros.get("uf"):
        df = base[(base["nivel"] == "UF") & (base["uf"] == filtros["uf"])]
    elif filtros.get("regiao"):
        df = base[(base["nivel"] == "Região") & (base["regiao"] == filtros["regiao"])]
    else:
        df = base[base["nivel"] == "Brasil"]
    return df[df["raca"].isin(filtros.get("racas") or RACAS) & df["meio"].isin(filtros.get("meios") or MEIOS)]


def municipios(dados: dict, filtros: dict) -> pd.DataFrame:
    df = dados["municipio"]
    if filtros.get("regiao"):
        df = df[df["regiao"] == filtros["regiao"]]
    if filtros.get("uf"):
        df = df[df["uf"] == filtros["uf"]]
    return df[df["raca"].isin(filtros.get("racas") or RACAS)]


@st.cache_data(show_spinner="Calculando a mediana de cada município...")
def medianas_municipais(df: pd.DataFrame) -> pd.DataFrame:
    return E.por_municipio(df)


# ---------------- FORMATAÇÃO (número no padrão brasileiro) ----------------
def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor, 1)}%"


def minutos(valor):
    return f"{num(valor, 1)} min"


def presentes(ordem, valores):
    return [x for x in ordem if x in set(valores)]


# ---------------- PAINEL ----------------
def render(dados: dict, filtros: dict) -> None:
    st.title("Tempo de deslocamento até o trabalho")
    st.write("**Pergunta:** qual é a mediana do tempo de deslocamento por meio de transporte e cor ou raça? · " + FONTE)

    df = selecionar(dados, filtros)
    if df["pessoas"].sum() == 0:
        st.error("Nenhuma pessoa com esses filtros. Amplie a seleção.")
        return

    if set(filtros.get("meios") or MEIOS) != set(MEIOS):
        st.write("**Filtro de meio de transporte ativo:** as linhas 1 e 2 consideram só quem usa os meios "
                 "selecionados. A base por município (linhas 3 e 4) não tem o meio de transporte.")

    geral = E.resumo_agrupado(df)
    por_raca = E.resumo_por_categoria(df, "raca", RACAS)
    por_meio = E.resumo_por_categoria(df, "meio", MEIOS)
    por_meio = por_meio[por_meio["n"] >= MIN_PESSOAS]

    # ================= LINHA 1 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        linhas = []
        for (meio, raca), grupo in df.groupby(["meio", "raca"]):
            f = E.frequencias(grupo)
            linhas.append({"meio": meio, "raca": raca,
                           "mediana": E.quantil_agrupado(f, 0.5) if f.sum() >= MIN_PESSOAS else np.nan})
        matriz = pd.DataFrame(linhas).pivot(index="meio", columns="raca", values="mediana")
        principais = ["A pé", "Bicicleta", "Motocicleta", "Automóvel", "Ônibus", "BRT", "Trem ou metrô"]
        matriz = matriz.reindex(index=presentes(principais, matriz.index) or presentes(MEIOS, matriz.index),
                                columns=presentes(RACAS, matriz.columns))
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(
            matriz,
            annot=True,
            fmt=".1f",
            cmap="YlGnBu",
            linewidths=0.5,
            cbar_kws={"label": "Mediana estimada (min)"},
            ax=ax
        )
        ax.set_title("Mediana do Tempo (min) por Meio e Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("Meio de transporte", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = f"**Análise:** Células vazias têm menos de {num(MIN_PESSOAS)} pessoas (estimativa instável). "
        if {"Preta", "Branca"} <= set(matriz.columns):
            dif = (matriz["Preta"] - matriz["Branca"]).dropna()
            if len(dif):
                texto += (f"Pessoas pretas levam mais tempo que brancas em {(dif > 0).sum()} de {len(dif)} meios; "
                          f"a maior diferença é no {dif.idxmax()} ({num(dif.max(), 1)} min a mais).")
        st.write(texto)

    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=por_raca,
            x="raca",
            y="mediana",
            hue="raca",
            palette=CORES_RACA,
            legend=False,
            errorbar=None,
            ax=ax
        )
        ax.set_title("Mediana Estimada do Tempo por Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("Mediana estimada (min)", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        maior, menor = por_raca.loc[por_raca["mediana"].idxmax()], por_raca.loc[por_raca["mediana"].idxmin()]
        st.write(f"**Análise:** Metade dos trabalhadores leva até {minutos(geral['mediana'])} para chegar ao "
                 f"trabalho. Pessoas {maior['raca'].lower()}s têm a maior mediana ({minutos(maior['mediana'])}) e "
                 f"pessoas {menor['raca'].lower()}s a menor ({minutos(menor['mediana'])}).")

    with col3:
        tb = por_raca.melt(id_vars="raca", value_vars=["pct_mais_1h", "pct_mais_2h"], var_name="limite",
                           value_name="percentual")
        tb["limite"] = tb["limite"].map({"pct_mais_1h": "Mais de 1 h", "pct_mais_2h": "Mais de 2 h"})
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=tb,
            x="raca",
            y="percentual",
            hue="limite",
            palette="Set2",
            errorbar=None,
            ax=ax
        )
        ax.set_title("Deslocamentos Demorados por Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("% do grupo racial", fontsize=11)
        ax.legend(title="Tempo", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        p1 = por_raca.set_index("raca")["pct_mais_1h"]
        st.write(f"**Análise:** {pct(geral['pct_mais_1h'])} dos trabalhadores levam mais de 1 hora e "
                 f"{pct(geral['pct_mais_2h'])} mais de 2 horas. Entre os grupos, o % acima de 1 h vai de "
                 f"{pct(p1.min())} ({p1.idxmin().lower()}) a {pct(p1.max())} ({p1.idxmax().lower()}): "
                 f"{num(p1.max() - p1.min(), 1)} p.p. de diferença.")

    # ================= LINHA 2 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        dist = E.participacao(df, "tempo_faixa", por=["raca"])
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=dist,
            x="tempo_faixa",
            y="percentual",
            hue="raca",
            order=TEMPO_FAIXAS,
            hue_order=presentes(RACAS, dist["raca"]),
            palette=CORES_RACA,
            errorbar=None,
            ax=ax
        )
        ax.set_title("Distribuição por Faixa de Tempo e Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Tempo até o trabalho", fontsize=11)
        ax.set_ylabel("% do grupo racial", fontsize=11)
        ax.legend(title="Cor ou raça", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        acima30 = dist[dist["tempo_faixa"].isin(["30 min a 1 h"] + E.FAIXAS_MAIS_1H)].groupby("raca")["percentual"].sum()
        st.write(f"**Análise:** A faixa mais comum (classe modal) é {geral['classe_modal']}, e a mediana cai na "
                 f"faixa {geral['classe_mediana']}. Levam mais de 30 minutos {pct(acima30.max())} das pessoas "
                 f"{acima30.idxmax().lower()}s, contra {pct(acima30.min())} das {acima30.idxmin().lower()}s.")

    with col2:
        faixas = E.frequencias(df)
        pizza = faixas.drop(["2 a 4 h", "Mais de 4 h"])
        pizza["Mais de 2 h"] = faixas[["2 a 4 h", "Mais de 4 h"]].sum()
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            pizza,
            labels=pizza.index,
            autopct=lambda p: f"{p:.1f}%" if p >= 2 else "",  # fatias muito pequenas ficam sem número
            startangle=140,
            colors=sns.color_palette("Set2", len(pizza)),
            wedgeprops={"edgecolor": "white", "linewidth": 1.5}
        )
        ax.set_title("Distribuição dos Trabalhadores por Faixa de Tempo", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        parte = 100 * pizza / pizza.sum()
        st.write(f"**Análise:** {pct(parte[['Até 5 min', '6 a 15 min', '15 a 30 min']].sum())} chegam ao trabalho "
                 f"em até 30 minutos. {pct(parte['30 min a 1 h'])} levam de 30 min a 1 h e "
                 f"{pct(parte[['1 a 2 h', 'Mais de 2 h']].sum())} mais de 1 hora.")

    with col3:
        tb = por_meio.assign(grupo=por_meio["meio"].map(GRUPO_MODAL)).sort_values("mediana", ascending=False)
        if tb.empty:
            st.write(f"Nenhum meio selecionado tem pelo menos {num(MIN_PESSOAS)} pessoas neste território.")
            return
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=tb,
            x="mediana",
            y="meio",
            hue="grupo",
            hue_order=presentes(GRUPOS, tb["grupo"]),
            palette=CORES_GRUPO,
            dodge=False,
            errorbar=None,
            ax=ax
        )
        ax.set_title("Mediana Estimada do Tempo por Meio de Transporte", fontsize=14, fontweight="bold")
        ax.set_xlabel("Mediana estimada (min)", fontsize=11)
        ax.set_ylabel("Meio de transporte", fontsize=11)
        ax.legend(title="Transporte", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = "**Análise:** Os meios com as viagens mais longas são "
        texto += ", ".join(f"{x['meio']} ({minutos(x['mediana'])}; {pct(x['pct_mais_1h'])} acima de 1 h)"
                           for _, x in tb.head(3).iterrows())
        st.write(texto + ". Transporte coletivo concentra as viagens mais demoradas.")

    # ================= LINHA 3 (estatística: mediana estimada de cada município) =================
    minimo = filtros.get("minimo", 5_000)
    v = medianas_municipais(municipios(dados, filtros))
    v = v[v["total"] >= minimo].dropna(subset=["mediana"]).copy()
    v["municipio"] = v["local"] + " (" + v["uf"] + ")"
    if len(v) < 5:
        st.warning("Poucos municípios com esse mínimo de trabalhadores. Reduza o mínimo ou amplie o território.")
        return
    r = E.resumo_descritivo(v["mediana"])

    col1, col2, col3 = st.columns(3)

    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(
            data=v,
            x="mediana",
            kde=True,
            bins=20,
            color="#4c72b0",
            ax=ax,
        )
        ax.axvline(r["media"], color="red", linestyle="--", linewidth=2, label=f"Média ({minutos(r['media'])})")
        ax.axvline(r["mediana"], color="#2b5c8f", linestyle="-", linewidth=2,
                   label=f"Mediana ({minutos(r['mediana'])})")
        ax.set_title("Distribuição da Mediana do Tempo nos Municípios", fontsize=14, fontweight="bold")
        ax.set_xlabel("Mediana estimada do município (min)", fontsize=11)
        ax.set_ylabel("Nº de municípios", fontsize=11)
        ax.legend(frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = (f"**Análise:** Nos {num(r['n'])} municípios com pelo menos {num(minimo)} trabalhadores, a média "
                 f"é {minutos(r['media'])} e a mediana {minutos(r['mediana'])}. ")
        if r["media"] > r["mediana"]:
            texto += ("Os municípios-dormitório das metrópoles têm tempos muito altos e puxam a média para cima "
                      "(assimetria à direita); a mediana descreve melhor o município típico.")
        st.write(texto)

    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            data=v,
            x="regiao",
            y="mediana",
            hue="regiao",
            order=presentes(REGIOES, v["regiao"]),
            palette=CORES_REGIAO,
            legend=False,
            ax=ax
        )
        ax.axhline(r["limite_superior"], color="red", linestyle="--", linewidth=1.5,
                   label=f"Limite de outlier ({minutos(r['limite_superior'])})")
        ax.set_title("Mediana do Tempo nos Municípios por Região", fontsize=14, fontweight="bold")
        ax.set_xlabel("Região", fontsize=11)
        ax.set_ylabel("Mediana estimada (min)", fontsize=11)
        ax.legend(frameon=True)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        med = v.groupby("regiao")["mediana"].median()
        st.write(f"**Análise:** Metade dos municípios fica entre {minutos(r['q1'])} (Q1) e {minutos(r['q3'])} "
                 f"(Q3), IQR de {minutos(r['iqr'])}. Acima de {minutos(r['limite_superior'])} há "
                 f"{r['qtd_outliers']} outliers. A maior mediana regional é a do {med.idxmax()} "
                 f"({minutos(med.max())}).")

    with col3:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(
            data=v,
            x="total",
            y="mediana",
            logx=True,
            color="#2b5c8f",
            scatter_kws={"s": 20, "alpha": 0.4},
            line_kws={"color": "red", "linewidth": 2},
            ax=ax
        )
        ax.set_xscale("log")
        ax.set_title("Relação entre Tamanho do Município e Tempo", fontsize=14, fontweight="bold")
        ax.set_xlabel("Nº de trabalhadores (escala log)", fontsize=11)
        ax.set_ylabel("Mediana estimada (min)", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        inclinacao = np.polyfit(np.log10(v["total"]), v["mediana"], 1)[0]
        corr = np.corrcoef(np.log10(v["total"]), v["mediana"])[0, 1]
        forca = "fraca" if abs(corr) < 0.3 else "moderada" if abs(corr) < 0.7 else "forte"
        st.write(f"**Análise:** A correlação é de {num(corr, 2)} ({forca}). Cada vez que o número de trabalhadores "
                 f"é multiplicado por 10, a mediana muda em média {num(inclinacao, 1)} min: "
                 + ("em cidades maiores a viagem tende a ser mais longa." if inclinacao > 0
                    else "em cidades maiores a viagem tende a ser mais curta."))

    # ================= LINHA 4 (tabelas) =================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Medidas para dados agrupados (todas as pessoas)**")
        medidas = [("Mediana estimada (Q2)", minutos(geral["mediana"])), ("Q1 estimado", minutos(geral["q1"])),
                   ("Q3 estimado", minutos(geral["q3"])), ("IQR estimado", minutos(geral["iqr"])),
                   ("Classe mediana", geral["classe_mediana"]), ("Classe modal (moda)", geral["classe_modal"]),
                   ("Média estimada*", minutos(geral["media_estimada"])),
                   ("Mais de 1 hora", pct(geral["pct_mais_1h"])), ("Mais de 2 horas", pct(geral["pct_mais_2h"]))]
        st.dataframe(pd.DataFrame(medidas, columns=["Medida", "Valor"]), hide_index=True, width="stretch")
        st.write(f"**Análise:** Mediana ≈ Li + ((n/2 − Fant) / fi) × h. *A faixa \"Mais de 4 h\" não tem fim: "
                 f"usamos {E.PONTO_MEDIO_ABERTA} min, então a média é aproximada e a mediana é a medida principal.")

    with col2:
        st.write("**Medidas estatísticas (mediana de cada município)**")
        medidas = [("Nº de municípios", num(r["n"])), ("Média", minutos(r["media"])),
                   ("Mediana", minutos(r["mediana"])), ("Moda (1 casa)", minutos(r["moda"])),
                   ("Q1", minutos(r["q1"])), ("Q3", minutos(r["q3"])), ("IQR", minutos(r["iqr"])),
                   ("Mínimo", minutos(r["minimo"])), ("Máximo", minutos(r["maximo"])),
                   ("Amplitude", minutos(r["amplitude"])), ("Variância", f"{num(r['variancia'], 1)} min²"),
                   ("Desvio padrão", minutos(r["desvio_padrao"])),
                   ("Limite superior de outlier", minutos(r["limite_superior"])), ("Outliers", num(r["qtd_outliers"]))]
        st.dataframe(pd.DataFrame(medidas, columns=["Medida", "Valor"]), hide_index=True, width="stretch")
        st.write("**Análise:** Não existe o tempo de cada pessoa, então não fazemos boxplot de pessoas: cada "
                 "município vira uma observação (a sua mediana estimada).")

    with col3:
        st.write("**Gargalos: municípios com mais viagens acima de 1 h**")
        gargalos = v.sort_values("pct_mais_1h", ascending=False).head(15)
        st.dataframe(gargalos[["municipio", "pct_mais_1h", "mediana"]].round(1)
                     .rename(columns={"municipio": "Município", "pct_mais_1h": "% > 1 h", "mediana": "Mediana (min)"}),
                     hide_index=True, width="stretch")
        g1, g2 = gargalos.iloc[0], gargalos.iloc[1]
        st.write(f"**Análise:** {g1['municipio']} lidera, com {pct(g1['pct_mais_1h'])} dos trabalhadores levando "
                 f"mais de 1 hora, seguido de {g2['municipio']} ({pct(g2['pct_mais_1h'])}). São, em geral, "
                 "cidades-dormitório das regiões metropolitanas.")


# ---------------- SIDEBAR (dados do aluno + filtros) ----------------
def barra_lateral(dados: dict) -> dict:
    st.sidebar.header("Informações do Aluno")
    st.sidebar.write("**Nome:** Alvaro")
    st.sidebar.write("**Nº da chamada:** —")
    st.sidebar.write("**Turma:** —")

    st.sidebar.header("Filtros")
    regiao = st.sidebar.selectbox("Região", ["Brasil (todas)"] + REGIOES)
    regiao = None if regiao.startswith("Brasil") else regiao
    mun = dados["municipio"]
    ufs = mun[mun["regiao"] == regiao]["uf"] if regiao else mun["uf"]
    uf = st.sidebar.selectbox("UF", ["Todas"] + sorted(ufs.unique()))
    uf = None if uf == "Todas" else uf
    racas = st.sidebar.multiselect("Cor ou raça", RACAS, default=RACAS)
    meios = st.sidebar.multiselect("Meio de transporte", MEIOS, default=MEIOS)
    minimo = st.sidebar.slider("Mínimo de trabalhadores por município", 0, 50_000, 5_000, 1_000,
                               help="Municípios muito pequenos têm estimativas instáveis.")
    return {"regiao": regiao, "uf": uf, "racas": racas, "meios": meios, "minimo": minimo}


if __name__ == "__main__":
    st.set_page_config(
        page_title="Tempo de deslocamento",
        layout="wide",
        initial_sidebar_state="expanded",  # sidebar começa aberto e pode ser recolhido
    )
    dados_alv = carregar_dados()
    render(dados_alv, barra_lateral(dados_alv))
