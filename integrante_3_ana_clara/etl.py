"""
ETL — ANA CLARA — MOBILIDADE ATIVA E USO DE BICICLETAS
======================================================

Rodar a partir da PASTA DO PROJETO:
    python -m integrante_3_ana_clara.etl

O que este arquivo faz:
 1. EXTRAIR   : baixa a tabela 10330 do Censo 2022 no nível MUNICÍPIO (API do SIDRA/IBGE)
                e a malha (contorno) das UFs, para o mapa (API de malhas do IBGE).
 2. TRANSFORMAR:
      - "-" vira 0 (zero no IBGE); "X", "..", "..." viram vazio (NaN), nunca zero;
      - padroniza município, UF, região, meio de transporte e raça;
      - remove duplicadas; cria grupo_modal.
 3. CARREGAR  : salva em dados/.

Bases geradas:
    dados/transporte_municipio.csv.gz -> 5.570 municípios: pessoas por meio de transporte × raça
    dados/mapa_uf.geojson             -> contorno das 27 UFs (malha oficial do IBGE)
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
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
             "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF")

# ---------------- CONSTANTES (códigos e nomes padronizados) ----------------
UF_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
REGIAO_POR_DIGITO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
REGIOES = list(REGIAO_POR_DIGITO.values())
RACAS = ["Branca", "Preta", "Parda", "Amarela", "Indígena"]
MEIO_IBGE_PARA_PADRAO = {
    "A pé": "A pé", "Bicicleta": "Bicicleta", "Motocicleta": "Motocicleta", "Mototáxi": "Mototáxi",
    "Automóvel": "Automóvel", "Táxi ou assemelhados": "Táxi", "Van, perua ou assemelhados": "Van",
    "Ônibus": "Ônibus", "BRT ou ônibus de trânsito rápido": "BRT", "Trem ou metrô": "Trem ou metrô",
    "Caminhonete ou caminhão adaptado (pau de arara)": "Pau de arara",
    "Embarcação de médio e grande porte (acima de 20 pessoas)": "Embarcação grande",
    "Embarcação de pequeno porte (até 20 pessoas)": "Embarcação pequena",
    "Outros": "Outros meios",
}
MEIOS = list(MEIO_IBGE_PARA_PADRAO.values())
GRUPO_MODAL = {
    "Ônibus": "Público", "BRT": "Público", "Trem ou metrô": "Público",
    "Automóvel": "Particular", "Motocicleta": "Particular",
    "A pé": "Ativo", "Bicicleta": "Ativo",
    "Mototáxi": "Outros", "Táxi": "Outros", "Van": "Outros", "Pau de arara": "Outros",
    "Embarcação grande": "Outros", "Embarcação pequena": "Outros", "Outros meios": "Outros",
}
SIDRA_MEIO = "Meio de transporte em que passa mais tempo para chegar ao local de trabalho"
VALORES_ESPECIAIS = {"-": 0.0, "X": np.nan, "..": np.nan, "...": np.nan}

# capitais das personas (código IBGE -> cidade e gestor)
MUNICIPIOS_PERSONAS = {
    "5208707": "Goiânia (Ana)",
    "3205309": "Vitória (Luciene)",
    "3106200": "Belo Horizonte (Pedrinho)",
    "5300108": "Brasília (Lucas)",
}


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


def baixar_municipios() -> pd.DataFrame:
    """Municípios: meio × raça (tempo = Total). Limite da API: 50 mil valores por consulta,
    então baixamos uma UF e uma raça de cada vez."""
    partes = []
    for cod_uf, sigla in UF_SIGLA.items():
        for raca in ["2776", "2777", "2778", "2779", "2780"]:
            partes.append(consultar_sidra(f"t/10330/n6/in%20n3%20{cod_uf}/v/13376/p/2022/c537/31609/"
                                          f"c2088/allxt/c469/79176/c86/{raca}"))
            time.sleep(0.2)
        print(f"   {sigla} ok")
    return pd.concat(partes, ignore_index=True)


def baixar_mapa() -> None:
    resposta = requests.get(URL_MALHA, timeout=120)
    resposta.raise_for_status()
    (PASTA_DADOS / "mapa_uf.geojson").write_text(resposta.text, encoding="utf-8")


# ================= 2. TRANSFORMAR =================

def converter_valor(serie: pd.Series) -> pd.Series:
    texto = serie.astype(str).str.strip()
    especial = texto.map(VALORES_ESPECIAIS)
    return especial.where(texto.isin(VALORES_ESPECIAIS.keys()), pd.to_numeric(texto, errors="coerce"))


def tratar(raw: pd.DataFrame) -> pd.DataFrame:
    print(f"\nlinhas brutas: {len(raw):,} | '-' (zero): {(raw['Valor'] == '-').sum():,} | "
          f"'X', '..', '...': {raw['Valor'].isin(['X', '..', '...']).sum():,}")
    desconhecidos = set(raw[SIDRA_MEIO].unique()) - set(MEIO_IBGE_PARA_PADRAO)
    if desconhecidos:
        raise ValueError(f"Meio de transporte inesperado: {desconhecidos}")

    df = pd.DataFrame({
        "ano": pd.to_numeric(raw["Ano"]).astype(int),
        "nivel": "Município",
        "cod_ibge": raw["Município (Código)"].astype(str),
        "local": raw["Município"].str.replace(r" - [A-Z]{2}$", "", regex=True),
    })
    df["uf"] = df["cod_ibge"].str[:2].map(UF_SIGLA)
    df["regiao"] = df["cod_ibge"].str[0].map(REGIAO_POR_DIGITO)
    df["meio"] = raw[SIDRA_MEIO].map(MEIO_IBGE_PARA_PADRAO)
    df["grupo_modal"] = df["meio"].map(GRUPO_MODAL)
    df["raca"] = raw["Cor ou raça"]
    df["pessoas"] = converter_valor(raw["Valor"])
    df["fonte_tabela"] = "SIDRA 10330"

    duplicadas = df.duplicated(subset=["cod_ibge", "meio", "raca"]).sum()
    df = df.drop_duplicates(subset=["cod_ibge", "meio", "raca"])
    print(f"duplicadas removidas: {duplicadas} | vazios (NaN): {df['pessoas'].isna().sum()} | "
          f"municípios: {df['cod_ibge'].nunique():,} | linhas finais: {len(df):,}")
    return df.reset_index(drop=True)


# ================= 3. CARREGAR =================

def main() -> None:
    PASTA_DADOS.mkdir(exist_ok=True)
    print("Baixando municípios (SIDRA 10330) — leva alguns minutos...")
    tratar(baixar_municipios()).to_csv(PASTA_DADOS / "transporte_municipio.csv.gz", index=False)
    print("Baixando a malha das UFs (mapa)...")
    baixar_mapa()
    print("\nPronto! Bases salvas em", PASTA_DADOS)


if __name__ == "__main__":
    main()
