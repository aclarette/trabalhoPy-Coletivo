"""
ESTATÍSTICAS — ANA KAROLINA — MEIOS DE TRANSPORTE POR RAÇA
==========================================================

Dois tipos de variável aparecem nesta análise:

1) CATEGÓRICA: o meio de transporte e a raça.
   -> Só fazem sentido MODA e PERCENTUAIS. Não existe "média de ônibus".
   -> funções: participacao(), moda_categorica()

2) NUMÉRICA: o % de trabalhadores que usa transporte público em CADA município.
   -> Cada município é uma observação com um número real.
   -> Aqui calculamos média, mediana, moda, quartis, IQR, amplitude,
      variância, desvio padrão e outliers.
   -> funções: percentual_por_municipio(), resumo_descritivo(), marcar_outliers()
"""

import numpy as np
import pandas as pd


def participacao(df: pd.DataFrame, categoria: str, por: list[str] | None = None) -> pd.DataFrame:
    """Soma as pessoas por categoria e calcula o PERCENTUAL dentro de cada grupo.

    Exemplo: participacao(df, "grupo_modal", por=["raca"])
      -> para cada raça, o % de pessoas em Público, Particular, Ativo e Outros (somam 100%).
    """
    por = por or []
    soma = df.groupby(por + [categoria], as_index=False)["pessoas"].sum()
    total = soma.groupby(por)["pessoas"].transform("sum") if por else soma["pessoas"].sum()
    soma["percentual"] = 100 * soma["pessoas"] / total
    return soma


def moda_categorica(df: pd.DataFrame, categoria: str) -> str | None:
    """Categoria com MAIS PESSOAS (a moda). Soma a coluna 'pessoas' — NÃO conta linhas,
    porque cada linha da tabela representa milhares de pessoas."""
    soma = df.groupby(categoria)["pessoas"].sum()
    return soma.idxmax() if soma.sum() > 0 else None


def percentual_por_municipio(df: pd.DataFrame, coluna: str, categorias: list[str],
                             minimo: float = 0) -> pd.DataFrame:
    """% de pessoas de cada município cuja `coluna` está em `categorias`.

    numerador = pessoas nas categorias; denominador = todas as pessoas do município.
    minimo: municípios com menos trabalhadores que isso ficam de fora (percentuais de
    populações pequenas oscilam muito e têm erro amostral maior).
    """
    chave = ["cod_ibge", "local", "uf", "regiao"]
    total = df.groupby(chave)["pessoas"].sum().rename("total")
    parte = df[df[coluna].isin(categorias)].groupby(chave)["pessoas"].sum().rename("quantidade")
    r = pd.concat([total, parte], axis=1).reset_index()
    r["quantidade"] = r["quantidade"].fillna(0)
    r["percentual"] = np.where(r["total"] > 0, 100 * r["quantidade"] / r["total"], np.nan)
    return r[r["total"] >= minimo].reset_index(drop=True)


def limites_outlier(q1: float, q3: float) -> tuple[float, float]:
    """Regra do 1,5 × IQR: inferior = Q1 − 1,5·IQR; superior = Q3 + 1,5·IQR."""
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def resumo_descritivo(valores: pd.Series) -> dict:
    """Todas as medidas pedidas no projeto para uma variável numérica.

    - Valores vazios (NaN) são ignorados, nunca trocados por zero.
    - Variância POPULACIONAL (divide por n): temos todos os municípios, não uma amostra.
    - Quartis pelo método padrão do Pandas (interpolação linear).
    """
    v = pd.to_numeric(valores, errors="coerce").dropna()
    if v.empty:
        return {"n": 0}
    q1, q2, q3 = v.quantile([0.25, 0.5, 0.75]).tolist()
    inferior, superior = limites_outlier(q1, q3)
    return {
        "n": len(v),
        "media": v.mean(),
        "mediana": q2,
        "moda": v.round(1).mode().iloc[0],
        "q1": q1, "q2": q2, "q3": q3,
        "iqr": q3 - q1,
        "minimo": v.min(), "maximo": v.max(),
        "amplitude": v.max() - v.min(),
        "variancia": v.var(ddof=0),
        "desvio_padrao": v.std(ddof=0),
        "limite_inferior": inferior,
        "limite_superior": superior,
        "qtd_outliers": int(((v < inferior) | (v > superior)).sum()),
    }


def marcar_outliers(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Cópia do df com a coluna 'outlier' = 'Acima', 'Abaixo' ou 'Normal'."""
    r = df.copy()
    q1, q3 = r[coluna].quantile(0.25), r[coluna].quantile(0.75)
    inferior, superior = limites_outlier(q1, q3)
    r["outlier"] = np.select([r[coluna] < inferior, r[coluna] > superior], ["Abaixo", "Acima"], "Normal")
    return r
