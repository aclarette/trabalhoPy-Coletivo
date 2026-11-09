"""
PAINEL — ANA CLARA — MOBILIDADE ATIVA E USO DE BICICLETAS
=========================================================

Responde à PERGUNTA 3 da persona: quais cidades têm mais mobilidade ativa (bicicleta)?
Medida principal: % de trabalhadores cujo meio PRINCIPAL é a bicicleta.

Rodar SOZINHO (a partir da pasta do projeto):
    streamlit run integrante_3_ana_clara/painel.py

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

from integrante_3_ana_clara import estatisticas as E
from integrante_3_ana_clara.etl import MUNICIPIOS_PERSONAS, PASTA_DADOS, RACAS, REGIOES

FONTE = "Fonte: IBGE, Censo Demográfico 2022, SIDRA 10330."
CORES_REGIAO = dict(zip(REGIOES, sns.color_palette("Set2", len(REGIOES))))


# ---------------- DADOS ----------------
@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(PASTA_DADOS / "transporte_municipio.csv.gz", dtype={"cod_ibge": str})


def filtrar(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
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


def nome(linha):
    return f"{linha['local']} ({linha['uf']})"


# ---------------- PAINEL ----------------
def render(dados: pd.DataFrame, filtros: dict) -> None:
    st.title("Mobilidade ativa e uso de bicicletas")
    st.write("**Pergunta:** quais cidades têm mais mobilidade ativa (bicicleta)? · " + FONTE)

    df = filtrar(dados, filtros)
    t = E.tabela_municipal(df)
    if t["total"].sum() == 0:
        st.error("Nenhuma pessoa com esses filtros. Amplie a seleção.")
        return

    minimo = filtros.get("minimo", 10_000)
    v = t[t["total"] >= minimo].copy()  # municípios que entram no ranking e na estatística
    v["municipio"] = v["local"] + " (" + v["uf"] + ")"
    t["municipio"] = t["local"] + " (" + t["uf"] + ")"
    if len(v) < 5:
        st.warning("Poucos municípios com esse mínimo de trabalhadores. Reduza o mínimo ou amplie o território.")
        return

    # ================= LINHA 1 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        top = v.nlargest(10, "pct_bicicleta")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=top,
            x="pct_bicicleta",
            y="municipio",
            hue="regiao",
            palette=CORES_REGIAO,
            dodge=False,
            ax=ax
        )
        ax.set_title("Top 10 Municípios por % de Bicicleta", fontsize=14, fontweight="bold")
        ax.set_xlabel("% dos trabalhadores que vão de bicicleta", fontsize=11)
        ax.set_ylabel("Município", fontsize=11)
        ax.legend(title="Região", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        p1, p2, p3 = top.iloc[0], top.iloc[1], top.iloc[2]
        st.write(f"**Análise:** {nome(p1)} lidera com {pct(p1['pct_bicicleta'])} dos trabalhadores indo de "
                 f"bicicleta, seguido de {nome(p2)} ({pct(p2['pct_bicicleta'])}) e {nome(p3)} "
                 f"({pct(p3['pct_bicicleta'])}). Entram só municípios com pelo menos {num(minimo)} trabalhadores.")

    with col2:
        top_abs = t.nlargest(10, "bicicleta")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=top_abs,
            x="bicicleta",
            y="municipio",
            hue="regiao",
            palette=CORES_REGIAO,
            dodge=False,
            ax=ax
        )
        ax.set_title("Top 10 Municípios por Número de Ciclistas", fontsize=14, fontweight="bold")
        ax.set_xlabel("Nº de trabalhadores que vão de bicicleta", fontsize=11)
        ax.set_ylabel("Município", fontsize=11)
        ax.legend(title="Região", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        a1 = top_abs.iloc[0]
        st.write(f"**Análise:** {nome(a1)} tem o maior número de ciclistas ({num(a1['bicicleta'])}), mas só "
                 f"{pct(a1['pct_bicicleta'])} dos seus trabalhadores vão de bicicleta. Cidades grandes aparecem "
                 "aqui por terem muita gente; por isso o ranking principal é o percentual.")

    with col3:
        pizza = df.groupby("grupo_modal")["pessoas"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8, 8))
        cores = sns.color_palette("Set2", len(pizza))
        ax.pie(
            pizza,
            labels=pizza.index,
            autopct="%1.1f%%",
            startangle=140,
            colors=cores,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5}
        )
        ax.set_title("Distribuição dos Trabalhadores por Tipo de Transporte", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        parte = 100 * pizza / pizza.sum()
        st.write(f"**Análise:** O transporte particular (carro e moto) leva {pct(parte.get('Particular', 0))} "
                 f"dos trabalhadores e o público (ônibus, BRT, trem e metrô) {pct(parte.get('Público', 0))}. "
                 f"A mobilidade ativa (bicicleta + a pé) responde por {pct(parte.get('Ativo', 0))}.")

    # ================= LINHA 2 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        reg = t.groupby("regiao", as_index=False)[["total", "bicicleta", "a_pe"]].sum()
        reg["Bicicleta"] = 100 * reg["bicicleta"] / reg["total"]
        reg["A pé"] = 100 * reg["a_pe"] / reg["total"]
        tb = reg.melt(id_vars="regiao", value_vars=["Bicicleta", "A pé"], var_name="meio", value_name="percentual")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=tb,
            x="regiao",
            y="percentual",
            hue="meio",
            order=[r for r in REGIOES if r in reg["regiao"].values],
            palette="Set2",
            errorbar=None,
            ax=ax
        )
        ax.set_title("Bicicleta e A Pé por Região", fontsize=14, fontweight="bold")
        ax.set_xlabel("Região", fontsize=11)
        ax.set_ylabel("% dos trabalhadores", fontsize=11)
        ax.legend(title="Meio", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        mb, mp = reg.loc[reg["Bicicleta"].idxmax()], reg.loc[reg["A pé"].idxmax()]
        st.write(f"**Análise:** O {mb['regiao']} tem o maior uso de bicicleta ({pct(mb['Bicicleta'])}) e o "
                 f"{mp['regiao']} o maior percentual a pé ({pct(mp['A pé'])}). No total, "
                 f"{pct(100 * t['bicicleta'].sum() / t['total'].sum())} vão de bicicleta e "
                 f"{pct(100 * t['a_pe'].sum() / t['total'].sum())} a pé.")

    r = E.resumo_descritivo(v["pct_bicicleta"])

    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(
            data=v,
            x="pct_bicicleta",
            kde=True,
            bins=20,
            color="#4c72b0",
            ax=ax,
        )
        ax.axvline(r["media"], color="red", linestyle="--", linewidth=2, label=f"Média ({pct(r['media'])})")
        ax.axvline(r["mediana"], color="#2b5c8f", linestyle="-", linewidth=2, label=f"Mediana ({pct(r['mediana'])})")
        ax.set_title("Distribuição do % de Bicicleta nos Municípios", fontsize=14, fontweight="bold")
        ax.set_xlabel("% dos trabalhadores que vão de bicicleta", fontsize=11)
        ax.set_ylabel("Nº de municípios", fontsize=11)
        ax.legend(frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = (f"**Análise:** A média é {pct(r['media'])}, a mediana {pct(r['mediana'])} e a moda "
                 f"{pct(r['moda'])}. ")
        if r["media"] > r["mediana"]:
            texto += ("A maioria dos municípios usa pouco a bicicleta e poucos usam muito (assimetria à direita); "
                      "por isso a mediana descreve melhor o município típico.")
        st.write(texto)

    with col3:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            data=v,
            x="regiao",
            y="pct_bicicleta",
            hue="regiao",
            order=[r_ for r_ in REGIOES if r_ in v["regiao"].values],
            palette=CORES_REGIAO,
            legend=False,
            ax=ax
        )
        ax.axhline(r["limite_superior"], color="red", linestyle="--", linewidth=1.5,
                   label=f"Limite de outlier ({pct(r['limite_superior'])})")
        ax.set_title("% de Bicicleta nos Municípios por Região", fontsize=14, fontweight="bold")
        ax.set_xlabel("Região", fontsize=11)
        ax.set_ylabel("% dos trabalhadores que vão de bicicleta", fontsize=11)
        ax.legend(frameon=True)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        med = v.groupby("regiao")["pct_bicicleta"].median()
        st.write(f"**Análise:** Metade dos municípios fica entre {pct(r['q1'])} (Q1) e {pct(r['q3'])} (Q3), "
                 f"IQR de {num(r['iqr'], 1)} p.p. Acima de {pct(r['limite_superior'])} há "
                 f"{r['qtd_outliers']} outliers, as \"cidades da bicicleta\". A maior mediana é a do "
                 f"{med.idxmax()} ({pct(med.max())}).")

    # ================= LINHA 3 =================
    col1, col2, col3 = st.columns(3)

    with col1:
        cruz = df[df["meio"] == "Bicicleta"].groupby(["regiao", "raca"])["pessoas"].sum() \
            / df.groupby(["regiao", "raca"])["pessoas"].sum() * 100
        matriz = cruz.unstack("raca")
        matriz = matriz.reindex(index=[r_ for r_ in REGIOES if r_ in matriz.index],
                                columns=[c for c in RACAS if c in matriz.columns])
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(
            matriz,
            annot=True,
            fmt=".1f",
            cmap="YlGnBu",
            linewidths=0.5,
            cbar_kws={"label": "% de bicicleta"},
            ax=ax
        )
        ax.set_title("% de Bicicleta por Região e Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("Região", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        maior, menor = cruz.idxmax(), cruz.idxmin()
        st.write(f"**Análise:** O maior uso de bicicleta é entre pessoas {maior[1].lower()}s no "
                 f"{maior[0]} ({pct(cruz.max())}) e o menor entre pessoas {menor[1].lower()}s no "
                 f"{menor[0]} ({pct(cruz.min())}).")

    with col2:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(
            data=v,
            x="pct_a_pe",
            y="pct_bicicleta",
            hue="regiao",
            hue_order=[r_ for r_ in REGIOES if r_ in v["regiao"].values],
            palette=CORES_REGIAO,
            s=40,
            alpha=0.6,
            ax=ax
        )
        ax.set_title("Relação entre % A Pé e % de Bicicleta", fontsize=14, fontweight="bold")
        ax.set_xlabel("% dos trabalhadores que vão a pé", fontsize=11)
        ax.set_ylabel("% dos trabalhadores que vão de bicicleta", fontsize=11)
        ax.legend(title="Região", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        ativo = v.loc[v["pct_ativo"].idxmax()]
        st.write(f"**Análise:** A correlação entre ir a pé e ir de bicicleta é de "
                 f"{num(v['pct_a_pe'].corr(v['pct_bicicleta']), 2)}, fraca: ter muita gente a pé não significa ter muitos ciclistas. "
                 f"O destaque em mobilidade ativa total é {nome(ativo)}, com {pct(ativo['pct_ativo'])} "
                 f"({pct(ativo['pct_a_pe'])} a pé).")

    with col3:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(
            data=v,
            x="total",
            y="pct_bicicleta",
            logx=True,
            color="#2b5c8f",
            scatter_kws={"s": 20, "alpha": 0.4},
            line_kws={"color": "red", "linewidth": 2},
            ax=ax
        )
        ax.set_xscale("log")
        ax.set_title("Relação entre Tamanho do Município e % de Bicicleta", fontsize=14, fontweight="bold")
        ax.set_xlabel("Nº de trabalhadores (escala log)", fontsize=11)
        ax.set_ylabel("% dos trabalhadores que vão de bicicleta", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        inclinacao = np.polyfit(np.log10(v["total"]), v["pct_bicicleta"], 1)[0]
        corr = np.corrcoef(np.log10(v["total"]), v["pct_bicicleta"])[0, 1]
        forca = "fraca" if abs(corr) < 0.3 else "moderada" if abs(corr) < 0.7 else "forte"
        st.write(f"**Análise:** A correlação é de {num(corr, 2)} ({forca}). Cada vez que o número de trabalhadores "
                 f"é multiplicado por 10, o % de bicicleta muda em média {num(inclinacao, 1)} p.p.: a tendência é "
                 + ("cidades maiores pedalarem menos." if inclinacao < 0 else "cidades maiores pedalarem mais."))

    # ================= LINHA 4 (tabelas) =================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Medidas estatísticas (% de bicicleta)**")
        medidas = [("Nº de municípios", num(r["n"])), ("Média", pct(r["media"])), ("Mediana", pct(r["mediana"])),
                   ("Moda (1 casa)", pct(r["moda"])), ("Q1", pct(r["q1"])), ("Q3", pct(r["q3"])),
                   ("IQR", f"{num(r['iqr'], 1)} p.p."), ("Mínimo", pct(r["minimo"])), ("Máximo", pct(r["maximo"])),
                   ("Amplitude", f"{num(r['amplitude'], 1)} p.p."), ("Variância", num(r["variancia"], 1)),
                   ("Desvio padrão", f"{num(r['desvio_padrao'], 1)} p.p."),
                   ("Limite superior de outlier", pct(r["limite_superior"])), ("Outliers", num(r["qtd_outliers"]))]
        st.dataframe(pd.DataFrame(medidas, columns=["Medida", "Valor"]), hide_index=True, width="stretch")
        st.write(f"**Análise:** O desvio padrão de {num(r['desvio_padrao'], 1)} p.p. e a amplitude de "
                 f"{num(r['amplitude'], 1)} p.p. mostram que o uso da bicicleta é muito desigual entre os municípios.")

    with col2:
        st.write("**Capitais das personas**")
        p = t[t["cod_ibge"].isin(MUNICIPIOS_PERSONAS)].copy()
        if len(p):
            ranking = t[t["total"] >= minimo].sort_values("pct_bicicleta", ascending=False)["cod_ibge"].tolist()
            p["Posição"] = p["cod_ibge"].map(lambda c: f"{ranking.index(c) + 1}º" if c in ranking else "—")
            p["Cidade (gestor)"] = p["cod_ibge"].map(MUNICIPIOS_PERSONAS)
            tabela = p[["Cidade (gestor)", "pct_bicicleta", "pct_a_pe", "pct_ativo", "Posição"]] \
                .sort_values("pct_bicicleta", ascending=False).round(1) \
                .rename(columns={"pct_bicicleta": "% bicicleta", "pct_a_pe": "% a pé", "pct_ativo": "% ativo"})
            st.dataframe(tabela, hide_index=True, width="stretch")
            melhor, pior = tabela.iloc[0], tabela.iloc[-1]
            st.write(f"**Análise:** Entre as capitais das personas, {melhor['Cidade (gestor)']} tem o maior uso de "
                     f"bicicleta ({pct(melhor['% bicicleta'])}) e {pior['Cidade (gestor)']} o menor "
                     f"({pct(pior['% bicicleta'])}, {pior['Posição']} de {num(len(ranking))} no ranking).")
        else:
            st.write("Nenhuma capital das personas no território filtrado.")

    with col3:
        st.write("**Outliers: as \"cidades da bicicleta\"**")
        fora = E.marcar_outliers(v, "pct_bicicleta")
        fora = fora[fora["outlier"] == "Acima"].sort_values("pct_bicicleta", ascending=False)
        st.dataframe(fora[["municipio", "pct_bicicleta", "bicicleta"]].round(1)
                     .rename(columns={"municipio": "Município", "pct_bicicleta": "% bicicleta", "bicicleta": "Ciclistas"}),
                     hide_index=True, width="stretch")
        por_uf = fora["uf"].value_counts()
        if len(por_uf):
            st.write(f"**Análise:** São {len(fora)} municípios acima de {pct(r['limite_superior'])}. "
                     f"A UF com mais deles é {por_uf.index[0]} ({por_uf.iloc[0]}).")


# ---------------- SIDEBAR (dados do aluno + filtros) ----------------
def barra_lateral(dados: pd.DataFrame) -> dict:
    st.sidebar.header("Informações do Aluno")
    st.sidebar.write("**Nome:** Ana Clara Matias")
    st.sidebar.write("**Nº da chamada:** 03")
    st.sidebar.write("**Turma:** 3E2")

    st.sidebar.header("Filtros")
    regiao = st.sidebar.selectbox("Região", ["Brasil (todas)"] + REGIOES)
    regiao = None if regiao.startswith("Brasil") else regiao
    ufs = dados[dados["regiao"] == regiao]["uf"] if regiao else dados["uf"]
    uf = st.sidebar.selectbox("UF", ["Todas"] + sorted(ufs.unique()))
    uf = None if uf == "Todas" else uf
    racas = st.sidebar.multiselect("Cor ou raça", RACAS, default=RACAS)
    minimo = st.sidebar.slider("Mínimo de trabalhadores no ranking", 0, 100_000, 10_000, 1_000,
                               help="Municípios muito pequenos têm percentuais instáveis.")
    return {"regiao": regiao, "uf": uf, "racas": racas, "minimo": minimo}


if __name__ == "__main__":
    st.set_page_config(
        page_title="Mobilidade ativa",
        layout="wide",
        initial_sidebar_state="expanded",  # sidebar começa aberto e pode ser recolhido
    )
    dados_ac = carregar_dados()
    render(dados_ac, barra_lateral(dados_ac))
