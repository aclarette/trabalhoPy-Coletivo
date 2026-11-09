"""
ESTATÍSTICAS — INGRID — RENDA E DESIGUALDADE NA MOBILIDADE
==========================================================

Três tipos de cálculo:

A) TEMPO × RENDA (dados agrupados): o IBGE dá a FAIXA de tempo, não os minutos.
   -> mediana estimada:  Mediana ≈ Li + ((n/2 − Fant) / fi) × h

B) RENDA DO MUNICÍPIO × MODAL (uma observação por município):
   -> média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão, outliers
   -> correlação de Pearson (r) entre renda e % de cada modal

C) INSTRUÇÃO × MODAL (categórico): percentuais.
"""

import numpy as np
import pandas as pd

LIMITES = {
    "Até 5 min": (0, 5), "6 a 15 min": (5, 15), "15 a 30 min": (15, 30), "30 min a 1 h": (30, 60),
    "1 a 2 h": (60, 120), "2 a 4 h": (120, 240), "Mais de 4 h": (240, None),
}
FAIXAS_MAIS_1H = ["1 a 2 h", "2 a 4 h", "Mais de 4 h"]
FAIXAS_MAIS_2H = ["2 a 4 h", "Mais de 4 h"]


def mediana_agrupada(f: pd.Series) -> float:
    """Mediana estimada por interpolação dentro da classe mediana."""
    f = f.reindex(list(LIMITES)).fillna(0)
    n = f.sum()
    if n <= 0:
        return np.nan
    acumulado = 0.0
    for classe, fi in f.items():
        if fi > 0 and acumulado + fi >= n / 2:
            li, ls = LIMITES[classe]
            return np.nan if ls is None else li + (n / 2 - acumulado) / fi * (ls - li)
        acumulado += fi
    return np.nan


def tempo_por_renda(df: pd.DataFrame, faixas_renda: list[str]) -> pd.DataFrame:
    """Para cada faixa de renda: pessoas, mediana estimada, % > 1 h e % > 2 h."""
    linhas = []
    for faixa in [r for r in faixas_renda if r in df["renda_faixa"].unique()]:
        f = df[df["renda_faixa"] == faixa].groupby("tempo_faixa")["pessoas"].sum().reindex(list(LIMITES)).fillna(0)
        n = f.sum()
        if n > 0:
            linhas.append({"renda_faixa": faixa, "pessoas": n, "mediana": mediana_agrupada(f),
                           "pct_mais_1h": 100 * f[FAIXAS_MAIS_1H].sum() / n,
                           "pct_mais_2h": 100 * f[FAIXAS_MAIS_2H].sum() / n})
    return pd.DataFrame(linhas)


def modal_por_municipio(df_meio: pd.DataFrame, renda: pd.DataFrame, minimo: int) -> pd.DataFrame:
    """Uma linha por município: % público, % particular e renda per capita mediana (R$)."""
    t = df_meio.pivot_table(index=["cod_ibge", "local", "uf", "regiao"], columns="grupo_modal",
                            values="pessoas", aggfunc="sum", fill_value=0)
    r = pd.DataFrame(index=t.index)
    r["total"] = t.sum(axis=1)
    r["pct_publico"] = 100 * t.get("Público", 0) / r["total"].where(r["total"] > 0)
    r["pct_particular"] = 100 * t.get("Particular", 0) / r["total"].where(r["total"] > 0)
    r = r.reset_index()
    r = r[r["total"] >= minimo]
    return r.merge(renda[["cod_ibge", "renda_mediana_pc", "renda_media_pc"]], on="cod_ibge", how="left")


def correlacao(x: pd.Series, y: pd.Series) -> float:
    """Correlação de Pearson (r), de −1 a +1. Mede relação LINEAR; correlação não prova causa."""
    d = pd.concat([x, y], axis=1).dropna()
    return float(np.corrcoef(d.iloc[:, 0], d.iloc[:, 1])[0, 1]) if len(d) >= 3 else np.nan


def forca_correlacao(r: float) -> str:
    if r is None or np.isnan(r):
        return "indefinida"
    a = abs(r)
    forca = "muito fraca" if a < 0.2 else "fraca" if a < 0.4 else "moderada" if a < 0.6 else "forte"
    return f"{forca} e {'positiva' if r > 0 else 'negativa'}"


def limites_outlier(q1: float, q3: float) -> tuple[float, float]:
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def resumo_descritivo(valores: pd.Series) -> dict:
    """Média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão e outliers.
    NaN é ignorado (nunca vira zero). Variância populacional (todos os municípios)."""
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


def participacao(df: pd.DataFrame, categoria: str, por: list[str]) -> pd.DataFrame:
    """Percentual de cada categoria dentro de cada grupo (soma 100% por grupo)."""
    soma = df.groupby(por + [categoria], as_index=False)["pessoas"].sum()
    soma["percentual"] = 100 * soma["pessoas"] / soma.groupby(por)["pessoas"].transform("sum")
    return soma
