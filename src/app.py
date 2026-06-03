import json
import urllib.request
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

# ── Caminhos ──────────────────────────────────────────────────────────────────

PASTA_ANALYTICS = Path(__file__).resolve().parents[1] / "data" / "analytics"
GEOJSON_CACHE   = Path(__file__).resolve().parents[1] / "data" / "uf_brasil.geojson"
_GEOJSON_URL    = (
    "https://raw.githubusercontent.com/codeforamerica/click_that_hood"
    "/master/public/data/brazil-states.geojson"
)


def _carregar_geojson():
    if GEOJSON_CACHE.exists():
        with open(GEOJSON_CACHE, encoding="utf-8") as _f:
            return json.load(_f)
    try:
        with urllib.request.urlopen(_GEOJSON_URL, timeout=15) as _r:
            _data = json.loads(_r.read().decode("utf-8"))
        GEOJSON_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(GEOJSON_CACHE, "w", encoding="utf-8") as _f:
            json.dump(_data, _f)
        return _data
    except Exception:
        return None


UF_GEOJSON = _carregar_geojson()


# ── Paleta ────────────────────────────────────────────────────────────────────

NAVY       = "#2C3E50"
TEAL       = "#18BC9C"
BODY       = "#546E7A"
CARD       = "#F4F7FA"
TINT       = "#E8F8F5"
CINZA_AZUL = "#8FA3B0"
BRANCO     = "#FFFFFF"

AZUL_ESCURO = NAVY
AZUL_MEDIO  = TEAL
VERDE_AGUA  = TEAL
LARANJA     = CINZA_AZUL
CINZA_CLARO = CARD
CINZA_TEXTO = BODY

PALETA_SEQ  = [TINT, "#45C9A4", TEAL, "#12907A", NAVY]
PALETA_CAT  = [TEAL, NAVY, CINZA_AZUL, "#0E7C66", "#5C8A99"]
PORTE_CORES = ["#86D9C8", "#34C4A8", "#18BC9C", "#0E7C66", "#2C3E50"]


# ── Dados ─────────────────────────────────────────────────────────────────────

def _ler(nome: str) -> pd.DataFrame:
    caminho = PASTA_ANALYTICS / nome
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    return pd.read_csv(caminho, sep=";", encoding="utf-8")


df_resumo       = _ler("resumo_geral_2022.csv")
df_renda        = _ler("agregado_renda_2022.csv")
df_internet     = _ler("agregado_internet_2022.csv")
df_escola       = _ler("agregado_tipo_escola_2022.csv")
df_porte        = _ler("agregado_porte_municipio_2022.csv")
df_municipio    = _ler("agregado_municipio_2022.csv")
df_transformado = _ler("enem_2022_ibge_transformado.csv")
df_outliers_uf  = _ler("agregado_outliers_uf_2022.csv")

ORDEM_RENDA = [
    "Nenhuma renda", "Até 1 salário mínimo",
    "1 a 1,5 salários", "1,5 a 2 salários",
    "2 a 2,5 salários", "2,5 a 3 salários",
    "3 a 4 salários",   "4 a 5 salários",
    "5 a 6 salários",   "6 a 7 salários",
    "7 a 8 salários",   "8 a 9 salários",
    "9 a 10 salários",  "10 a 12 salários",
    "12 a 15 salários", "15 a 20 salários",
    "Acima de 20 salários",
]

ORDEM_PORTE = [
    "Até 20 mil", "20 mil a 100 mil",
    "100 mil a 500 mil", "500 mil a 1 milhão",
    "Acima de 1 milhão",
]

df_renda["RENDA_FAMILIAR"] = pd.Categorical(
    df_renda["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
)
df_renda = df_renda.sort_values("RENDA_FAMILIAR")

df_porte["PORTE_MUNICIPIO"] = pd.Categorical(
    df_porte["PORTE_MUNICIPIO"], categories=ORDEM_PORTE, ordered=True
)
df_porte = df_porte.sort_values("PORTE_MUNICIPIO")

DF_BOX_SAMPLE = (
    df_transformado
    .dropna(subset=["RENDA_FAMILIAR", "NU_NOTA_REDACAO"])
    .sample(min(15_000, len(df_transformado)), random_state=42)
    .assign(RENDA_FAMILIAR=lambda d: pd.Categorical(
        d["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
    ))
)

_heat_base = (
    df_transformado
    .dropna(subset=["MEDIA_OBJETIVAS", "NU_NOTA_REDACAO"])
    .query("300 <= MEDIA_OBJETIVAS <= 700 and 300 <= NU_NOTA_REDACAO <= 1000")
)
DF_HEAT_SAMPLE = _heat_base.sample(min(100_000, len(_heat_base)), random_state=42)

_uf_base = df_municipio.dropna(subset=["SG_UF_PROVA", "MEDIA_GERAL", "TOTAL_PARTICIPANTES"])
DF_UF = (
    _uf_base
    .assign(_PESO=_uf_base["MEDIA_GERAL"] * _uf_base["TOTAL_PARTICIPANTES"])
    .groupby("SG_UF_PROVA")
    .agg(_SOMA_PESO=("_PESO", "sum"), TOTAL_PARTICIPANTES=("TOTAL_PARTICIPANTES", "sum"))
    .assign(MEDIA_GERAL=lambda d: d["_SOMA_PESO"] / d["TOTAL_PARTICIPANTES"])
    .drop(columns="_SOMA_PESO")
    .reset_index()
)

df_outliers_uf = df_outliers_uf.sort_values("GAP_MAX_MEDIA", ascending=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _layout(fig, titulo=""):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=45, b=50),
        title=dict(text=titulo, font=dict(size=13, color=NAVY, family="Poppins, sans-serif")),
        paper_bgcolor=BRANCO,
        plot_bgcolor=BRANCO,
        font=dict(size=11, color=BODY),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def _vazio_fig(msg="Sem dados para os filtros selecionados"):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        annotations=[dict(text=msg, showarrow=False, x=.5, y=.5,
                          xref="paper", yref="paper",
                          font=dict(size=14, color=BODY))],
    )
    return fig


def _card(icone, titulo, valor, subtitulo, cor=TEAL):
    return dbc.Card(
        dbc.CardBody(
            html.Div([
                html.Span(icone, style={"fontSize": "1.6rem"}),
                html.Div([
                    html.P(titulo, className="mb-0",
                           style={"fontSize": ".7rem", "color": BODY,
                                  "textTransform": "uppercase", "letterSpacing": "1px"}),
                    html.H4(valor, className="mb-0 fw-bold", style={"color": NAVY}),
                    html.P(subtitulo, className="mb-0",
                           style={"fontSize": ".75rem", "color": BODY}),
                ], className="ms-3"),
            ], className="d-flex align-items-center"),
        ),
        className="shadow-sm border-0 h-100",
        style={"borderLeft": f"4px solid {cor} !important", "borderRadius": "10px",
               "backgroundColor": CARD},
    )


def _aplicar_filtros(df, escola, internet, renda):
    if escola != "Todos" and "TIPO_ESCOLA" in df.columns:
        df = df[df["TIPO_ESCOLA"] == escola]
    if internet != "Todos" and "ACESSO_INTERNET" in df.columns:
        df = df[df["ACESSO_INTERNET"] == internet]
    if renda != "Todas" and "RENDA_FAMILIAR" in df.columns:
        df = df[df["RENDA_FAMILIAR"] == renda]
    return df


def _barras_renda(df_ag):
    fig = go.Figure([
        go.Bar(name="Objetivas", y=df_ag["RENDA_FAMILIAR"].astype(str),
               x=df_ag["MEDIA_OBJETIVAS"], orientation="h", marker_color=NAVY),
        go.Bar(name="Redação",   y=df_ag["RENDA_FAMILIAR"].astype(str),
               x=df_ag["MEDIA_REDACAO"],   orientation="h", marker_color=TEAL),
    ])
    fig.update_layout(barmode="group", xaxis_range=[350, 850])
    _layout(fig)
    fig.update_layout(
        legend=dict(orientation="h", x=1, xanchor="right", y=0, yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)"),
        margin=dict(l=40, r=20, t=20, b=50),
    )
    return fig


def _grafico_card(titulo, subtitulo=None, graph_id=None, altura=280):
    corpo = [html.H6(titulo, className="fw-bold mb-1", style={"color": NAVY})]
    if subtitulo:
        corpo.append(html.P(subtitulo, style={"fontSize": ".75rem", "color": BODY}))
    if graph_id:
        corpo.append(dcc.Graph(id=graph_id, config={"displayModeBar": False},
                               style={"height": f"{altura}px"}))
    return dbc.Card(dbc.CardBody(corpo), className="shadow-sm border-0 h-100",
                    style={"backgroundColor": CARD})


# ── Layouts das abas ──────────────────────────────────────────────────────────

def layout_visao_geral():
    r = df_resumo.iloc[0]
    cards = [
        ("", "Participantes",  f"{int(r['TOTAL_PARTICIPANTES']):,}".replace(",", "."),
         "Candidatos com nota válida", TEAL),
        ("", "Média Geral",    f"{r['MEDIA_GERAL']:.1f}",     "Todas as provas",     NAVY),
        ("", "Média Redação",  f"{r['MEDIA_REDACAO']:.1f}",   "Competência escrita", TEAL),
        ("", "Média Objetivas",f"{r['MEDIA_OBJETIVAS']:.1f}", "CN + CH + LC + MT",   NAVY),
        ("", "Com Internet",   f"{r['PERCENTUAL_COM_INTERNET']:.1f}%", "Acesso residencial", TEAL),
        ("", "Municípios",     f"{int(r['TOTAL_MUNICIPIOS_PROVA'])}",  "Com ao menos 1 prova", NAVY),
    ]
    return dbc.Container(fluid=True, children=[
        html.Div([
            html.H4("Visão Geral Executiva",
                    style={"fontFamily": "'Poppins', sans-serif", "color": NAVY}),
            html.P("Panorama nacional dos candidatos ao ENEM 2022.",
                   style={"color": BODY, "fontSize": ".9rem"}),
        ], className="mb-4"),
        dbc.Row([dbc.Col(_card(*c), md=2) for c in cards], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(_grafico_card("Participantes por tipo de escola",
                                  graph_id="g1-escola"), md=5),
            dbc.Col(_grafico_card("Desempenho médio × acesso à internet",
                                  graph_id="g1-internet"), md=7),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(_grafico_card("Média geral por faixa de renda familiar",
                                  graph_id="g1-renda", altura=420), md=12),
        ], className="mb-4 g-3"),
    ])


def layout_socioeconomico():
    rendas_disp = [r for r in ORDEM_RENDA
                   if r in df_transformado["RENDA_FAMILIAR"].dropna().unique()]

    filtros = dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col([
            html.Label("Tipo de escola", className="fw-bold",
                       style={"fontSize": ".8rem", "color": BODY}),
            dcc.Dropdown(id="f2-escola",
                options=[{"label": "Todos", "value": "Todos"}] + [
                    {"label": v, "value": v}
                    for v in df_transformado["TIPO_ESCOLA"].dropna().unique()
                    if v != "Não respondeu"
                ], value="Todos", clearable=False),
        ], md=4),
        dbc.Col([
            html.Label("Acesso à internet", className="fw-bold",
                       style={"fontSize": ".8rem", "color": BODY}),
            dcc.Dropdown(id="f2-internet",
                options=[{"label": l, "value": v} for l, v in
                         [("Todos","Todos"),("Sim","Sim"),("Não","Não")]],
                value="Todos", clearable=False),
        ], md=4),
        dbc.Col([
            html.Label("Faixa de renda (boxplot)", className="fw-bold",
                       style={"fontSize": ".8rem", "color": BODY}),
            dcc.Dropdown(id="f2-renda",
                options=[{"label": "Todas", "value": "Todas"}] +
                        [{"label": r, "value": r} for r in rendas_disp],
                value="Todas", clearable=False),
        ], md=4),
    ])), className="shadow-sm border-0 mb-4", style={"backgroundColor": CARD})

    return dbc.Container(fluid=True, children=[
        html.Div([
            html.H4("Desigualdade Socioeconômica",
                    style={"fontFamily": "'Poppins', sans-serif", "color": NAVY}),
            html.P("Explore como renda, escola e conectividade moldam o desempenho.",
                   style={"color": BODY, "fontSize": ".9rem"}),
        ], className="mb-4"),
        filtros,
        dbc.Row([
            dbc.Col(_grafico_card("Distribuição da nota de redação por renda",
                                  "Boxplot — mediana, quartis e outliers",
                                  "g2-boxplot", altura=400), md=7),
            dbc.Col(_grafico_card("Objetivas vs Redação por renda",
                                  "Barras agrupadas — médias comparadas",
                                  "g2-barras-duplas", altura=400), md=5),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(_grafico_card(
                "Concentração: provas objetivas × redação",
                "Mapa de densidade — regiões mais escuras = maior concentração de candidatos",
                "g2-heatmap", altura=350), md=12),
        ], className="mb-4 g-3"),
    ])


def layout_municipios():
    ufs = sorted(df_municipio["SG_UF_PROVA"].dropna().unique())

    filtros = dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col([
            html.Label("UF da prova", className="fw-bold",
                       style={"fontSize": ".8rem", "color": BODY}),
            dcc.Dropdown(id="f3-uf",
                options=[{"label": "Todas", "value": "Todas"}] +
                        [{"label": uf, "value": uf} for uf in ufs],
                value="Todas", clearable=False),
        ], md=4),
        dbc.Col([
            html.Label("Mínimo de participantes por município", className="fw-bold",
                       style={"fontSize": ".8rem", "color": BODY}),
            dcc.Slider(id="f3-min-part", min=50, max=2000, step=50, value=200,
                       marks={50:"50", 500:"500", 1000:"1k", 2000:"2k"},
                       tooltip={"placement": "bottom", "always_visible": False}),
        ], md=8),
    ])), className="shadow-sm border-0 mb-4", style={"backgroundColor": CARD})

    return dbc.Container(fluid=True, children=[
        html.Div([
            html.H4("Contexto Municipal & IBGE",
                    style={"fontFamily": "'Poppins', sans-serif", "color": NAVY}),
            html.P("Desempenho cruzado com dados populacionais do IBGE 2022.",
                   style={"color": BODY, "fontSize": ".9rem"}),
        ], className="mb-4"),
        filtros,

        # Linha 1 — mapa
        dbc.Row([
            dbc.Col(_grafico_card("Nota média por UF",
                                  "Média geral ponderada pelo número de participantes",
                                  "g3-mapa", altura=420), md=12),
        ], className="mb-4 g-3"),

        # Linha 2 — porte
        dbc.Row([
            dbc.Col(_grafico_card("Média geral por porte do município",
                                  "Classificação populacional pelo IBGE 2022",
                                  "g3-porte-media"), md=6),
            dbc.Col(_grafico_card("Participantes por porte do município",
                                  "Concentração de candidatos por tamanho de cidade",
                                  "g3-porte-part"), md=6),
        ], className="mb-4 g-3"),

        # Linha 3 — scatter + top15
        dbc.Row([
            dbc.Col(_grafico_card("População do município × Média geral",
                                  "Tamanho do ponto = total de participantes · Cor = porte",
                                  "g3-scatter", altura=380), md=7),
            dbc.Col(_grafico_card("Top 15 municípios — maior média geral",
                                  "Apenas municípios com mínimo de participantes definido no filtro",
                                  "g3-top-municipios", altura=380), md=5),
        ], className="mb-4 g-3"),

        # Linha 4 — desigualdade interna por UF
        html.Div([
            html.Hr(style={"borderColor": TEAL, "borderWidth": "2px", "opacity": "1"}),
            html.H5("Desigualdade Interna por Estado", className="fw-bold mt-3",
                    style={"color": NAVY, "fontFamily": "'Poppins', sans-serif"}),
            html.P(
                "Média vs máximo por UF — estados com maior gap revelam uma elite de alto "
                "desempenho completamente descolada da média estadual.",
                style={"color": BODY, "fontSize": ".85rem"},
            ),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(_grafico_card(
                "Média geral vs Máximo por UF",
                "Barras sobrepostas — a barra de fundo (navy) é o máximo; a da frente (teal) é a média",
                "g3-outlier-barras", altura=520), md=7),
            dbc.Col(_grafico_card(
                "Ranking de gap por UF",
                "Máximo − Média: maior gap = outlier mais distante da realidade estadual",
                "g3-outlier-gap", altura=520), md=5),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(_grafico_card(
                "Média, P95 e Máximo por UF",
                "Se P95 ≈ Máximo → topo consistente. Se P95 ≪ Máximo → outlier pontual isolado.",
                "g3-outlier-scatter", altura=420), md=12),
        ], className="mb-4 g-3"),
    ])


# ── App ───────────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
)
server = app.server

_HEADER = {
    "background": "linear-gradient(135deg, #2C3E50 0%, #1b2a3a 100%)",
    "padding": "2rem 2.5rem 1.5rem",
}

app.layout = html.Div([
    html.Div([
        html.H1("O Raio-X da Desigualdade no ENEM",
                style={"fontFamily": "'Poppins', sans-serif", "color": BRANCO,
                       "fontSize": "2rem", "marginBottom": ".3rem", "fontWeight": "700"}),
        html.P(
            "Microdados ENEM 2022 integrados a indicadores socioeconômicos do IBGE — "
            "análise de desempenho, renda familiar, acesso à internet e contexto municipal.",
            style={"color": "rgba(255,255,255,.7)", "fontSize": ".9rem", "margin": 0},
        ),
    ], style=_HEADER),

    dbc.Tabs([
        dbc.Tab(layout_visao_geral(),    label="① Visão Geral",       tab_id="tab1",
                label_style={"fontFamily": "'Poppins', sans-serif", "fontWeight": "500"}),
        dbc.Tab(layout_socioeconomico(), label="② Socioeconômico",    tab_id="tab2",
                label_style={"fontFamily": "'Poppins', sans-serif", "fontWeight": "500"}),
        dbc.Tab(layout_municipios(),     label="③ Municípios & IBGE", tab_id="tab3",
                label_style={"fontFamily": "'Poppins', sans-serif", "fontWeight": "500"}),
    ], active_tab="tab1",
       style={"backgroundColor": CARD, "paddingLeft": "1.5rem",
              "borderBottom": "3px solid #18BC9C"}),

], style={"fontFamily": "'Poppins', sans-serif", "backgroundColor": CARD, "minHeight": "100vh"})


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("g1-escola",   "figure"),
    Output("g1-internet", "figure"),
    Output("g1-renda",    "figure"),
    Input("g1-escola",    "id"),
)
def montar_visao_geral(_):
    fig_escola = px.pie(
        df_escola[df_escola["TIPO_ESCOLA"] != "Não respondeu"],
        names="TIPO_ESCOLA", values="TOTAL_PARTICIPANTES",
        color_discrete_sequence=PALETA_CAT, hole=0.55,
    )
    fig_escola.update_traces(textposition="outside", textinfo="percent+label")
    _layout(fig_escola)
    fig_escola.update_layout(showlegend=False, margin=dict(l=10, r=10, t=15, b=10))

    fig_internet = px.bar(
        df_internet.sort_values("MEDIA_GERAL"),
        x="MEDIA_GERAL", y="ACESSO_INTERNET", orientation="h",
        color="ACESSO_INTERNET",
        color_discrete_map={"Sim": TEAL, "Não": CINZA_AZUL},
        text="MEDIA_GERAL",
    )
    fig_internet.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_internet.update_xaxes(range=[400, 600])
    _layout(fig_internet)
    fig_internet.update_layout(showlegend=False)

    fig_renda = px.bar(
        df_renda,
        x="MEDIA_GERAL", y=df_renda["RENDA_FAMILIAR"].astype(str),
        orientation="h", color="MEDIA_GERAL",
        color_continuous_scale=[TINT, TEAL, NAVY],
        text="MEDIA_GERAL", labels={"MEDIA_GERAL": "Média Geral", "y": ""},
    )
    fig_renda.update_traces(
        texttemplate="%{x:.1f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Média Geral: %{x:.1f}<extra></extra>",
    )
    fig_renda.update_xaxes(range=[350, 850])
    _layout(fig_renda)
    fig_renda.update_layout(coloraxis_showscale=False, margin=dict(l=40, r=20, t=20, b=50))

    return fig_escola, fig_internet, fig_renda


@app.callback(
    Output("g2-boxplot",       "figure"),
    Output("g2-barras-duplas", "figure"),
    Output("g2-heatmap",       "figure"),
    Input("f2-escola",   "value"),
    Input("f2-internet", "value"),
    Input("f2-renda",    "value"),
)
def atualizar_socioeconomico(escola, internet, renda):
    dados_box = _aplicar_filtros(DF_BOX_SAMPLE.copy(), escola, internet, renda)
    dados_box = dados_box.dropna(subset=["RENDA_FAMILIAR", "NU_NOTA_REDACAO"])
    dados_box["RENDA_FAMILIAR"] = pd.Categorical(
        dados_box["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
    )
    if dados_box.empty:
        fig_box = _vazio_fig()
    else:
        fig_box = px.box(
            dados_box.sort_values("RENDA_FAMILIAR"),
            y="RENDA_FAMILIAR", x="NU_NOTA_REDACAO", orientation="h",
            color_discrete_sequence=[TEAL],
            labels={"NU_NOTA_REDACAO": "Nota de Redação", "RENDA_FAMILIAR": ""},
        )
        _layout(fig_box)
        fig_box.update_layout(showlegend=False)

    dados_bar = _aplicar_filtros(DF_BOX_SAMPLE.copy(), escola, internet, renda)
    if dados_bar.empty:
        fig_bar = _vazio_fig()
    else:
        df_ag = (
            dados_bar
            .dropna(subset=["RENDA_FAMILIAR", "MEDIA_OBJETIVAS", "NU_NOTA_REDACAO"])
            .groupby("RENDA_FAMILIAR", observed=True)
            .agg(MEDIA_OBJETIVAS=("MEDIA_OBJETIVAS", "mean"),
                 MEDIA_REDACAO=("NU_NOTA_REDACAO", "mean"))
            .reset_index()
        )
        df_ag["RENDA_FAMILIAR"] = pd.Categorical(
            df_ag["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
        )
        fig_bar = _barras_renda(df_ag.sort_values("RENDA_FAMILIAR"))

    dados_heat = _aplicar_filtros(DF_HEAT_SAMPLE.copy(), escola, internet, renda)
    dados_heat = (
        dados_heat
        .dropna(subset=["MEDIA_OBJETIVAS", "NU_NOTA_REDACAO"])
        .query("300 <= MEDIA_OBJETIVAS <= 750 and 300 <= NU_NOTA_REDACAO <= 1000")
    )
    if dados_heat.empty:
        fig_heat = _vazio_fig()
    else:
        n = len(dados_heat)
        fig_heat = px.density_heatmap(
            dados_heat, x="MEDIA_OBJETIVAS", y="NU_NOTA_REDACAO",
            nbinsx=50, nbinsy=50,
            color_continuous_scale=[[0, BRANCO], [0.5, TEAL], [1, NAVY]],
            labels={"MEDIA_OBJETIVAS": "Média das Provas Objetivas",
                    "NU_NOTA_REDACAO": "Nota de Redação", "count": "Quantidade de candidatos"},
        )
        fig_heat.update_xaxes(range=[300, 750])
        fig_heat.update_yaxes(range=[300, 1000])
        fig_heat.update_traces(hovertemplate=(
            "Média objetivas: %{x}<br>Nota redação: %{y}<br>"
            "Quantidade na faixa: %{z}<extra></extra>"
        ))
        fig_heat.update_layout(coloraxis_colorbar_title="Qtd.", bargap=0)
        _layout(fig_heat, f"Concentração: objetivas × redação — n = {n:,}".replace(",", "."))

    return fig_box, fig_bar, fig_heat


@app.callback(
    Output("g3-porte-media",    "figure"),
    Output("g3-porte-part",     "figure"),
    Output("g3-scatter",        "figure"),
    Output("g3-top-municipios", "figure"),
    Input("f3-uf",       "value"),
    Input("f3-min-part", "value"),
)
def atualizar_municipios(uf, min_part):
    def _porte_bar(y_col, label, fmt, y_range=None):
        fig = px.bar(
            df_porte, x="PORTE_MUNICIPIO", y=y_col,
            color="PORTE_MUNICIPIO", text=y_col,
            color_discrete_sequence=PALETA_SEQ,
            labels={"PORTE_MUNICIPIO": "", y_col: label},
        )
        fig.update_traces(texttemplate=fmt, textposition="outside")
        if y_range:
            fig.update_yaxes(range=y_range)
        _layout(fig)
        fig.update_layout(showlegend=False)
        return fig

    fig_pm = _porte_bar("MEDIA_GERAL",        "Média Geral",   "%{text:.1f}", [450, 600])
    fig_pp = _porte_bar("TOTAL_PARTICIPANTES", "Participantes", "%{text:,}")

    df_m = df_municipio.copy()
    if uf != "Todas":
        df_m = df_m[df_m["SG_UF_PROVA"] == uf]
    df_m = df_m[df_m["TOTAL_PARTICIPANTES"] >= min_part]

    if df_m.empty:
        v = _vazio_fig("Sem municípios com esses critérios")
        return fig_pm, fig_pp, v, v

    fig_sc = px.scatter(
        df_m, x="POPULACAO_MUNICIPIO", y="MEDIA_GERAL",
        size="TOTAL_PARTICIPANTES", color="PORTE_MUNICIPIO",
        hover_name="NO_MUNICIPIO_PROVA",
        hover_data={"SG_UF_PROVA": True, "TOTAL_PARTICIPANTES": True,
                    "POPULACAO_MUNICIPIO": True, "PORTE_MUNICIPIO": False},
        color_discrete_sequence=PORTE_CORES, size_max=34, log_x=True,
        labels={"POPULACAO_MUNICIPIO": "População (escala log)", "MEDIA_GERAL": "Média Geral"},
        category_orders={"PORTE_MUNICIPIO": ORDEM_PORTE},
    )
    _layout(fig_sc)
    fig_sc.update_traces(marker=dict(opacity=0.78, line=dict(width=0.5, color=NAVY)))

    top15 = (
        df_m.sort_values("MEDIA_GERAL", ascending=False).head(15)
        .sort_values("MEDIA_GERAL")
        .assign(LABEL=lambda d: d["NO_MUNICIPIO_PROVA"] + " - " + d["SG_UF_PROVA"])
    )
    fig_top = px.bar(
        top15, x="MEDIA_GERAL", y="LABEL", orientation="h",
        color="MEDIA_GERAL", color_continuous_scale=[TINT, TEAL, NAVY],
        text="MEDIA_GERAL", labels={"MEDIA_GERAL": "Média Geral", "LABEL": ""},
    )
    fig_top.update_traces(
        texttemplate="%{x:.1f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Média Geral: %{x:.1f}<extra></extra>",
    )
    _layout(fig_top)
    fig_top.update_layout(coloraxis_showscale=False)

    return fig_pm, fig_pp, fig_sc, fig_top


@app.callback(
    Output("g3-mapa", "figure"),
    Input("f3-uf", "value"),
)
def montar_mapa_uf(uf):
    if UF_GEOJSON is None:
        return _vazio_fig("GeoJSON indisponível — sem conexão ou arquivo data/uf_brasil.geojson ausente")
    fig_mapa = px.choropleth(
        DF_UF, geojson=UF_GEOJSON,
        locations="SG_UF_PROVA", featureidkey="properties.sigla",
        color="MEDIA_GERAL", color_continuous_scale=["#CDEFE8", TEAL, NAVY],
        hover_name="SG_UF_PROVA",
        hover_data={"TOTAL_PARTICIPANTES": True, "SG_UF_PROVA": False},
        labels={"MEDIA_GERAL": "Média Geral", "TOTAL_PARTICIPANTES": "Participantes"},
    )
    if uf and uf != "Todas":
        fig_mapa.add_trace(go.Choropleth(
            geojson=UF_GEOJSON, locations=[uf], featureidkey="properties.sigla",
            z=[1], colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False, marker_line_color=NAVY, marker_line_width=3, hoverinfo="skip",
        ))
    fig_mapa.update_geos(fitbounds="locations", visible=False)
    _layout(fig_mapa)
    fig_mapa.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    return fig_mapa


@app.callback(
    Output("g3-outlier-barras",  "figure"),
    Output("g3-outlier-gap",     "figure"),
    Output("g3-outlier-scatter", "figure"),
    Input("g3-outlier-barras",   "id"),   # disparo único ao carregar
)
def montar_outliers_uf(_):
    df = df_outliers_uf.copy()

    # Gráfico 1 — barras sobrepostas: Máximo (fundo) vs Média (frente)
    df_b = df.sort_values("MEDIA_GERAL_MAX", ascending=True)
    fig_barras = go.Figure([
        go.Bar(name="Máximo", y=df_b["SG_UF_PROVA"], x=df_b["MEDIA_GERAL_MAX"],
               orientation="h", marker_color=NAVY,
               hovertemplate="<b>%{y}</b><br>Máximo: %{x:.1f}<extra></extra>"),
        go.Bar(name="Média", y=df_b["SG_UF_PROVA"], x=df_b["MEDIA_GERAL_MEDIA"],
               orientation="h", marker_color=TEAL,
               hovertemplate="<b>%{y}</b><br>Média: %{x:.1f}<extra></extra>"),
    ])
    fig_barras.update_layout(
        barmode="overlay", xaxis_range=[400, 1000],
        legend=dict(orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom",
                    bgcolor="rgba(255,255,255,0.8)"),
        margin=dict(l=40, r=20, t=30, b=40),
    )
    _layout(fig_barras)

    # Gráfico 2 — ranking de gap
    df_g = df.sort_values("GAP_MAX_MEDIA", ascending=True)
    fig_gap = px.bar(
        df_g, x="GAP_MAX_MEDIA", y="SG_UF_PROVA", orientation="h",
        color="GAP_MAX_MEDIA", color_continuous_scale=[TINT, TEAL, NAVY],
        text="GAP_MAX_MEDIA",
        labels={"GAP_MAX_MEDIA": "Gap (pts)", "SG_UF_PROVA": ""},
        custom_data=["MEDIA_GERAL_MEDIA", "MEDIA_GERAL_MAX"],
    )
    fig_gap.update_traces(
        texttemplate="%{x:.1f}", textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>Gap: %{x:.1f} pts<br>"
            "Média: %{customdata[0]:.1f}<br>Máximo: %{customdata[1]:.1f}<extra></extra>"
        ),
    )
    _layout(fig_gap)
    fig_gap.update_xaxes(range=[200, df_g["GAP_MAX_MEDIA"].max() * 1.15])
    fig_gap.update_layout(coloraxis_showscale=False, margin=dict(l=40, r=60, t=30, b=40))

    # Gráfico 3 — strip plot com Média / P95 / Máximo
    df_long = df.melt(
        id_vars="SG_UF_PROVA",
        value_vars=["MEDIA_GERAL_MEDIA", "MEDIA_GERAL_P95", "MEDIA_GERAL_MAX"],
        var_name="Métrica", value_name="Valor",
    ).replace({"MEDIA_GERAL_MEDIA": "Média", "MEDIA_GERAL_P95": "P95",
               "MEDIA_GERAL_MAX": "Máximo"})

    ordem_uf = df.sort_values("MEDIA_GERAL_MEDIA")["SG_UF_PROVA"].tolist()
    fig_scatter = px.strip(
        df_long, x="Valor", y="SG_UF_PROVA", color="Métrica",
        color_discrete_map={"Média": CINZA_AZUL, "P95": TEAL, "Máximo": NAVY},
        labels={"Valor": "Pontuação", "SG_UF_PROVA": ""},
        category_orders={"SG_UF_PROVA": ordem_uf, "Métrica": ["Média", "P95", "Máximo"]},
        stripmode="overlay",
    )
    fig_scatter.update_traces(marker=dict(size=10, opacity=0.85))
    fig_scatter.update_xaxes(range=[400, 1000])
    _layout(fig_scatter)
    fig_scatter.update_layout(
        legend=dict(orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom",
                    bgcolor="rgba(255,255,255,0.8)"),
        margin=dict(l=40, r=20, t=30, b=40),
    )

    return fig_barras, fig_gap, fig_scatter


# ── Execução ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)