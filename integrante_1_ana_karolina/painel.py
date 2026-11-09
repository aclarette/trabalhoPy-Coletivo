"""
PAINEL — ANA KAROLINA — MEIOS DE TRANSPORTE POR RAÇA
====================================================

Responde à PERGUNTA 2 da persona: % de transporte público × particular × ativo, por cor ou raça.
O meio de transporte é CATEGÓRICO (só moda e percentuais). Para média, quartis, desvio padrão
e outliers usamos uma variável NUMÉRICA: o % que usa transporte público em cada município.

Rodar SOZINHO (a partir da pasta do projeto):
    streamlit run integrante_1_ana_karolina/painel.py

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

from integrante_1_ana_karolina import estatisticas as E
from integrante_1_ana_karolina.etl import GRUPOS_MODAIS, MEIOS, PASTA_DADOS, RACAS, REGIOES

FONTE = "Fonte: IBGE, Censo Demográfico 2022, SIDRA 10330."
PRINCIPAIS = ["Automóvel", "Motocicleta", "Ônibus", "BRT", "Trem ou metrô", "Bicicleta", "A pé"]
CORES_GRUPO = dict(zip(GRUPOS_MODAIS, sns.color_palette("Set2", len(GRUPOS_MODAIS))))
CORES_RACA = dict(zip(RACAS, sns.color_palette("Set2", len(RACAS))))
CORES_REGIAO = dict(zip(REGIOES, sns.color_palette("Set2", len(REGIOES))))


# ---------------- DADOS ----------------
@st.cache_data
def carregar_dados() -> dict:
    return {
        "uf": pd.read_csv(PASTA_DADOS / "transporte_raca_uf.csv", dtype={"cod_ibge": str}),
        "municipio": pd.read_csv(PASTA_DADOS / "transporte_raca_municipio.csv.gz", dtype={"cod_ibge": str}),
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


# ---------------- FORMATAÇÃO (número no padrão brasileiro) ----------------
def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor, 1)}%"


def presentes(ordem, valores):
    return [x for x in ordem if x in set(valores)]


# ---------------- PAINEL ----------------
def render(dados: dict, filtros: dict) -> None:
    st.title("Meios de transporte por cor ou raça")
    st.write("**Pergunta:** qual o % de transporte público, particular e ativo em cada grupo racial? · " + FONTE)

    df = selecionar(dados, filtros)
    df = df[df.groupby("raca")["pessoas"].transform("sum") > 0]  # tira grupos sem ninguém (evita divisão por zero)
    if df["pessoas"].sum() == 0:
        st.error("Nenhuma pessoa com esses filtros. Amplie a seleção.")
        return

    if set(filtros.get("meios") or MEIOS) != set(MEIOS):
        st.write("**Filtro de meio de transporte ativo:** os percentuais das linhas 1 e 2 são calculados só entre "
                 "os meios selecionados. A estatística por município (linhas 3 e 4) sempre usa todos os meios.")

    por_raca = E.participacao(df, "grupo_modal", por=["raca"])
    publico = por_raca[por_raca["grupo_modal"] == "Público"].set_index("raca")["percentual"]
    particular = por_raca[por_raca["grupo_modal"] == "Particular"].set_index("raca")["percentual"]

    # ================= LINHA 1 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=por_raca,
            x="raca",
            y="percentual",
            hue="grupo_modal",
            order=presentes(RACAS, por_raca["raca"]),
            hue_order=GRUPOS_MODAIS,
            palette=CORES_GRUPO,
            errorbar=None,
            ax=ax
        )
        ax.set_title("Grupo de Transporte por Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("% do grupo racial", fontsize=11)
        ax.legend(title="Transporte", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = "**Análise:** "
        if len(publico):
            texto += (f"Pessoas {publico.idxmax().lower()}s são o grupo que mais usa transporte público "
                      f"({pct(publico.max())}). ")
        if len(particular):
            texto += (f"Pessoas {particular.idxmax().lower()}s são o grupo que mais usa carro e moto "
                      f"({pct(particular.max())}).")
        if "Preta" in publico and "Branca" in publico:
            texto += (f" Entre pessoas pretas, {pct(publico['Preta'])} usam transporte público, contra "
                      f"{pct(publico['Branca'])} das brancas ({num(publico['Preta'] - publico['Branca'], 1)} p.p.).")
        st.write(texto)

    with col2:
        pizza = df.groupby("grupo_modal")["pessoas"].sum().reindex(GRUPOS_MODAIS).dropna()
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            pizza,
            labels=pizza.index,
            autopct="%1.1f%%",
            startangle=140,
            colors=[CORES_GRUPO[g] for g in pizza.index],
            wedgeprops={"edgecolor": "white", "linewidth": 1.5}
        )
        ax.set_title("Distribuição dos Trabalhadores por Grupo de Transporte", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        parte = 100 * pizza / pizza.sum()
        st.write(f"**Análise:** {pct(parte.get('Particular', 0))} vão de carro ou moto, "
                 f"{pct(parte.get('Público', 0))} de transporte público (ônibus, BRT, trem e metrô) e "
                 f"{pct(parte.get('Ativo', 0))} a pé ou de bicicleta. Outros meios (mototáxi, van, barco...) "
                 f"somam {pct(parte.get('Outros', 0))}.")

    with col3:
        meios = E.participacao(df.assign(todos="x"), "meio", por=["todos"]).sort_values("percentual", ascending=False)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=meios,
            x="percentual",
            y="meio",
            color="#4c72b0",
            errorbar=None,
            ax=ax
        )
        ax.set_title("Frequência dos Meios de Transporte", fontsize=14, fontweight="bold")
        ax.set_xlabel("% dos trabalhadores", fontsize=11)
        ax.set_ylabel("Meio de transporte", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = f"**Análise:** O meio mais usado (a moda) é {meios.iloc[0]['meio']} ({pct(meios.iloc[0]['percentual'])})"
        if len(meios) > 1:
            texto += ", seguido de " + " e ".join(f"{x['meio']} ({pct(x['percentual'])})"
                                                  for _, x in meios.iloc[1:3].iterrows())
        st.write(texto + ".")

    # ================= LINHA 2 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        meio_raca = E.participacao(df, "meio", por=["raca"])
        matriz = meio_raca.pivot(index="meio", columns="raca", values="percentual")
        mostrados = presentes(PRINCIPAIS, matriz.index) or presentes(MEIOS, matriz.index)
        matriz = matriz.reindex(index=mostrados, columns=presentes(RACAS, matriz.columns))
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(
            matriz,
            annot=True,
            fmt=".1f",
            cmap="YlGnBu",
            linewidths=0.5,
            cbar_kws={"label": "% do grupo racial"},
            ax=ax
        )
        ax.set_title("% de Cada Meio de Transporte por Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("Meio de transporte", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        moda = meio_raca.loc[meio_raca.groupby("raca")["percentual"].idxmax()].set_index("raca")
        frases = [f"{r.lower()}: {moda.loc[r, 'meio']} ({pct(moda.loc[r, 'percentual'])})"
                  for r in presentes(RACAS, moda.index)]
        st.write("**Análise:** Modal predominante de cada grupo: " + "; ".join(frases) + ".")

    with col2:
        comp = E.participacao(df[df["meio"].isin(mostrados)], "raca", por=["meio"])
        tb = comp.pivot(index="meio", columns="raca", values="percentual")
        tb = tb.reindex(index=mostrados[::-1], columns=presentes(RACAS, tb.columns))
        fig, ax = plt.subplots(figsize=(10, 6))
        tb.plot(
            kind="barh",
            stacked=True,
            color=[CORES_RACA[r] for r in tb.columns],
            edgecolor="white",
            ax=ax
        )
        ax.set_title("Quem São os Usuários de Cada Meio (Composição Racial)", fontsize=14, fontweight="bold")
        ax.set_xlabel("% dos usuários do meio", fontsize=11)
        ax.set_ylabel("Meio de transporte", fontsize=11)
        ax.set_xlim(0, 100)
        ax.legend(title="Cor ou raça", frameon=True, loc="upper left", bbox_to_anchor=(1.01, 1))
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = "**Análise:** "
        if "Automóvel" in tb.index and "Branca" in tb.columns:
            texto += f"Dos usuários de automóvel, {pct(tb.loc['Automóvel', 'Branca'])} são brancos. "
        if "Ônibus" in tb.index and {"Preta", "Parda"} <= set(tb.columns):
            texto += (f"Dos passageiros de ônibus, {pct(tb.loc['Ônibus', 'Preta'] + tb.loc['Ônibus', 'Parda'])} "
                      "são pretos ou pardos.")
        st.write(texto)

    mun = municipios(dados, filtros)

    with col3:
        reg = E.participacao(mun[mun["raca"].isin(["Branca", "Preta", "Parda"])], "grupo_modal", por=["regiao", "raca"])
        reg = reg[reg["grupo_modal"] == "Público"]
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=reg,
            x="regiao",
            y="percentual",
            hue="raca",
            order=presentes(REGIOES, reg["regiao"]),
            hue_order=presentes(RACAS, reg["raca"]),
            palette=CORES_RACA,
            errorbar=None,
            ax=ax
        )
        ax.set_title("Transporte Público por Região e Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Região", fontsize=11)
        ax.set_ylabel("% que usa transporte público", fontsize=11)
        ax.legend(title="Cor ou raça", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        if len(reg):
            maior = reg.loc[reg["percentual"].idxmax()]
            st.write(f"**Análise:** O maior uso de transporte público é entre pessoas {maior['raca'].lower()}s do "
                     f"{maior['regiao']} ({pct(maior['percentual'])}). O gráfico mostra só branca, preta e parda, "
                     "que têm amostra grande em todas as regiões.")

    # ================= LINHA 3 (estatística: % público em cada município) =================
    minimo = filtros.get("minimo", 5_000)
    v = E.percentual_por_municipio(mun, "grupo_modal", ["Público"], minimo)
    v["municipio"] = v["local"] + " (" + v["uf"] + ")"
    if len(v) < 5:
        st.warning("Poucos municípios com esse mínimo de trabalhadores. Reduza o mínimo ou amplie o território.")
        return
    r = E.resumo_descritivo(v["percentual"])

    col1, col2, col3 = st.columns(3)

    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(
            data=v,
            x="percentual",
            kde=True,
            bins=20,
            color="#4c72b0",
            ax=ax,
        )
        ax.axvline(r["media"], color="red", linestyle="--", linewidth=2, label=f"Média ({pct(r['media'])})")
        ax.axvline(r["mediana"], color="#2b5c8f", linestyle="-", linewidth=2, label=f"Mediana ({pct(r['mediana'])})")
        ax.set_title("Distribuição do % de Transporte Público nos Municípios", fontsize=14, fontweight="bold")
        ax.set_xlabel("% dos trabalhadores que usam transporte público", fontsize=11)
        ax.set_ylabel("Nº de municípios", fontsize=11)
        ax.legend(frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = (f"**Análise:** Nos {num(r['n'])} municípios com pelo menos {num(minimo)} trabalhadores, a média é "
                 f"{pct(r['media'])} e a mediana {pct(r['mediana'])}. ")
        if r["media"] > r["mediana"]:
            texto += ("Poucos municípios com valores muito altos (cidades grandes, com metrô ou boa rede de ônibus) "
                      "puxam a média para cima (assimetria à direita); a mediana descreve melhor o município típico.")
        st.write(texto)

    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            data=v,
            x="regiao",
            y="percentual",
            hue="regiao",
            order=presentes(REGIOES, v["regiao"]),
            palette=CORES_REGIAO,
            legend=False,
            ax=ax
        )
        ax.axhline(r["limite_superior"], color="red", linestyle="--", linewidth=1.5,
                   label=f"Limite de outlier ({pct(r['limite_superior'])})")
        ax.set_title("% de Transporte Público nos Municípios por Região", fontsize=14, fontweight="bold")
        ax.set_xlabel("Região", fontsize=11)
        ax.set_ylabel("% que usa transporte público", fontsize=11)
        ax.legend(frameon=True)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        med = v.groupby("regiao")["percentual"].median()
        st.write(f"**Análise:** Metade dos municípios fica entre {pct(r['q1'])} (Q1) e {pct(r['q3'])} (Q3), "
                 f"IQR de {num(r['iqr'], 1)} p.p. Acima de {pct(r['limite_superior'])} há {r['qtd_outliers']} "
                 f"outliers. A maior mediana é a do {med.idxmax()} ({pct(med.max())}).")

    with col3:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(
            data=v,
            x="total",
            y="percentual",
            logx=True,
            color="#2b5c8f",
            scatter_kws={"s": 20, "alpha": 0.4},
            line_kws={"color": "red", "linewidth": 2},
            ax=ax
        )
        ax.set_xscale("log")
        ax.set_title("Relação entre Tamanho do Município e Transporte Público", fontsize=14, fontweight="bold")
        ax.set_xlabel("Nº de trabalhadores (escala log)", fontsize=11)
        ax.set_ylabel("% que usa transporte público", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        inclinacao = np.polyfit(np.log10(v["total"]), v["percentual"], 1)[0]
        corr = np.corrcoef(np.log10(v["total"]), v["percentual"])[0, 1]
        forca = "fraca" if abs(corr) < 0.3 else "moderada" if abs(corr) < 0.7 else "forte"
        st.write(f"**Análise:** A correlação é de {num(corr, 2)} ({forca}). Cada vez que o número de trabalhadores "
                 f"é multiplicado por 10, o % de transporte público muda em média {num(inclinacao, 1)} p.p.: "
                 + ("cidades maiores usam mais transporte público." if inclinacao > 0
                    else "cidades maiores usam menos transporte público."))

    # ================= LINHA 4 (tabelas) =================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Medidas estatísticas (% de transporte público)**")
        medidas = [("Nº de municípios", num(r["n"])), ("Média", pct(r["media"])), ("Mediana", pct(r["mediana"])),
                   ("Moda (1 casa)", pct(r["moda"])), ("Q1", pct(r["q1"])), ("Q3", pct(r["q3"])),
                   ("IQR", f"{num(r['iqr'], 1)} p.p."), ("Mínimo", pct(r["minimo"])), ("Máximo", pct(r["maximo"])),
                   ("Amplitude", f"{num(r['amplitude'], 1)} p.p."), ("Variância", num(r["variancia"], 1)),
                   ("Desvio padrão", f"{num(r['desvio_padrao'], 1)} p.p."),
                   ("Limite superior de outlier", pct(r["limite_superior"])), ("Outliers", num(r["qtd_outliers"]))]
        st.dataframe(pd.DataFrame(medidas, columns=["Medida", "Valor"]), hide_index=True, width="stretch")
        st.write(f"**Análise:** O desvio padrão de {num(r['desvio_padrao'], 1)} p.p. mostra que o acesso ao "
                 "transporte público é muito desigual entre os municípios.")

    with col2:
        st.write("**Grupo de transporte por cor ou raça (%)**")
        tabela = por_raca.pivot(index="raca", columns="grupo_modal", values="percentual") \
            .reindex(index=presentes(RACAS, por_raca["raca"]), columns=GRUPOS_MODAIS).round(1)
        tabela["Modal predominante"] = [moda.loc[x, "meio"] for x in tabela.index]
        st.dataframe(tabela.reset_index().rename(columns={"raca": "Cor ou raça"}), hide_index=True, width="stretch")
        st.write("**Análise:** O meio de transporte é uma variável categórica: para ela só fazem sentido a moda "
                 "e os percentuais, por isso a estatística ao lado usa o % de cada município.")

    with col3:
        st.write("**Outliers: municípios com muito transporte público**")
        fora = E.marcar_outliers(v, "percentual")
        fora = fora[fora["outlier"] == "Acima"].sort_values("percentual", ascending=False)
        st.dataframe(fora[["municipio", "percentual", "total"]].round(1)
                     .rename(columns={"municipio": "Município", "percentual": "% público", "total": "Trabalhadores"}),
                     hide_index=True, width="stretch")
        if len(fora):
            st.write(f"**Análise:** São {len(fora)} municípios acima de {pct(r['limite_superior'])}. O maior é "
                     f"{fora.iloc[0]['municipio']}, com {pct(fora.iloc[0]['percentual'])}.")


# ---------------- SIDEBAR (dados do aluno + filtros) ----------------
def barra_lateral(dados: dict) -> dict:
    st.sidebar.header("Informações do Aluno")
    st.sidebar.write("**Nome:** Ana Karolina")
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
                               help="Municípios muito pequenos têm percentuais instáveis.")
    return {"regiao": regiao, "uf": uf, "racas": racas, "meios": meios, "minimo": minimo}


if __name__ == "__main__":
    st.set_page_config(
        page_title="Transporte por raça",
        layout="wide",
        initial_sidebar_state="expanded",  # sidebar começa aberto e pode ser recolhido
    )
    dados_ak = carregar_dados()
    render(dados_ak, barra_lateral(dados_ak))
