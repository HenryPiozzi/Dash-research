"""
Gera agregado_outliers_uf_2022.csv — salva em data/analytics/.
Execute na raiz do projeto antes de subir o dashboard.
"""

from pathlib import Path
import pandas as pd

PASTA = Path(__file__).resolve().parents[1] / "data" / "analytics"


def _ler(nome):
    return pd.read_csv(PASTA / nome, sep=";", encoding="utf-8")


df = _ler("enem_2022_ibge_transformado.csv")

resumo = (
    df.groupby("SG_UF_PROVA")
    .agg(
        MEDIA_GERAL_MEDIA =("MEDIA_GERAL",      "mean"),
        MEDIA_GERAL_MAX   =("MEDIA_GERAL",      "max"),
        MEDIA_GERAL_P95   =("MEDIA_GERAL",      lambda x: x.quantile(0.95)),
        REDACAO_MAX       =("NU_NOTA_REDACAO",   "max"),
        REDACAO_MEDIA     =("NU_NOTA_REDACAO",   "mean"),
        OBJETIVAS_MAX     =("MEDIA_OBJETIVAS",   "max"),
        OBJETIVAS_MEDIA   =("MEDIA_OBJETIVAS",   "mean"),
        TOTAL_CANDIDATOS  =("MEDIA_GERAL",       "count"),
    )
    .reset_index()
    .round(1)
)

resumo["GAP_MAX_MEDIA"] = (resumo["MEDIA_GERAL_MAX"] - resumo["MEDIA_GERAL_MEDIA"]).round(1)

saida = PASTA / "agregado_outliers_uf_2022.csv"
resumo.to_csv(saida, sep=";", index=False, encoding="utf-8")
print(f"Salvo em: {saida}")
print(resumo.sort_values("GAP_MAX_MEDIA", ascending=False).to_string(index=False))