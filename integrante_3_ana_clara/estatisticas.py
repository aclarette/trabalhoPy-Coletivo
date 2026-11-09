"""
ESTATÍSTICAS — ANA CLARA — MOBILIDADE ATIVA E BICICLETAS
========================================================

A variável principal é NUMÉRICA e existe para cada município:
    % de trabalhadores cujo meio PRINCIPAL é a bicicleta
        numerador   = trabalhadores que vão principalmente de bicicleta
        denominador = todos os trabalhadores do município (entre quem declarou o meio)

Como cada município é uma observação, calculamos média, mediana, moda, quartis,
IQR, amplitude, variância, desvio padrão e outliers (regra 1,5 × IQR).
"""

import numpy as np
import pandas as pd


def tabela_municipal(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por município: total de trabalhadores, ciclistas, pedestres e percentuais."""
    t = df.pivot_table(index=["cod_ibge", "local", "uf", "regiao"], columns="meio", values="pessoas",
                       aggfunc="sum", fill_value=0)
    r = pd.DataFrame(index=t.index)
    r["total"] = t.sum(axis=1)
    r["bicicleta"] = t.get("Bicicleta", 0)
    r["a_pe"] = t.get("A pé", 0)
    r["ativo"] = r["bicicleta"] + r["a_pe"]
    for coluna in ["bicicleta", "a_pe", "ativo"]:
        r[f"pct_{coluna}"] = 100 * r[coluna] / r["total"].where(r["total"] > 0)
    return r.reset_index()


def percentuais_do_territorio(tabela: pd.DataFrame) -> dict:
    """% do território inteiro: soma os ciclistas de todos os municípios ÷ soma dos trabalhadores.
    (Não é a média dos percentuais! Cada pessoa conta igual, não cada município.)"""
    total = tabela["total"].sum()
    return {chave: 100 * tabela[chave].sum() / total if total else np.nan for chave in ["bicicleta", "a_pe", "ativo"]}


def limites_outlier(q1: float, q3: float) -> tuple[float, float]:
    """Regra do 1,5 × IQR: inferior = Q1 − 1,5·IQR; superior = Q3 + 1,5·IQR."""
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def resumo_descritivo(valores: pd.Series) -> dict:
    """Todas as medidas pedidas no projeto. NaN é ignorado (nunca vira zero).
    Variância POPULACIONAL (divide por n): usamos todos os municípios, não uma amostra."""
    v = pd.to_numeric(valores, errors="coerce").dropna()
    if v.empty:
        return {"n": 0}
    q1, q2, q3 = v.quantile([0.25, 0.5, 0.75]).tolist()
    inferior, superior = limites_outlier(q1, q3)
    return {
        "n": len(v), "media": v.mean(), "mediana": q2, "moda": v.round(1).mode().iloc[0],
        "q1": q1, "q2": q2, "q3": q3, "iqr": q3 - q1,
        "minimo": v.min(), "maximo": v.max(), "amplitude": v.max() - v.min(),
        "variancia": v.var(ddof=0), "desvio_padrao": v.std(ddof=0),
        "limite_inferior": inferior, "limite_superior": superior,
        "qtd_outliers": int(((v < inferior) | (v > superior)).sum()),
    }


def marcar_outliers(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    r = df.copy()
    inferior, superior = limites_outlier(r[coluna].quantile(0.25), r[coluna].quantile(0.75))
    r["outlier"] = np.select([r[coluna] < inferior, r[coluna] > superior], ["Abaixo", "Acima"], "Normal")
    return r


def posicao_no_ranking(tabela: pd.DataFrame, cod_ibge: str, minimo: int) -> tuple[int | None, int]:
    """Posição de um município no ranking de % de bicicleta (1º = maior)."""
    ranking = tabela[tabela["total"] >= minimo].sort_values("pct_bicicleta", ascending=False).reset_index(drop=True)
    achou = ranking.index[ranking["cod_ibge"] == cod_ibge]
    return (int(achou[0]) + 1 if len(achou) else None), len(ranking)
