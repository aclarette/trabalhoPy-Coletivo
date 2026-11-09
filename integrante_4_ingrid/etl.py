"""
ETL — INGRID — RENDA E DESIGUALDADE NA MOBILIDADE
=================================================

Rodar a partir da PASTA DO PROJETO:
    python -m integrante_4_ingrid.etl

ATENÇÃO: o Censo 2022 NÃO tem uma tabela que cruze meio de transporte × renda das pessoas.
Por isso baixamos 4 tabelas, cada uma para uma parte da análise:

    Tabela 10331 -> tempo de deslocamento × raça × RENDA (pessoas)        -> parte A
    Tabela 10295 -> renda per capita MÉDIA e MEDIANA de cada município    -> parte B
    Tabela 10330 -> meio de transporte de cada município                  -> parte B
    Tabela 10332 -> meio de transporte × NÍVEL DE INSTRUÇÃO × raça         -> parte C

As tabelas têm universos diferentes: NUNCA somamos linhas de uma com a outra.

Transformações: "-" vira 0 (zero no IBGE); "X", "..", "..." viram vazio (NaN), nunca zero;
padronização de território e categorias; conferência com os Totais; remoção de Totais e duplicadas.

Bases geradas em dados/:
    tempo_renda_raca_uf.csv, renda_municipio.csv, meio_municipio.csv.gz, instrucao_meio_raca_uf.csv
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import truststore

truststore.inject_into_ssl()

PASTA = Path(__file__).resolve().parent
PASTA_DADOS = PASTA / "dados"
URL_SIDRA = "https://apisidra.ibge.gov.br/values"

# ---------------- CONSTANTES (códigos e nomes padronizados) ----------------
UF_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
REGIAO_POR_DIGITO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
REGIOES = list(REGIAO_POR_DIGITO.values())
NIVEL_SIDRA = {"Brasil": "Brasil", "Grande Região": "Região",
               "Unidade da Federação": "UF", "Município": "Município"}
RACAS = ["Branca", "Preta", "Parda", "Amarela", "Indígena"]

TEMPO_IBGE_PARA_PADRAO = {
    "Até cinco minutos": "Até 5 min",
    "De seis minutos até quinze minutos": "6 a 15 min",
    "Mais de quinze minutos até meia hora": "15 a 30 min",
    "Mais de meia hora até uma hora": "30 min a 1 h",
    "Mais de uma hora até duas horas": "1 a 2 h",
    "Mais de duas horas até quatro horas": "2 a 4 h",
    "Mais de quatro horas": "Mais de 4 h",
}
TEMPO_FAIXAS = list(TEMPO_IBGE_PARA_PADRAO.values())
RENDA_IBGE_PARA_PADRAO = {
    "Sem rendimento": "Sem rendimento",
    "Até 1/4 de salário mínimo": "Até 1/4 SM",
    "Mais de 1/4 a 1/2 salário mínimo": "1/4 a 1/2 SM",
    "Mais de 1/2 a 1 salário mínimo": "1/2 a 1 SM",
    "Mais de 1 a 2 salários mínimos": "1 a 2 SM",
    "Mais de 2 a 3 salários mínimos": "2 a 3 SM",
    "Mais de 3 a 5 salários mínimos": "3 a 5 SM",
    "Mais de 5 salários mínimos": "Mais de 5 SM",
}
RENDA_FAIXAS = list(RENDA_IBGE_PARA_PADRAO.values())
INSTRUCAO_IBGE_PARA_PADRAO = {
    "Sem instrução e fundamental incompleto": "Sem instrução / fund. incompleto",
    "Fundamental completo e médio incompleto": "Fund. completo / médio incompleto",
    "Médio completo e superior incompleto": "Médio completo / sup. incompleto",
    "Superior completo": "Superior completo",
}
INSTRUCAO_NIVEIS = list(INSTRUCAO_IBGE_PARA_PADRAO.values())
MEIO_IBGE_PARA_PADRAO = {
    "A pé": "A pé", "Bicicleta": "Bicicleta", "Motocicleta": "Motocicleta", "Mototáxi": "Mototáxi",
    "Automóvel": "Automóvel", "Táxi ou assemelhados": "Táxi", "Van, perua ou assemelhados": "Van",
    "Ônibus": "Ônibus", "BRT ou ônibus de trânsito rápido": "BRT", "Trem ou metrô": "Trem ou metrô",
    "Caminhonete ou caminhão adaptado (pau de arara)": "Pau de arara",
    "Embarcação de médio e grande porte (acima de 20 pessoas)": "Embarcação grande",
    "Embarcação de pequeno porte (até 20 pessoas)": "Embarcação pequena",
    "Outros": "Outros meios",
}
GRUPO_MODAL = {
    "Ônibus": "Público", "BRT": "Público", "Trem ou metrô": "Público",
    "Automóvel": "Particular", "Motocicleta": "Particular",
    "A pé": "Ativo", "Bicicleta": "Ativo",
    "Mototáxi": "Outros", "Táxi": "Outros", "Van": "Outros", "Pau de arara": "Outros",
    "Embarcação grande": "Outros", "Embarcação pequena": "Outros", "Outros meios": "Outros",
}
GRUPOS_MODAIS = ["Público", "Particular", "Ativo", "Outros"]


DIMENSOES = {
    "Tempo habitual de deslocamento do domicílio para o trabalho principal": ("tempo_faixa", TEMPO_IBGE_PARA_PADRAO),
    "Cor ou raça": ("raca", {r: r for r in RACAS}),
    "Classes de rendimento nominal mensal domiciliar per capita": ("renda_faixa", RENDA_IBGE_PARA_PADRAO),
    "Nível de instrução": ("instrucao", INSTRUCAO_IBGE_PARA_PADRAO),
    "Meio de transporte em que passa mais tempo para chegar ao local de trabalho": ("meio", MEIO_IBGE_PARA_PADRAO),
}
VALORES_ESPECIAIS = {"-": 0.0, "X": np.nan, "..": np.nan, "...": np.nan}


# ================= 1. EXTRAIR =================

def consultar_sidra(caminho: str) -> pd.DataFrame:
    """Uma consulta à API do SIDRA (a 1ª linha do JSON é o cabeçalho)."""
    for tentativa in range(3):
        try:
            resposta = requests.get(f"{URL_SIDRA}/{caminho}", timeout=120)
            resposta.raise_for_status()
            if not resposta.text.startswith("["):
                raise ValueError(resposta.text[:200])
            linhas = resposta.json()
            return pd.DataFrame(linhas[1:]).rename(columns=linhas[0])
        except (requests.RequestException, ValueError) as erro:
            print(f"   tentativa {tentativa + 1} falhou: {erro}")
            time.sleep(3)
    raise RuntimeError(f"Não foi possível baixar: {caminho}")


def baixar_niveis(tabela: str, resto: str) -> pd.DataFrame:
    """Brasil (n1), regiões (n2) e UFs (n3)."""
    return pd.concat([consultar_sidra(f"t/{tabela}/{n}/all/{resto}") for n in ("n1", "n2", "n3")], ignore_index=True)


def baixar_por_uf(tabela: str, resto: str) -> pd.DataFrame:
    """Todos os municípios, uma UF por vez (limite de 50 mil valores por consulta)."""
    partes = []
    for cod_uf in UF_SIGLA:
        partes.append(consultar_sidra(f"t/{tabela}/n6/in%20n3%20{cod_uf}/{resto}"))
        time.sleep(0.2)
    return pd.concat(partes, ignore_index=True)


# ================= 2. TRANSFORMAR =================

def converter_valor(serie: pd.Series) -> pd.Series:
    texto = serie.astype(str).str.strip()
    especial = texto.map(VALORES_ESPECIAIS)
    return especial.where(texto.isin(VALORES_ESPECIAIS.keys()), pd.to_numeric(texto, errors="coerce"))


def padronizar_territorio(raw: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(index=raw.index)
    df["ano"] = pd.to_numeric(raw["Ano"]).astype(int)
    df["nivel"] = raw["Nível Territorial"].map(NIVEL_SIDRA)
    codigo = pd.Series(pd.NA, index=raw.index, dtype="object")
    nome = pd.Series(pd.NA, index=raw.index, dtype="object")
    for nivel in NIVEL_SIDRA:
        if f"{nivel} (Código)" in raw.columns:
            codigo = codigo.fillna(raw[f"{nivel} (Código)"])
            nome = nome.fillna(raw[nivel])
    df["cod_ibge"] = codigo.astype(str)
    df["local"] = nome.astype(str).str.replace(r" - [A-Z]{2}$", "", regex=True)
    uf_ou_mun = df["nivel"].isin(["UF", "Município"])
    df["uf"] = np.where(uf_ou_mun, df["cod_ibge"].str[:2].map(UF_SIGLA), None)
    df["regiao"] = np.where(uf_ou_mun, df["cod_ibge"].str[0].map(REGIAO_POR_DIGITO), None)
    df.loc[df["nivel"] == "Região", "regiao"] = df["local"]
    return df


def tratar_contagem(raw: pd.DataFrame, fonte: str, nome_base: str) -> pd.DataFrame:
    """Tabelas de contagem de pessoas: padroniza as dimensões que existirem na tabela."""
    print(f"\n[{nome_base}] linhas brutas: {len(raw):,} | '-' (zero): {(raw['Valor'] == '-').sum():,} | "
          f"'X', '..', '...': {raw['Valor'].isin(['X', '..', '...']).sum():,}")
    df = padronizar_territorio(raw)
    dims = []
    for coluna_sidra, (coluna, dicionario) in DIMENSOES.items():
        if coluna_sidra in raw.columns and raw[coluna_sidra].nunique() > 1:
            desconhecidas = set(raw[coluna_sidra].unique()) - set(dicionario) - {"Total"}
            if desconhecidas:
                raise ValueError(f"Categoria inesperada em {coluna}: {desconhecidas}")
            df[coluna] = raw[coluna_sidra].map(lambda v, d=dicionario: "Total" if v == "Total" else d[v])
            dims.append(coluna)
    df["pessoas"] = converter_valor(raw["Valor"])

    for dim in dims:
        outras = [d for d in dims if d != dim]
        base = df[(df["nivel"] == "Brasil") & df[outras].eq("Total").all(axis=1)]
        if (base[dim] == "Total").any():
            total = base.loc[base[dim] == "Total", "pessoas"].sum()
            soma = base.loc[base[dim] != "Total", "pessoas"].sum()
            print(f"   conferência {dim}: soma {100 * soma / total:.2f}% do Total do IBGE")

    df = df[~df[dims].eq("Total").any(axis=1)].copy()
    chave = ["nivel", "cod_ibge"] + dims
    duplicadas = df.duplicated(subset=chave).sum()
    df = df.drop_duplicates(subset=chave)
    if "meio" in df:
        df["grupo_modal"] = df["meio"].map(GRUPO_MODAL)
    df["fonte_tabela"] = fonte
    print(f"   duplicadas removidas: {duplicadas} | vazios (NaN): {df['pessoas'].isna().sum()} | linhas finais: {len(df):,}")
    return df.reset_index(drop=True)


def tratar_renda(raw: pd.DataFrame) -> pd.DataFrame:
    """Tabela 10295: duas variáveis em R$ (média e mediana) -> uma coluna para cada."""
    df = padronizar_territorio(raw)
    df["variavel"] = np.where(raw["Variável"].str.contains("mediano"), "renda_mediana_pc", "renda_media_pc")
    df["valor"] = converter_valor(raw["Valor"])
    largo = (df.pivot_table(index=["ano", "nivel", "cod_ibge", "local", "uf", "regiao"], columns="variavel",
                            values="valor", aggfunc="first").reset_index())
    largo.columns.name = None
    largo["fonte_tabela"] = "SIDRA 10295"
    print(f"\n[renda municipal] municípios: {len(largo):,} | sem renda mediana: {largo['renda_mediana_pc'].isna().sum()}")
    return largo


# ================= 3. CARREGAR =================

def main() -> None:
    PASTA_DADOS.mkdir(exist_ok=True)
    print("Tabela 10331: tempo × raça × renda (Brasil, regiões, UFs)...")
    tratar_contagem(baixar_niveis("10331", "v/13556/p/2022/c537/all/c2/6794/c86/all/c386/all"),
                    "SIDRA 10331", "tempo × renda").to_csv(PASTA_DADOS / "tempo_renda_raca_uf.csv", index=False)

    print("Tabela 10332: meio × instrução × raça (Brasil, regiões, UFs)...")
    tratar_contagem(baixar_niveis("10332", "v/13377/p/2022/c2088/all/c1568/all/c86/all"),
                    "SIDRA 10332", "instrução × meio").to_csv(PASTA_DADOS / "instrucao_meio_raca_uf.csv", index=False)

    print("Tabela 10295: renda per capita média e mediana (municípios)...")
    tratar_renda(baixar_por_uf("10295", "v/13431,13534/p/2022/c2/6794/c86/95251/c58/95253")
                 ).to_csv(PASTA_DADOS / "renda_municipio.csv", index=False)

    print("Tabela 10330: meio de transporte (municípios)...")
    tratar_contagem(baixar_por_uf("10330", "v/13376/p/2022/c537/31609/c2088/allxt/c86/95251/c469/79176"),
                    "SIDRA 10330", "meio por município").to_csv(PASTA_DADOS / "meio_municipio.csv.gz", index=False)
    print("\nPronto! Bases salvas em", PASTA_DADOS)


if __name__ == "__main__":
    main()
