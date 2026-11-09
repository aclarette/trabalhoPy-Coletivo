"""
NÚMEROS QUE FALAM — DESCOBRINDO O BRASIL
Indicador 5: Transporte e Mobilidade Urbana (IBGE, Censo Demográfico 2022)
=========================================================================

Painel único do grupo: junta as partes individuais em um só app.

Rodar (a partir desta pasta):
    pip install -r requirements.txt
    streamlit run app.py

Como funciona a integração (ver docs/padrao_integracao.md):
    cada integrante tem um painel.py com   carregar_dados()   e   render(dados, filtros)
    este app monta a barra lateral (menu, filtros e upload) e chama o render() da página escolhida.
"""

import gzip
import io
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title="Números que Falam — Mobilidade Urbana",
    layout="wide",
    initial_sidebar_state="expanded",  # sidebar começa aberto e pode ser recolhido
)

from integrante_1_ana_karolina import painel as p_ak, estatisticas as e_ak
from integrante_2_alvaro import painel as p_alv, estatisticas as e_alv
from integrante_3_ana_clara import painel as p_ac, estatisticas as e_ac
from integrante_4_ingrid import painel as p_ing, estatisticas as e_ing
from integrante_3_ana_clara.etl import MUNICIPIOS_PERSONAS, REGIAO_POR_DIGITO, UF_SIGLA
from integrante_1_ana_karolina.etl import GRUPOS_MODAIS, MEIOS, RACAS, REGIOES
from integrante_4_ingrid.etl import RENDA_FAIXAS

# ---------------- IDENTIFICAÇÃO DO GRUPO (edite aqui) ----------------
STARTUP = "Rota Dados"  # nome da startup de análise de dados do grupo
TURMA = "3E2"
INTEGRANTES = [  # (nome, nº da chamada, parte no painel)
    ("Ana Karolina", "—", "Meios de transporte por raça"),
    ("Alvaro", "—", "Tempo de deslocamento"),
    ("Ana Clara Matias", "03", "Mobilidade ativa e bicicletas"),
    ("Ingrid", "—", "Renda e desigualdade na mobilidade"),
]
FONTE = "Fonte: IBGE, Censo Demográfico 2022 (SIDRA 10330, 10331, 10332 e 10295)."

PAGINAS = ["Início", "1. Transporte por raça", "2. Tempo de deslocamento", "3. Mobilidade ativa",
           "4. Renda e mobilidade", "Notícias e imagens", "Upload de dados"]
MINIMO_PADRAO = {"1. Transporte por raça": 5_000, "2. Tempo de deslocamento": 5_000,
                 "3. Mobilidade ativa": 10_000, "4. Renda e mobilidade": 5_000}
CORES_GRUPO = dict(zip(GRUPOS_MODAIS, sns.color_palette("Set2", len(GRUPOS_MODAIS))))
CORES_REGIAO = dict(zip(REGIOES, sns.color_palette("Set2", len(REGIOES))))


# ---------------- FORMATAÇÃO (número no padrão brasileiro) ----------------
def num(valor, casas=0):
    if valor is None or pd.isna(valor):
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return f"{num(valor, 1)}%"


def minutos(valor):
    return f"{num(valor, 1)} min"


def presentes(ordem, valores):
    return [x for x in ordem if x in set(valores)]


# ================= UPLOAD DE DADOS =================
TERRITORIO = ["nivel", "cod_ibge", "local", "uf", "regiao"]
BASES = {  # nome da base: (colunas obrigatórias, é base de municípios?, onde entra, descrição)
    "renda_municipio": (TERRITORIO + ["renda_media_pc", "renda_mediana_pc"], True,
                        [("ing", "renda_municipio")], "Renda per capita dos municípios (SIDRA 10295)"),
    "tempo_renda_raca_uf": (TERRITORIO + ["tempo_faixa", "raca", "renda_faixa", "pessoas"], False,
                            [("ing", "tempo_renda")], "Tempo × raça × renda (SIDRA 10331)"),
    "instrucao_meio_raca_uf": (TERRITORIO + ["raca", "instrucao", "meio", "pessoas", "grupo_modal"], False,
                               [("ing", "instrucao")], "Meio × instrução × raça (SIDRA 10332)"),
    "tempo_meio_raca_uf": (TERRITORIO + ["tempo_faixa", "meio", "raca", "pessoas"], False,
                           [("alv", "uf")], "Tempo × meio × raça, Brasil/regiões/UFs (SIDRA 10330)"),
    "tempo_raca_municipio": (TERRITORIO + ["tempo_faixa", "raca", "pessoas"], True,
                             [("alv", "municipio")], "Tempo × raça dos municípios (SIDRA 10330)"),
    "transporte_raca_municipio": (TERRITORIO + ["meio", "raca", "pessoas", "grupo_modal"], True,
                                  [("ak", "municipio"), ("ac", None)], "Meio × raça dos municípios (SIDRA 10330)"),
    "transporte_raca_uf": (TERRITORIO + ["meio", "raca", "pessoas", "grupo_modal"], False,
                           [("ak", "uf")], "Meio × raça, Brasil/regiões/UFs (SIDRA 10330)"),
    "meio_municipio": (TERRITORIO + ["meio", "pessoas", "grupo_modal"], True,
                       [("ing", "meio_municipio")], "Meio de transporte dos municípios (SIDRA 10330)"),
}


@st.cache_data(show_spinner="Lendo o arquivo enviado...")
def ler_arquivo(nome: str, conteudo: bytes) -> pd.DataFrame:
    """Lê CSV (separado por vírgula ou ponto e vírgula), CSV compactado (.gz) ou XLSX."""
    nome = nome.lower()
    if nome.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(conteudo), dtype={"cod_ibge": str})
    if nome.endswith(".gz"):
        conteudo = gzip.decompress(conteudo)
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            primeira_linha = conteudo[:5000].decode(codificacao, errors="strict").split("\n")[0]
            separador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","
            df = pd.read_csv(io.BytesIO(conteudo), sep=separador, encoding=codificacao, dtype={"cod_ibge": str})
            return converter_numeros(df)
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível ler o arquivo.")


def converter_numeros(df: pd.DataFrame) -> pd.DataFrame:
    """Colunas de texto que são números com vírgula decimal (padrão brasileiro) viram numéricas."""
    for coluna in df.columns:
        if coluna != "cod_ibge" and not pd.api.types.is_numeric_dtype(df[coluna]):
            convertido = pd.to_numeric(df[coluna].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            if convertido.notna().mean() >= 0.9:
                df[coluna] = convertido
    return df


def identificar_base(df: pd.DataFrame) -> str | None:
    """Descobre, pelas colunas, qual base do projeto o arquivo enviado substitui (ou None)."""
    colunas = set(df.columns)
    if "nivel" not in colunas or df.empty:
        return None
    municipal = bool((df["nivel"] == "Município").all())
    for nome, (obrigatorias, de_municipio, _, _) in BASES.items():
        if set(obrigatorias) <= colunas and de_municipio == municipal:
            return nome
    return None


def carregar_tudo(arquivos) -> tuple[dict, list[dict]]:
    """Bases dos 4 integrantes + as bases enviadas pelo upload (que substituem as originais)."""
    dados = {"ak": dict(p_ak.carregar_dados()), "alv": dict(p_alv.carregar_dados()),
             "ac": p_ac.carregar_dados(), "ing": dict(p_ing.carregar_dados())}
    enviados = []
    for arquivo in arquivos or []:
        registro = {"nome": arquivo.name, "df": None, "base": None, "erro": None}
        try:
            df = ler_arquivo(arquivo.name, arquivo.getvalue())
            registro["df"] = df
            base = identificar_base(df)
            if base:
                df = df.copy()
                df["cod_ibge"] = df["cod_ibge"].astype(str)
                for coluna in ["pessoas", "renda_media_pc", "renda_mediana_pc"]:
                    if coluna in df.columns:
                        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
                for quem, chave in BASES[base][2]:
                    if chave is None:
                        dados[quem] = df
                    else:
                        dados[quem][chave] = df
                registro["base"] = base
        except Exception as erro:  # arquivo corrompido ou em formato desconhecido: avisa e segue com a base original
            registro["erro"] = str(erro)
        enviados.append(registro)
    return dados, enviados


# ================= BARRA LATERAL =================
def barra_lateral() -> tuple[str, dict, list]:
    sb = st.sidebar
    sb.header("Números que Falam")
    pagina = sb.radio("Indicador", PAGINAS)

    sb.header("Informações do Grupo")
    sb.write(f"**Startup:** {STARTUP}")
    sb.write(f"**Turma:** {TURMA}")
    for nome, numero, parte in INTEGRANTES:
        sb.write(f"**{nome}** (nº {numero}): {parte}")

    sb.header("Filtros")
    regiao = sb.selectbox("Região", ["Brasil (todas)"] + REGIOES)
    regiao = None if regiao.startswith("Brasil") else regiao
    ufs = sorted(sigla for codigo, sigla in UF_SIGLA.items() if not regiao or REGIAO_POR_DIGITO[codigo[0]] == regiao)
    uf = sb.selectbox("UF", ["Todas"] + ufs)
    uf = None if uf == "Todas" else uf
    racas = sb.multiselect("Cor ou raça", RACAS, default=RACAS)
    meios = sb.multiselect("Meio de transporte", MEIOS, default=MEIOS,
                           help="Vale para as páginas 1 e 2 (onde o IBGE cruza o meio com raça e tempo).")
    rendas = sb.multiselect("Categoria de renda (domiciliar per capita)", RENDA_FAIXAS, default=RENDA_FAIXAS,
                            help="Vale para a página 4: o Censo só cruza a renda com o tempo de deslocamento.")
    filtros = {"regiao": regiao, "uf": uf, "racas": racas, "meios": meios, "rendas": rendas}
    if pagina in MINIMO_PADRAO:
        filtros["minimo"] = sb.slider("Mínimo de trabalhadores por município", 0, 100_000, MINIMO_PADRAO[pagina],
                                      1_000, key=f"minimo_{pagina}",
                                      help="Municípios muito pequenos têm percentuais instáveis.")

    sb.header("Upload de dados")
    arquivos = sb.file_uploader("Base do IBGE (CSV ou XLSX)", type=["csv", "gz", "xlsx"], accept_multiple_files=True,
                                help="Envie uma base tratada do projeto para substituir a original, ou qualquer "
                                     "tabela do IBGE para explorar na página \"Upload de dados\".")
    return pagina, filtros, arquivos


# ================= PÁGINA INICIAL =================
def pagina_inicio(dados: dict, filtros: dict) -> None:
    st.title("Números que Falam — Transporte e Mobilidade Urbana")
    st.write(f"**{STARTUP}**, consultoria de análise de dados · " + FONTE)
    st.write("**Nossos clientes:** Fernando (Secretário Nacional de Mobilidade Urbana), Ana (Gestora de Transportes da "
             "Região Metropolitana de Goiânia), Luciene (Prefeita de Vitória), Pedrinho (Prefeito de Belo Horizonte) e "
             "Lucas (Especialista em Logística de Brasília). **O pedido:** avaliar os modais de transporte mais "
             "utilizados por raça.")
    local = filtros["uf"] or (f"Região {filtros['regiao']}" if filtros["regiao"] else "Brasil")
    st.write(f"**Território:** {local} · **Universo:** pessoas ocupadas que se deslocam para o trabalho. "
             "Use o menu da barra lateral para abrir a análise completa de cada integrante.")

    f = dict(filtros, meios=MEIOS)  # a página inicial sempre considera todos os meios de transporte
    tempo = p_alv.selecionar(dados["alv"], f)
    modal = p_ak.selecionar(dados["ak"], f)
    if tempo["pessoas"].sum() == 0 or modal["pessoas"].sum() == 0:
        st.error("Nenhuma pessoa com esses filtros. Amplie a seleção.")
        return

    # ---------------- PERGUNTA 1 ----------------
    st.header("Pergunta 1: qual é a mediana do tempo por meio de transporte e raça?")
    geral = e_alv.resumo_agrupado(tempo)
    por_raca = e_alv.resumo_por_categoria(tempo, "raca", RACAS).set_index("raca")
    for coluna, meio in zip(st.columns(4), ["Automóvel", "Ônibus", "Trem ou metrô", "Bicicleta"]):
        do_meio = tempo[tempo["meio"] == meio]
        mediana = e_alv.quantil_agrupado(e_alv.frequencias(do_meio), 0.5)
        por = {}
        for raca in presentes(RACAS, do_meio["raca"]):
            fr = e_alv.frequencias(do_meio[do_meio["raca"] == raca])
            if fr.sum() >= p_alv.MIN_PESSOAS:
                por[raca] = e_alv.quantil_agrupado(fr, 0.5)
        diferenca = None
        if "Preta" in por and "Branca" in por:
            diferenca = f"{por['Preta'] - por['Branca']:+.1f} min (pretas × brancas)".replace(".", ",")
        coluna.metric(f"{meio}: mediana do tempo", minutos(mediana), diferenca, delta_color="off")
        coluna.caption(" · ".join(f"{raca} {num(v, 1)}" for raca, v in por.items()))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mediana geral (todos os meios)", minutos(geral["mediana"]))
    c2.metric("Maior mediana por raça", f"{por_raca['mediana'].idxmax()}: {minutos(por_raca['mediana'].max())}")
    c3.metric("Levam mais de 1 hora", pct(geral["pct_mais_1h"]))
    c4.metric("Levam mais de 2 horas", pct(geral["pct_mais_2h"]))

    # ---------------- PERGUNTA 2 ----------------
    st.header("Pergunta 2: transporte público × particular × ativo")
    grupos = 100 * modal.groupby("grupo_modal")["pessoas"].sum() / modal["pessoas"].sum()
    grupo_raca = e_ak.participacao(modal, "grupo_modal", por=["raca"])
    publico = grupo_raca[grupo_raca["grupo_modal"] == "Público"].set_index("raca")["percentual"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transporte público (ônibus, BRT, trem/metrô)", pct(grupos.get("Público", 0)))
    c2.metric("Transporte particular (carro, moto)", pct(grupos.get("Particular", 0)))
    c3.metric("Transporte ativo (a pé, bicicleta)", pct(grupos.get("Ativo", 0)))
    c4.metric("Modal predominante (moda)", e_ak.moda_categorica(modal, "meio"))
    if len(publico):
        st.caption("Transporte público por cor ou raça: "
                   + " · ".join(f"{raca} {pct(publico[raca])}" for raca in presentes(RACAS, publico.index)))

    # ---------------- PERGUNTA 3 ----------------
    st.header("Pergunta 3: quais cidades têm mais mobilidade ativa (bicicleta)?")
    bike = e_ac.tabela_municipal(p_ac.filtrar(dados["ac"], f))
    bike["municipio"] = bike["local"] + " (" + bike["uf"] + ")"
    ranking = bike[bike["total"] >= MINIMO_PADRAO["3. Mobilidade ativa"]].sort_values("pct_bicicleta", ascending=False)
    colunas = st.columns(4)
    colunas[0].metric("Vão de bicicleta (território)", pct(100 * bike["bicicleta"].sum() / bike["total"].sum()))
    for coluna, (posicao, (_, linha)) in zip(colunas[1:], enumerate(ranking.head(3).iterrows(), start=1)):
        coluna.metric(f"{posicao}º em % de bicicleta", linha["municipio"], pct(linha["pct_bicicleta"]), delta_color="off")
    st.caption(f"Ranking entre municípios com pelo menos {num(MINIMO_PADRAO['3. Mobilidade ativa'])} trabalhadores.")

    # ---------------- RENDA ----------------
    st.header("Complemento: a renda muda o deslocamento?")
    tr = p_ing.territorio(dados["ing"]["tempo_renda"], f)
    tr = tr[tr["raca"].isin(filtros["racas"] or RACAS)]
    por_renda = e_ing.tempo_por_renda(tr, RENDA_FAIXAS)
    por_renda = por_renda[por_renda["renda_faixa"] != "Sem rendimento"]
    if len(por_renda):
        pior, rica = por_renda.loc[por_renda["pct_mais_1h"].idxmax()], por_renda.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Mais de 1 h: faixa {pior['renda_faixa']}", pct(pior["pct_mais_1h"]))
        c2.metric(f"Mais de 1 h: faixa {rica['renda_faixa']}", pct(rica["pct_mais_1h"]))
        c3.metric(f"Mediana do tempo: {pior['renda_faixa']}", minutos(pior["mediana"]))
        c4.metric(f"Mediana do tempo: {rica['renda_faixa']}", minutos(rica["mediana"]))
        st.caption("O Censo 2022 não cruza meio de transporte com renda das pessoas: ver a página 4.")

    # ================= GRÁFICOS PEDIDOS PELOS GESTORES =================
    st.header("Gráficos principais")
    col1, col2, col3 = st.columns(3)

    with col1:
        pizza = modal.groupby("grupo_modal")["pessoas"].sum().reindex(GRUPOS_MODAIS).dropna()
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            pizza,
            labels=pizza.index,
            autopct="%1.1f%%",
            startangle=140,
            colors=[CORES_GRUPO[g] for g in pizza.index],
            wedgeprops={"edgecolor": "white", "linewidth": 1.5}
        )
        ax.set_title("Modal de Transporte Predominante", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.write(f"**Análise:** O transporte particular leva {pct(grupos.get('Particular', 0))} dos trabalhadores, "
                 f"o público {pct(grupos.get('Público', 0))} e o ativo {pct(grupos.get('Ativo', 0))}. O meio mais "
                 f"usado é {e_ak.moda_categorica(modal, 'meio')}.")

    v = p_alv.medianas_municipais(p_alv.municipios(dados["alv"], f))
    v = v[v["total"] >= MINIMO_PADRAO["2. Tempo de deslocamento"]].dropna(subset=["mediana"]).copy()
    v["municipio"] = v["local"] + " (" + v["uf"] + ")"
    r = e_alv.resumo_descritivo(v["mediana"]) if len(v) >= 5 else None

    with col2:
        if r is None:
            st.write("Poucos municípios neste território para o boxplot.")
        else:
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
            ax.set_title("Tempo de Deslocamento nos Municípios (Gargalos)", fontsize=14, fontweight="bold")
            ax.set_xlabel("Região", fontsize=11)
            ax.set_ylabel("Mediana estimada do município (min)", fontsize=11)
            ax.legend(frameon=True)
            ax.grid(True, axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
            gargalo = v.loc[v["pct_mais_1h"].idxmax()]
            st.write(f"**Análise:** Cada ponto acima da linha vermelha é um município outlier: são "
                     f"{r['qtd_outliers']} gargalos acima de {minutos(r['limite_superior'])}. A média "
                     f"({minutos(r['media'])}) fica acima da mediana ({minutos(r['mediana'])}) porque esses outliers "
                     f"a puxam para cima. O pior caso é {gargalo['municipio']}, onde {pct(gargalo['pct_mais_1h'])} "
                     "levam mais de 1 hora.")

    with col3:
        top = ranking.head(10)
        if top.empty:
            st.write("Nenhum município com o mínimo de trabalhadores neste território.")
        else:
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
            maior_abs = bike.loc[bike["bicicleta"].idxmax()]
            st.write(f"**Análise:** {top.iloc[0]['municipio']} lidera, com {pct(top.iloc[0]['pct_bicicleta'])} dos "
                     f"trabalhadores indo de bicicleta. Em número absoluto, o maior é {maior_abs['municipio']} "
                     f"({num(maior_abs['bicicleta'])} ciclistas, só {pct(maior_abs['pct_bicicleta'])} dos seus "
                     "trabalhadores): por isso o ranking usa o percentual.")

    # ================= TABELAS =================
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Resumo estatístico dos indicadores municipais**")
        publico_mun = e_ak.percentual_por_municipio(p_ak.municipios(dados["ak"], f), "grupo_modal", ["Público"],
                                                    MINIMO_PADRAO["1. Transporte por raça"])
        eco = e_ing.modal_por_municipio(p_ing.municipios(dados["ing"]["meio_municipio"], f),
                                        dados["ing"]["renda_municipio"], MINIMO_PADRAO["4. Renda e mobilidade"])
        series = {"% transporte público": publico_mun["percentual"], "Mediana do tempo (min)": v["mediana"],
                  "% bicicleta": ranking["pct_bicicleta"], "Renda mediana (R$)": eco["renda_mediana_pc"]}
        linhas = []
        for nome, serie in series.items():
            d = e_ac.resumo_descritivo(serie)
            if d["n"] >= 5:
                linhas.append({"Indicador": nome, "Municípios": d["n"], "Média": d["media"], "Mediana": d["mediana"],
                               "Q1": d["q1"], "Q3": d["q3"], "IQR": d["iqr"], "Amplitude": d["amplitude"],
                               "Desvio padrão": d["desvio_padrao"], "Outliers": d["qtd_outliers"]})
        if linhas:
            st.dataframe(pd.DataFrame(linhas).round(1), hide_index=True, width="stretch")
            assimetricos = [x["Indicador"] for x in linhas if x["Média"] > x["Mediana"]]
            st.write("**Análise:** Cada município é uma observação. Outliers pela regra de 1,5 × IQR. "
                     + (f"A média fica acima da mediana em: {', '.join(assimetricos)} (poucos municípios com valores "
                        "muito altos puxam a média). " if assimetricos else "")
                     + "Nesses casos a mediana descreve melhor o município típico.")

    with col2:
        st.write("**As cidades dos nossos clientes**")
        brasil = {"racas": filtros["racas"], "meios": MEIOS}
        t_bike = e_ac.tabela_municipal(p_ac.filtrar(dados["ac"], brasil)).set_index("cod_ibge")
        t_tempo = p_alv.medianas_municipais(p_alv.municipios(dados["alv"], brasil)).set_index("cod_ibge")
        t_pub = e_ak.percentual_por_municipio(p_ak.municipios(dados["ak"], brasil), "grupo_modal", ["Público"]) \
            .set_index("cod_ibge")
        linhas = []
        for codigo, cidade in MUNICIPIOS_PERSONAS.items():
            if codigo in t_bike.index and codigo in t_tempo.index and codigo in t_pub.index:
                linhas.append({"Cidade (gestor)": cidade, "% público": t_pub.loc[codigo, "percentual"],
                               "% bicicleta": t_bike.loc[codigo, "pct_bicicleta"], "% a pé": t_bike.loc[codigo, "pct_a_pe"],
                               "Mediana (min)": t_tempo.loc[codigo, "mediana"], "% > 1 h": t_tempo.loc[codigo, "pct_mais_1h"]})
        if linhas:
            cidades = pd.DataFrame(linhas)
            st.dataframe(cidades.round(1), hide_index=True, width="stretch")
            lenta, pedala = cidades.loc[cidades["Mediana (min)"].idxmax()], cidades.loc[cidades["% bicicleta"].idxmax()]
            menos = cidades.loc[cidades["% bicicleta"].idxmin()]
            st.write(f"**Análise:** {lenta['Cidade (gestor)']} tem o maior tempo mediano ({minutos(lenta['Mediana (min)'])}; "
                     f"{pct(lenta['% > 1 h'])} acima de 1 hora). {pedala['Cidade (gestor)']} é onde mais se pedala "
                     f"({pct(pedala['% bicicleta'])}) e {menos['Cidade (gestor)']} onde menos ({pct(menos['% bicicleta'])}). "
                     "Esta tabela mostra sempre as quatro cidades, sem os filtros de região e UF.")

    st.header("O que recomendamos aos gestores")
    st.write("- **Fernando (Secretaria Nacional):** o ônibus é o meio em que pessoas pretas e pardas são maioria e "
             "um dos que têm as viagens mais longas. Investir em qualidade, preço e velocidade do transporte coletivo "
             "(faixas exclusivas, BRT, metrô) reduz a desigualdade racial no tempo de deslocamento.\n"
             "- **Ana (Goiânia) e Lucas (Brasília):** os municípios do entorno do Distrito Federal em Goiás estão "
             "entre os maiores gargalos do país. A prioridade é a ligação entre as cidades-dormitório e os centros "
             "de emprego.\n"
             "- **Luciene (Vitória):** cidade plana e litorânea, como as líderes do ranking de bicicleta. Ciclovias "
             "conectadas e bicicletários nos terminais aproveitam esse potencial.\n"
             "- **Pedrinho (Belo Horizonte):** o uso de bicicleta é muito baixo, mas muita gente já vai a pé. Há "
             "espaço para bicicleta elétrica e compartilhada em trajetos curtos, integrada ao ônibus.\n"
             "- **Para todos:** tarifa social e integração tarifária alcançam as faixas de renda que concentram "
             "as viagens de mais de 1 hora.")


# ================= NOTÍCIAS E IMAGENS =================
IMAGENS = [  # (arquivo local opcional em imagens/, endereço, legenda)
    ("transito.jpg",
     "https://commons.wikimedia.org/wiki/Special:FilePath/Traffic%20jam%20Marginal%20Pinheiros%206122%20SAO%2007%202009.jpg?width=900",
     "Congestionamento na Marginal Pinheiros, São Paulo. Foto: Mariordo / Wikimedia Commons."),
    ("metro.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Central_station%2C_Metr%C3%B4_do_DF%2C_04-01-2007.jpg/640px-Central_station%2C_Metr%C3%B4_do_DF%2C_04-01-2007.jpg",
     "Estação Central do Metrô do Distrito Federal, Brasília. Foto: Wikimedia Commons."),
    ("ciclovia.jpg",
     "https://commons.wikimedia.org/wiki/Special:FilePath/Ciclovia%20Orla%20de%20Camburi.jpg?width=900",
     "Ciclovia da orla de Camburi, Vitória. Foto: Wikimedia Commons."),
]
NOTICIAS = {
    "Caos no trânsito": [
        ("Recife tem o trânsito mais congestionado entre as capitais do país, diz estudo", "Diário de Pernambuco, 15/05/2026",
         "Levantamento internacional de tráfego coloca Recife à frente de Porto Alegre, Belo Horizonte e São Paulo em nível de congestionamento.",
         "https://www.diariodepernambuco.com.br/vida-urbana/2026/05/11714322-motoristas-perderam-130-horas-no-transito-do-recife-em-2025-diz-pesquisa.html"),
        ("Curitiba supera São Paulo e acende alerta sobre mobilidade urbana no Brasil", "Portal do Trânsito, 15/05/2026",
         "A capital paranaense passou a liderar o ranking de horas perdidas no trânsito; o aumento da frota e a dependência do carro aparecem como causas.",
         "https://www.portaldotransito.com.br/noticias/mobilidade-e-tecnologia/mobilidade-urbana/curitiba-supera-sao-paulo-e-acende-alerta-sobre-mobilidade-urbana-no-brasil/"),
        ("1,3 milhão de brasileiros levam mais de duas horas para chegar ao trabalho, diz IBGE", "InfoMoney, 10/2025",
         "Os resultados do Censo 2022 mostram quantos trabalhadores enfrentam os deslocamentos mais longos do país.",
         "https://www.infomoney.com.br/?p=3056750"),
    ],
    "O que o Censo 2022 mostrou": [
        ("Automóvel é o meio de transporte mais utilizado no deslocamento para o trabalho", "Agência de Notícias do IBGE, 09/10/2025",
         "Notícia oficial da divulgação dos dados que usamos neste painel: pela primeira vez o Censo investigou o meio de transporte para o trabalho.",
         "https://agenciadenoticias.ibge.gov.br/agencia-noticias/noticias/44713-automovel-e-o-meio-de-transporte-mais-utilizado-no-deslocamento-para-o-trabalho"),
        ("Mais pobres e pretos gastam mais tempo no transporte até o trabalho no Brasil", "Acessa.com / Folhapress, 10/2025",
         "A reportagem destaca a mesma desigualdade de tempo por raça e renda que aparece nas páginas 2 e 4 deste painel.",
         "https://www.acessa.com/noticias/2025/10/287929-mais-pobres-e-pretos-gastam-mais-tempo-no-transporte-ate-o-trabalho-no-brasil.html"),
        ("Censo dos Deslocamentos do IBGE mostra a necessidade de BRTs metropolitanos", "Diário do Transporte, 14/12/2025",
         "Análise do setor de transporte sobre o peso do transporte individual e o pouco uso de BRT nas regiões metropolitanas.",
         "https://diariodotransporte.com.br/2025/12/14/inedito-censo-dos-deslocamentos-do-ibge-pela-primeira-vez-mostra-a-necessidade-de-brts-metropolitanos-menos-usados-que-pau-de-arara-e-mototaxis/"),
    ],
    "Mobilidade sustentável": [
        ("Menos emissões, mais qualidade de vida: o impacto da bicicleta nas cidades", "Agência Gov, 06/2026",
         "A mobilidade ativa (bicicleta e a pé) é um dos destaques da construção do Plano Nacional de Mobilidade Urbana.",
         "https://agenciagov.ebc.com.br/noticias/202606/menos-emissoes-mais-qualidade-de-vida-o-impacto-da-bicicleta-nas-cidades"),
        ("Cidades anuncia mais de R$ 2,5 bi para mobilidade urbana", "Agência Gov, 03/02/2026",
         "Investimentos federais em projetos de mobilidade e na renovação da frota de ônibus por veículos menos poluentes.",
         "https://agenciagov.ebc.com.br/noticias/202602/cidades-anuncia-mais-de-r-2-5-bi-para-mobilidade-urbana-e-renovacao-do-transporte-publico"),
        ("Estudo aponta 187 projetos de mobilidade urbana até 2054", "Portal do Trânsito, 30/11/2025",
         "O Estudo Nacional de Mobilidade Urbana (BNDES e Ministério das Cidades) planeja o transporte de média e alta capacidade em 21 regiões metropolitanas.",
         "https://www.portaldotransito.com.br/noticias/mobilidade-e-tecnologia/mobilidade-urbana/estudo-aponta-187-projetos-de-mobilidade-urbana-ate-2054-e-preve-reducao-de-8-mil-mortes-no-transito/"),
    ],
}


def pagina_noticias() -> None:
    st.title("Notícias e imagens")
    st.write("**Contexto:** o que a imprensa e os órgãos públicos estão dizendo sobre trânsito, o Censo 2022 e a "
             "mobilidade sustentável. Cada título abre a reportagem original.")
    pasta = Path(__file__).resolve().parent / "imagens"
    for coluna, (arquivo, endereco, legenda) in zip(st.columns(3), IMAGENS):
        local = pasta / arquivo
        coluna.image(str(local) if local.exists() else endereco, caption=legenda, width="stretch")
    for coluna, (tema, itens) in zip(st.columns(3), NOTICIAS.items()):
        with coluna:
            st.header(tema)
            for titulo, fonte, resumo, endereco in itens:
                st.write(f"**[{titulo}]({endereco})**")
                st.caption(fonte)
                st.write(resumo)


# ================= PÁGINA DE UPLOAD =================
def pagina_upload(dados: dict, enviados: list[dict]) -> None:
    st.title("Upload de dados")
    st.write("**Como funciona:** envie um arquivo CSV ou XLSX na barra lateral. Se ele tiver as colunas de uma das "
             "bases tratadas do projeto, substitui a base original e todas as páginas são recalculadas. Qualquer outra "
             "tabela do IBGE pode ser explorada aqui, com as medidas estatísticas de uma coluna numérica.")

    with st.expander("Bases que o painel reconhece (e modelos para baixar)"):
        st.dataframe(pd.DataFrame([{"Base": nome, "O que é": descricao, "Colunas obrigatórias": ", ".join(colunas)}
                                   for nome, (colunas, _, _, descricao) in BASES.items()]),
                     hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        c1.download_button("Baixar modelo: transporte_raca_uf.csv", dados["ak"]["uf"].to_csv(index=False).encode("utf-8"),
                           "transporte_raca_uf.csv", "text/csv")
        c2.download_button("Baixar modelo: renda_municipio.csv",
                           dados["ing"]["renda_municipio"].to_csv(index=False).encode("utf-8"),
                           "renda_municipio.csv", "text/csv")

    if not enviados:
        st.write("Nenhum arquivo enviado: o painel está usando as bases originais do grupo.")
        return

    for i, registro in enumerate(enviados):
        st.header(registro["nome"])
        if registro["erro"]:
            st.error(f"Não foi possível ler este arquivo ({registro['erro']}). O painel continua com a base original.")
            continue
        df = registro["df"]
        if registro["base"]:
            st.success(f"Reconhecido como **{registro['base']}** ({BASES[registro['base']][3]}). "
                       "Esta base está substituindo a original em todas as páginas.")
        else:
            st.info("Não tem as colunas de nenhuma base do projeto, então não altera as outras páginas. "
                    "Você pode explorar os dados abaixo.")
        st.write(f"**{num(len(df))} linhas e {len(df.columns)} colunas.** Primeiras linhas:")
        st.dataframe(df.head(20), hide_index=True, width="stretch")

        numericas = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().sum() >= 5
                     and str(c).lower() not in ("ano", "cod_ibge")]
        if not numericas:
            st.write("O arquivo não tem coluna numérica com pelo menos 5 valores para calcular as estatísticas.")
            continue
        coluna = st.selectbox("Coluna numérica para analisar", numericas, key=f"coluna_{i}")
        valores = pd.to_numeric(df[coluna], errors="coerce").dropna()
        r = e_ac.resumo_descritivo(valores)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Medidas estatísticas**")
            medidas = [("Nº de valores", num(r["n"])), ("Média", num(r["media"], 2)), ("Mediana", num(r["mediana"], 2)),
                       ("Moda", num(r["moda"], 2)), ("Q1", num(r["q1"], 2)), ("Q3", num(r["q3"], 2)),
                       ("IQR", num(r["iqr"], 2)), ("Mínimo", num(r["minimo"], 2)), ("Máximo", num(r["maximo"], 2)),
                       ("Amplitude", num(r["amplitude"], 2)), ("Variância", num(r["variancia"], 2)),
                       ("Desvio padrão", num(r["desvio_padrao"], 2)),
                       ("Limite inferior de outlier", num(r["limite_inferior"], 2)),
                       ("Limite superior de outlier", num(r["limite_superior"], 2)), ("Outliers", num(r["qtd_outliers"]))]
            st.dataframe(pd.DataFrame(medidas, columns=["Medida", "Valor"]), hide_index=True, width="stretch")
        with col2:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.histplot(
                x=valores,
                kde=True,
                bins=20,
                color="#4c72b0",
                ax=ax,
            )
            ax.axvline(r["media"], color="red", linestyle="--", linewidth=2, label="Média")
            ax.axvline(r["mediana"], color="#2b5c8f", linestyle="-", linewidth=2, label="Mediana")
            ax.set_title(f"Distribuição de {coluna}", fontsize=14, fontweight="bold")
            ax.set_xlabel(coluna, fontsize=11)
            ax.set_ylabel("Frequência", fontsize=11)
            ax.legend(frameon=True)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        with col3:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.boxplot(
                y=valores,
                color=sns.color_palette("Set2")[0],
                ax=ax
            )
            ax.set_title(f"Boxplot de {coluna}", fontsize=14, fontweight="bold")
            ax.set_ylabel(coluna, fontsize=11)
            ax.grid(True, axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        texto = (f"**Análise:** A média de {coluna} é {num(r['media'], 2)} e a mediana {num(r['mediana'], 2)}; "
                 f"o IQR é {num(r['iqr'], 2)} e o desvio padrão {num(r['desvio_padrao'], 2)}. "
                 f"Pela regra de 1,5 × IQR há {num(r['qtd_outliers'])} outliers. ")
        if np.isclose(r["media"], r["mediana"]):
            texto += "Média e mediana são praticamente iguais (distribuição simétrica)."
        elif r["media"] > r["mediana"]:
            texto += "A média é maior que a mediana: valores muito altos a puxam para cima (assimetria à direita)."
        else:
            texto += "A média é menor que a mediana: valores muito baixos a puxam para baixo (assimetria à esquerda)."
        st.write(texto)


# ================= APP =================
pagina, filtros, arquivos = barra_lateral()
dados, enviados = carregar_tudo(arquivos)
substituidas = [x["base"] for x in enviados if x["base"]]
if substituidas and pagina != "Upload de dados":
    st.info("Usando dados enviados por upload no lugar de: " + ", ".join(substituidas) + ".")

try:
    if pagina == "Início":
        pagina_inicio(dados, filtros)
    elif pagina == "1. Transporte por raça":
        p_ak.render(dados["ak"], filtros)
    elif pagina == "2. Tempo de deslocamento":
        p_alv.render(dados["alv"], filtros)
    elif pagina == "3. Mobilidade ativa":
        st.caption("Nesta página o filtro de meio de transporte não se aplica: o % de bicicleta precisa de todos os "
                   "meios no denominador.")
        p_ac.render(dados["ac"], filtros)
    elif pagina == "4. Renda e mobilidade":
        st.caption("Nesta página o filtro de categoria de renda vale para a parte A (tempo × renda); o de meio de "
                   "transporte não se aplica.")
        p_ing.render(dados["ing"], filtros)
    elif pagina == "Notícias e imagens":
        pagina_noticias()
    else:
        pagina_upload(dados, enviados)
except Exception as erro:
    if not substituidas:
        raise
    st.error("Não foi possível montar esta página com a base enviada por upload: ela parece ter categorias ou valores "
             f"diferentes do esperado ({erro}). Remova o arquivo na barra lateral para voltar à base original.")
