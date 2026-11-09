"""
PAINEL — INGRID — RENDA E DESIGUALDADE NA MOBILIDADE
====================================================

Complementa as PERGUNTAS 1 e 2 da persona: relação entre renda, tempo e modal.

LIMITAÇÃO: o Censo 2022 não cruza MEIO DE TRANSPORTE × RENDA das pessoas. Por isso:
  A) Tempo × renda               (pessoas)               -> SIDRA 10331
  B) Renda do município × modal  (municípios)            -> SIDRA 10295 + 10330  (cuidado: falácia ecológica)
  C) Instrução × modal           (proxy socioeconômico)  -> SIDRA 10332

Rodar SOZINHO (a partir da pasta do projeto):
    streamlit run integrante_4_ingrid/painel.py

No dashboard do grupo, o app.py chama:  carregar_dados()  e  render(dados, filtros)
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from integrante_4_ingrid import estatisticas as E
from integrante_4_ingrid.etl import GRUPOS_MODAIS, INSTRUCAO_NIVEIS, PASTA_DADOS, RACAS, REGIOES, RENDA_FAIXAS, TEMPO_FAIXAS

FONTE = "Fonte: IBGE, Censo Demográfico 2022 (SIDRA 10331, 10295, 10330 e 10332)."
SALARIO_MINIMO_2022 = 1212
CORES_GRUPO = dict(zip(GRUPOS_MODAIS, sns.color_palette("Set2", len(GRUPOS_MODAIS))))
CORES_REGIAO = dict(zip(REGIOES, sns.color_palette("Set2", len(REGIOES))))


# ---------------- DADOS ----------------
@st.cache_data
def carregar_dados() -> dict:
    def ler(nome):
        return pd.read_csv(PASTA_DADOS / nome, dtype={"cod_ibge": str})
    return {"tempo_renda": ler("tempo_renda_raca_uf.csv"), "instrucao": ler("instrucao_meio_raca_uf.csv"),
            "renda_municipio": ler("renda_municipio.csv"), "meio_municipio": ler("meio_municipio.csv.gz")}


def territorio(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    """Bases com Brasil, região e UF (não têm municípios)."""
    if filtros.get("uf"):
        return df[(df["nivel"] == "UF") & (df["uf"] == filtros["uf"])]
    if filtros.get("regiao"):
        return df[(df["nivel"] == "Região") & (df["regiao"] == filtros["regiao"])]
    return df[df["nivel"] == "Brasil"]


def municipios(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    if filtros.get("regiao"):
        df = df[df["regiao"] == filtros["regiao"]]
    if filtros.get("uf"):
        df = df[df["uf"] == filtros["uf"]]
    return df


# ---------------- FORMATAÇÃO (número no padrão brasileiro) ----------------
def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor, 1)}%"


def minutos(valor):
    return f"{num(valor, 1)} min"


def reais(valor):
    return f"R$ {num(valor)}"


def presentes(ordem, valores):
    return [x for x in ordem if x in set(valores)]


# ---------------- PAINEL ----------------
def render(dados: dict, filtros: dict) -> None:
    st.title("Renda e desigualdade na mobilidade")
    st.write("**Pergunta:** quem ganha menos gasta mais tempo e usa mais transporte público? · " + FONTE)
    st.write("**Atenção:** o Censo 2022 não publica meio de transporte × renda das pessoas. Por isso a análise "
             "tem três partes: **A)** tempo × renda (pessoas), **B)** renda do município × modal (municípios) e "
             "**C)** nível de instrução × modal (um substituto da renda).")

    racas = filtros.get("racas") or RACAS
    tempo_renda = territorio(dados["tempo_renda"], filtros)
    tempo_renda = tempo_renda[tempo_renda["raca"].isin(racas)
                              & tempo_renda["renda_faixa"].isin(filtros.get("rendas") or RENDA_FAIXAS)]
    if tempo_renda["pessoas"].sum() == 0:
        st.error("Nenhuma pessoa com esses filtros. Amplie a seleção.")
        return
    por_renda = E.tempo_por_renda(tempo_renda, RENDA_FAIXAS)
    faixas = por_renda[por_renda["renda_faixa"] != "Sem rendimento"]  # só 19 mil pessoas: fica fora da comparação
    if faixas.empty:
        faixas = por_renda
    pobre, rica = faixas.iloc[0], faixas.iloc[-1]
    pior = faixas.loc[faixas["pct_mais_1h"].idxmax()]

    # ================= LINHA 1 — A) TEMPO × RENDA =================
    col1, col2, col3 = st.columns(3)

    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=por_renda,
            x="renda_faixa",
            y="pct_mais_1h",
            color="#4c72b0",
            errorbar=None,
            ax=ax
        )
        ax.set_title("Deslocamentos de Mais de 1 Hora por Renda", fontsize=14, fontweight="bold")
        ax.set_xlabel("Renda domiciliar per capita (salários mínimos)", fontsize=11)
        ax.set_ylabel("% com mais de 1 h", fontsize=11)
        ax.tick_params(axis="x", rotation=20)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.write(f"**Análise:** A faixa com mais viagens acima de 1 hora é {pior['renda_faixa']} "
                 f"({pct(pior['pct_mais_1h'])}); na faixa {rica['renda_faixa']} são {pct(rica['pct_mais_1h'])}. "
                 + (f"A faixa {pobre['renda_faixa']} tem só {pct(pobre['pct_mais_1h'])}: a mais pobre inclui muitos "
                    "trabalhadores rurais e de cidades pequenas, com trajetos curtos. "
                    if pobre["pct_mais_1h"] < pior["pct_mais_1h"] else "")
                 + "A faixa \"Sem rendimento\" tem poucas pessoas e deve ser lida com cautela.")

    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(
            data=por_renda,
            x="renda_faixa",
            y="mediana",
            marker="o",
            color="#2b5c8f",
            linewidth=2,
            ax=ax,
        )
        ax.set_title("Mediana Estimada do Tempo por Renda", fontsize=14, fontweight="bold")
        ax.set_xlabel("Renda domiciliar per capita (salários mínimos)", fontsize=11)
        ax.set_ylabel("Mediana estimada (min)", fontsize=11)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.write(f"**Análise:** A mediana do tempo vai de {minutos(faixas['mediana'].max())} na faixa "
                 f"{faixas.loc[faixas['mediana'].idxmax(), 'renda_faixa']} para {minutos(rica['mediana'])} na faixa "
                 f"{rica['renda_faixa']}"
                 + (": quem ganha mais tende a morar mais perto do trabalho." if rica["mediana"] < faixas["mediana"].max()
                    else "."))

    with col3:
        linhas = []
        for (renda, raca), g in tempo_renda.groupby(["renda_faixa", "raca"]):
            n = g["pessoas"].sum()
            mais = g[g["tempo_faixa"].isin(E.FAIXAS_MAIS_1H)]["pessoas"].sum()
            linhas.append({"renda_faixa": renda, "raca": raca, "pct": 100 * mais / n if n >= 1_000 else None})
        matriz = pd.DataFrame(linhas).pivot(index="renda_faixa", columns="raca", values="pct").astype(float)
        matriz = matriz.reindex(index=presentes(RENDA_FAIXAS, matriz.index), columns=presentes(RACAS, matriz.columns))
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(
            matriz,
            annot=True,
            fmt=".1f",
            cmap="YlGnBu",
            linewidths=0.5,
            cbar_kws={"label": "% com mais de 1 h"},
            ax=ax
        )
        ax.set_title("% com Mais de 1 Hora: Renda × Cor ou Raça", fontsize=14, fontweight="bold")
        ax.set_xlabel("Cor ou raça", fontsize=11)
        ax.set_ylabel("Renda (salários mínimos)", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = "**Análise:** Células vazias têm menos de 1.000 pessoas. "
        if {"Preta", "Branca"} <= set(matriz.columns):
            dif = (matriz["Preta"] - matriz["Branca"]).dropna()
            texto += (f"Na mesma faixa de renda, pessoas pretas têm mais viagens longas que brancas em "
                      f"{(dif > 0).sum()} de {len(dif)} faixas: a renda sozinha não explica a diferença racial.")
        st.write(texto)

    # ================= LINHA 2 — A) e C) =================
    col1, col2, col3 = st.columns(3)

    with col1:
        dist = E.participacao(tempo_renda, "tempo_faixa", por=["renda_faixa"])
        tb = dist.pivot(index="renda_faixa", columns="tempo_faixa", values="percentual")
        tb = tb.reindex(index=presentes(RENDA_FAIXAS, tb.index)[::-1], columns=presentes(TEMPO_FAIXAS, tb.columns))
        fig, ax = plt.subplots(figsize=(10, 6))
        tb.plot(
            kind="barh",
            stacked=True,
            color=sns.color_palette("YlGnBu", len(tb.columns)),
            edgecolor="white",
            ax=ax
        )
        ax.set_title("Faixa de Tempo por Renda (Barras 100% Empilhadas)", fontsize=14, fontweight="bold")
        ax.set_xlabel("% da faixa de renda", fontsize=11)
        ax.set_ylabel("Renda (salários mínimos)", fontsize=11)
        ax.set_xlim(0, 100)
        ax.legend(title="Tempo", frameon=True, loc="upper left", bbox_to_anchor=(1.01, 1))
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        ate15 = tb[presentes(["Até 5 min", "6 a 15 min"], tb.columns)].sum(axis=1)
        st.write(f"**Análise:** Chegam em até 15 minutos {pct(ate15.get(pobre['renda_faixa'], 0))} da faixa "
                 f"{pobre['renda_faixa']} e {pct(ate15.get(rica['renda_faixa'], 0))} da faixa {rica['renda_faixa']}. "
                 f"A faixa com mais viagens acima de 1 hora é {pior['renda_faixa']}.")

    with col2:
        pizza = tempo_renda.groupby("renda_faixa")["pessoas"].sum().reindex(presentes(RENDA_FAIXAS, tempo_renda["renda_faixa"]))
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            pizza,
            labels=[nome if 100 * v / pizza.sum() >= 1 else "" for nome, v in pizza.items()],  # sem rótulo < 1%
            autopct=lambda p: f"{p:.1f}%" if p >= 2 else "",  # fatias muito pequenas ficam sem número
            startangle=140,
            colors=sns.color_palette("Set2", len(pizza)),
            wedgeprops={"edgecolor": "white", "linewidth": 1.5}
        )
        ax.set_title("Distribuição dos Trabalhadores por Faixa de Renda", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        parte = 100 * pizza / pizza.sum()
        ate2 = parte[presentes(["Sem rendimento", "Até 1/4 SM", "1/4 a 1/2 SM", "1/2 a 1 SM", "1 a 2 SM"], parte.index)].sum()
        st.write(f"**Análise:** {pct(ate2)} dos trabalhadores têm renda domiciliar per capita de até 2 salários "
                 f"mínimos. A faixa mais comum é {parte.idxmax()} ({pct(parte.max())}).")

    with col3:
        instr = territorio(dados["instrucao"], filtros)
        instrucao = E.participacao(instr[instr["raca"].isin(racas)], "grupo_modal", por=["instrucao"])
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=instrucao,
            x="instrucao",
            y="percentual",
            hue="grupo_modal",
            order=presentes(INSTRUCAO_NIVEIS, instrucao["instrucao"]),
            hue_order=GRUPOS_MODAIS,
            palette=CORES_GRUPO,
            errorbar=None,
            ax=ax
        )
        ax.set_title("Grupo de Transporte por Nível de Instrução", fontsize=14, fontweight="bold")
        ax.set_xlabel("Nível de instrução (substituto da renda)", fontsize=11)
        ax.set_ylabel("% do nível de instrução", fontsize=11)
        ax.set_xticks(range(len(ax.get_xticklabels())))
        ax.set_xticklabels([t.get_text().replace(" / ", "\n") for t in ax.get_xticklabels()])
        ax.legend(title="Transporte", frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        part = instrucao[instrucao["grupo_modal"] == "Particular"].set_index("instrucao")["percentual"]
        pub = instrucao[instrucao["grupo_modal"] == "Público"].set_index("instrucao")["percentual"]
        st.write(f"**Análise:** Com superior completo, {pct(part.get(INSTRUCAO_NIVEIS[-1], 0))} usam carro ou moto, "
                 f"contra {pct(part.get(INSTRUCAO_NIVEIS[0], 0))} de quem não tem instrução. O transporte público "
                 f"tem o maior uso no nível {pub.idxmax()} ({pct(pub.max())}).")

    # ================= LINHA 3 — B) RENDA DO MUNICÍPIO =================
    minimo = filtros.get("minimo", 5_000)
    eco = E.modal_por_municipio(municipios(dados["meio_municipio"], filtros), dados["renda_municipio"], minimo)
    eco = eco.dropna(subset=["renda_mediana_pc"]).copy()
    eco["municipio"] = eco["local"] + " (" + eco["uf"] + ")"
    if len(eco) < 5:
        st.warning("Poucos municípios com esse mínimo de trabalhadores. Reduza o mínimo ou amplie o território.")
        return
    r = E.resumo_descritivo(eco["renda_mediana_pc"])
    r_part = E.correlacao(eco["renda_mediana_pc"], eco["pct_particular"])
    r_pub = E.correlacao(eco["renda_mediana_pc"], eco["pct_publico"])

    col1, col2, col3 = st.columns(3)

    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(
            data=eco,
            x="renda_mediana_pc",
            kde=True,
            bins=20,
            color="#4c72b0",
            ax=ax,
        )
        ax.axvline(r["media"], color="red", linestyle="--", linewidth=2, label=f"Média ({reais(r['media'])})")
        ax.axvline(r["mediana"], color="#2b5c8f", linestyle="-", linewidth=2, label=f"Mediana ({reais(r['mediana'])})")
        ax.set_title("Distribuição da Renda Mediana dos Municípios", fontsize=14, fontweight="bold")
        ax.set_xlabel("Renda domiciliar per capita mediana (R$)", fontsize=11)
        ax.set_ylabel("Nº de municípios", fontsize=11)
        ax.legend(frameon=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        texto = (f"**Análise:** Nos {num(r['n'])} municípios com pelo menos {num(minimo)} trabalhadores, a média é "
                 f"{reais(r['media'])}, a mediana {reais(r['mediana'])} e a moda {reais(r['moda'])}. ")
        if r["media"] < r["mediana"]:
            texto += "A média é MENOR que a mediana: muitos municípios com renda bem baixa a puxam para baixo. "
        else:
            texto += "A média é maior que a mediana: poucos municípios muito ricos a puxam para cima. "
        if abs(r["moda"] - SALARIO_MINIMO_2022) < 1:
            texto += ("A moda é exatamente o salário mínimo de 2022: muitos domicílios vivem de rendas iguais a "
                      "1 salário mínimo (aposentadorias, BPC, salários).")
        st.write(texto)

    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            data=eco,
            x="regiao",
            y="renda_mediana_pc",
            hue="regiao",
            order=presentes(REGIOES, eco["regiao"]),
            palette=CORES_REGIAO,
            legend=False,
            ax=ax
        )
        ax.axhline(r["limite_superior"], color="red", linestyle="--", linewidth=1.5,
                   label=f"Limite de outlier ({reais(r['limite_superior'])})")
        ax.set_title("Renda Mediana dos Municípios por Região", fontsize=14, fontweight="bold")
        ax.set_xlabel("Região", fontsize=11)
        ax.set_ylabel("Renda domiciliar per capita mediana (R$)", fontsize=11)
        ax.legend(frameon=True)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        med = eco.groupby("regiao")["renda_mediana_pc"].median()
        st.write(f"**Análise:** Metade dos municípios fica entre {reais(r['q1'])} (Q1) e {reais(r['q3'])} (Q3), "
                 f"IQR de {reais(r['iqr'])}. A maior mediana é a do {med.idxmax()} ({reais(med.max())}) e a menor "
                 f"a do {med.idxmin()} ({reais(med.min())}). Há {r['qtd_outliers']} outliers.")

    with col3:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(
            data=eco,
            x="renda_mediana_pc",
            y="pct_particular",
            color="#2b5c8f",
            scatter_kws={"s": 20, "alpha": 0.4},
            line_kws={"color": "red", "linewidth": 2},
            ax=ax
        )
        ax.set_title("Relação entre Renda do Município e Carro/Moto", fontsize=14, fontweight="bold")
        ax.set_xlabel("Renda domiciliar per capita mediana (R$)", fontsize=11)
        ax.set_ylabel("% que usa carro ou moto", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.write(f"**Análise:** Renda × carro/moto: r = {num(r_part, 2)} ({E.forca_correlacao(r_part)}). "
                 f"Renda × transporte público: r = {num(r_pub, 2)} ({E.forca_correlacao(r_pub)}). Isso descreve "
                 "municípios, não pessoas (falácia ecológica): uma cidade rica pode ter muitos moradores pobres "
                 "que usam ônibus.")

    # ================= LINHA 4 (tabelas) =================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Medidas estatísticas (renda mediana dos municípios)**")
        medidas = [("Nº de municípios", num(r["n"])), ("Média", reais(r["media"])), ("Mediana", reais(r["mediana"])),
                   ("Moda", reais(r["moda"])), ("Q1", reais(r["q1"])), ("Q3", reais(r["q3"])),
                   ("IQR", reais(r["iqr"])), ("Mínimo", reais(r["minimo"])), ("Máximo", reais(r["maximo"])),
                   ("Amplitude", reais(r["amplitude"])), ("Variância", f"{num(r['variancia'])} (R$)²"),
                   ("Desvio padrão", reais(r["desvio_padrao"])),
                   ("Limite superior de outlier", reais(r["limite_superior"])), ("Outliers", num(r["qtd_outliers"]))]
        st.dataframe(pd.DataFrame(medidas, columns=["Medida", "Valor"]), hide_index=True, width="stretch")
        st.write(f"**Análise:** O desvio padrão de {reais(r['desvio_padrao'])} mostra a desigualdade de renda "
                 "entre os municípios.")

    with col2:
        st.write("**Tempo de deslocamento por faixa de renda**")
        st.dataframe(por_renda.round(1).rename(columns={"renda_faixa": "Renda", "pessoas": "Pessoas",
                     "mediana": "Mediana (min)", "pct_mais_1h": "% > 1 h", "pct_mais_2h": "% > 2 h"}),
                     hide_index=True, width="stretch")
        st.write("**Análise:** A mediana é estimada pelas faixas de tempo do IBGE: "
                 "Mediana ≈ Li + ((n/2 − Fant) / fi) × h.")

    with col3:
        st.write("**Outliers: municípios com renda muito alta**")
        fora = E.marcar_outliers(eco, "renda_mediana_pc")
        fora = fora[fora["outlier"] == "Acima"].sort_values("renda_mediana_pc", ascending=False)
        st.dataframe(fora[["municipio", "renda_mediana_pc", "pct_publico", "pct_particular"]].round(1)
                     .rename(columns={"municipio": "Município", "renda_mediana_pc": "Renda mediana (R$)",
                                      "pct_publico": "% público", "pct_particular": "% carro/moto"}),
                     hide_index=True, width="stretch")
        if len(fora):
            st.write(f"**Análise:** São {len(fora)} municípios acima de {reais(r['limite_superior'])}. O maior é "
                     f"{fora.iloc[0]['municipio']}, com {reais(fora.iloc[0]['renda_mediana_pc'])}.")


# ---------------- SIDEBAR (dados do aluno + filtros) ----------------
def barra_lateral(dados: dict) -> dict:
    st.sidebar.header("Informações do Aluno")
    st.sidebar.write("**Nome:** Ingrid")
    st.sidebar.write("**Nº da chamada:** —")
    st.sidebar.write("**Turma:** —")

    st.sidebar.header("Filtros")
    regiao = st.sidebar.selectbox("Região", ["Brasil (todas)"] + REGIOES)
    regiao = None if regiao.startswith("Brasil") else regiao
    mun = dados["renda_municipio"]
    ufs = mun[mun["regiao"] == regiao]["uf"] if regiao else mun["uf"]
    uf = st.sidebar.selectbox("UF", ["Todas"] + sorted(ufs.unique()))
    uf = None if uf == "Todas" else uf
    racas = st.sidebar.multiselect("Cor ou raça", RACAS, default=RACAS)
    rendas = st.sidebar.multiselect("Renda domiciliar per capita", RENDA_FAIXAS, default=RENDA_FAIXAS)
    minimo = st.sidebar.slider("Mínimo de trabalhadores por município", 0, 50_000, 5_000, 1_000,
                               help="Municípios muito pequenos têm percentuais instáveis.")
    return {"regiao": regiao, "uf": uf, "racas": racas, "rendas": rendas, "minimo": minimo}


if __name__ == "__main__":
    st.set_page_config(
        page_title="Renda e mobilidade",
        layout="wide",
        initial_sidebar_state="expanded",  # sidebar começa aberto e pode ser recolhido
    )
    dados_ing = carregar_dados()
    render(dados_ing, barra_lateral(dados_ing))
