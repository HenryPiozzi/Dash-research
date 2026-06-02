from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc


# ─────────────────────────────────────────────
#  CAMINHOS
# ─────────────────────────────────────────────

PASTA_RAIZ      = Path(__file__).resolve().parents[1]
PASTA_ANALYTICS = PASTA_RAIZ / "data" / "analytics"

# ─────────────────────────────────────────────
#  PALETA
# ─────────────────────────────────────────────

AZUL_ESCURO  = "#1a2e4a"
AZUL_MEDIO   = "#2563eb"
VERDE_AGUA   = "#0d9488"
LARANJA      = "#f97316"
CINZA_CLARO  = "#f1f5f9"
CINZA_TEXTO  = "#64748b"
BRANCO       = "#ffffff"

PALETA_SEQ   = [AZUL_ESCURO, AZUL_MEDIO, VERDE_AGUA, "#38bdf8", "#7dd3fc"]
PALETA_CAT   = [AZUL_MEDIO, VERDE_AGUA, LARANJA, "#8b5cf6", "#ec4899"]

# ─────────────────────────────────────────────
#  CARREGAMENTO DOS AGREGADOS
# ─────────────────────────────────────────────

def _ler(nome: str) -> pd.DataFrame:
    caminho = PASTA_ANALYTICS / nome
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    return pd.read_csv(caminho, sep=";", encoding="utf-8")


df_resumo        = _ler("resumo_geral_2022.csv")
df_renda         = _ler("agregado_renda_2022.csv")
df_internet      = _ler("agregado_internet_2022.csv")
df_escola        = _ler("agregado_tipo_escola_2022.csv")
df_porte         = _ler("agregado_porte_municipio_2022.csv")
df_municipio     = _ler("agregado_municipio_2022.csv")
df_transformado  = _ler("enem_2022_ibge_transformado.csv")

# Ordem correta de renda para gráficos
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

# Garante ordem categórica
df_renda["RENDA_FAMILIAR"] = pd.Categorical(
    df_renda["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
)
df_renda = df_renda.sort_values("RENDA_FAMILIAR")

df_porte["PORTE_MUNICIPIO"] = pd.Categorical(
    df_porte["PORTE_MUNICIPIO"], categories=ORDEM_PORTE, ordered=True
)
df_porte = df_porte.sort_values("PORTE_MUNICIPIO")

# Amostra para boxplot (pesado na base completa)
DF_BOX_SAMPLE = (
    df_transformado
    .dropna(subset=["RENDA_FAMILIAR", "NU_NOTA_REDACAO"])
    .sample(min(15_000, len(df_transformado)), random_state=42)
)
DF_BOX_SAMPLE["RENDA_FAMILIAR"] = pd.Categorical(
    DF_BOX_SAMPLE["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _layout(fig, titulo=""):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=45, b=50),
        title=dict(text=titulo, font=dict(size=13, color=AZUL_ESCURO, family="Georgia, serif")),
        paper_bgcolor=BRANCO,
        plot_bgcolor=CINZA_CLARO,
        font=dict(size=11, color=CINZA_TEXTO),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def _card(icone, titulo, valor, subtitulo, cor_borda=AZUL_MEDIO):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icone, style={"fontSize": "1.6rem"}),
                html.Div([
                    html.P(titulo, className="mb-0",
                           style={"fontSize": ".7rem", "color": CINZA_TEXTO,
                                  "textTransform": "uppercase", "letterSpacing": "1px"}),
                    html.H4(valor, className="mb-0 fw-bold",
                            style={"color": AZUL_ESCURO}),
                    html.P(subtitulo, className="mb-0",
                           style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                ], className="ms-3"),
            ], className="d-flex align-items-center"),
        ]),
        className="shadow-sm border-0 h-100",
        style={"borderLeft": f"4px solid {cor_borda} !important",
               "borderRadius": "10px"},
    )


# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap",
    ],
    suppress_callback_exceptions=True,
)
server = app.server


# ─────────────────────────────────────────────
#  ABA 1 — VISÃO GERAL EXECUTIVA
# ─────────────────────────────────────────────

def layout_visao_geral():
    r = df_resumo.iloc[0]
    return dbc.Container(fluid=True, children=[

        # Cabeçalho da aba
        html.Div([
            html.H4("Visão Geral Executiva", style={"fontFamily": "'Playfair Display', serif",
                                                     "color": AZUL_ESCURO}),
            html.P("Panorama nacional dos candidatos ao ENEM 2022.",
                   style={"color": CINZA_TEXTO, "fontSize": ".9rem"}),
        ], className="mb-4"),

        # Cards de indicadores
        dbc.Row([
            dbc.Col(_card("👥", "Participantes", f"{int(r['TOTAL_PARTICIPANTES']):,}".replace(",", "."),
                          "Candidatos com nota válida", AZUL_MEDIO), md=2),
            dbc.Col(_card("📊", "Média Geral", f"{r['MEDIA_GERAL']:.1f}",
                          "Todas as provas", VERDE_AGUA), md=2),
            dbc.Col(_card("✍️", "Média Redação", f"{r['MEDIA_REDACAO']:.1f}",
                          "Competência escrita", LARANJA), md=2),
            dbc.Col(_card("📐", "Média Objetivas", f"{r['MEDIA_OBJETIVAS']:.1f}",
                          "CN + CH + LC + MT", AZUL_ESCURO), md=2),
            dbc.Col(_card("🌐", "Com Internet", f"{r['PERCENTUAL_COM_INTERNET']:.1f}%",
                          "Acesso residencial", VERDE_AGUA), md=2),
            dbc.Col(_card("🏙️", "Municípios", f"{int(r['TOTAL_MUNICIPIOS_PROVA'])}",
                          "Com ao menos 1 prova", AZUL_MEDIO), md=2),
        ], className="mb-4 g-3"),

        # Linha 1: escola + internet
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Participantes por tipo de escola", className="fw-bold mb-3",
                        style={"color": AZUL_ESCURO}),
                dcc.Graph(id="g1-escola", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ]), className="shadow-sm border-0 h-100"), md=5),

            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Desempenho médio × acesso à internet", className="fw-bold mb-3",
                        style={"color": AZUL_ESCURO}),
                dcc.Graph(id="g1-internet", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ]), className="shadow-sm border-0 h-100"), md=7),
        ], className="mb-4 g-3"),

        # Linha 2: renda
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Média geral, redação e provas objetivas por renda familiar",
                        className="fw-bold mb-3", style={"color": AZUL_ESCURO}),
                dcc.Graph(id="g1-renda", config={"displayModeBar": False},
                          style={"height": "420px"}),
            ]), className="shadow-sm border-0"), md=12),
        ], className="mb-4 g-3"),
    ])


# ─────────────────────────────────────────────
#  ABA 2 — DESIGUALDADE SOCIOECONÔMICA
# ─────────────────────────────────────────────

def layout_socioeconomico():
    rendas_disp = [r for r in ORDEM_RENDA if r in df_transformado["RENDA_FAMILIAR"].dropna().unique()]
    return dbc.Container(fluid=True, children=[

        html.Div([
            html.H4("Desigualdade Socioeconômica", style={"fontFamily": "'Playfair Display', serif",
                                                           "color": AZUL_ESCURO}),
            html.P("Explore como renda, escola e conectividade moldam o desempenho.",
                   style={"color": CINZA_TEXTO, "fontSize": ".9rem"}),
        ], className="mb-4"),

        # Filtros
        dbc.Card(dbc.CardBody(
            dbc.Row([
                dbc.Col([
                    html.Label("Tipo de escola", className="fw-bold",
                               style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
                    dcc.Dropdown(
                        id="f2-escola",
                        options=[{"label": "Todos", "value": "Todos"}] +
                                [{"label": v, "value": v}
                                 for v in df_transformado["TIPO_ESCOLA"].dropna().unique()
                                 if v != "Não respondeu"],
                        value="Todos", clearable=False,
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Acesso à internet", className="fw-bold",
                               style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
                    dcc.Dropdown(
                        id="f2-internet",
                        options=[{"label": "Todos", "value": "Todos"},
                                 {"label": "Sim", "value": "Sim"},
                                 {"label": "Não", "value": "Não"}],
                        value="Todos", clearable=False,
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Faixa de renda (boxplot)", className="fw-bold",
                               style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
                    dcc.Dropdown(
                        id="f2-renda",
                        options=[{"label": "Todas", "value": "Todas"}] +
                                [{"label": r, "value": r} for r in rendas_disp],
                        value="Todas", clearable=False,
                        multi=False,
                    ),
                ], md=4),
            ])
        ), className="shadow-sm border-0 mb-4"),

        # Linha 1: boxplot + barras agrupadas
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Distribuição da nota de redação por renda",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Boxplot — mediana, quartis e outliers",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g2-boxplot", config={"displayModeBar": False},
                          style={"height": "400px"}),
            ]), className="shadow-sm border-0"), md=7),

            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Objetivas vs Redação por renda",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Barras agrupadas — médias comparadas",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g2-barras-duplas", config={"displayModeBar": False},
                          style={"height": "400px"}),
            ]), className="shadow-sm border-0"), md=5),
        ], className="mb-4 g-3"),

        # Linha 2: dispersão de densidade
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Concentração: média geral × nota de redação",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Mapa de densidade — regiões mais escuras = maior concentração de candidatos",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g2-heatmap", config={"displayModeBar": False},
                          style={"height": "350px"}),
            ]), className="shadow-sm border-0"), md=12),
        ], className="mb-4 g-3"),
    ])


# ─────────────────────────────────────────────
#  ABA 3 — CONTEXTO MUNICIPAL
# ─────────────────────────────────────────────

def layout_municipios():
    ufs = sorted(df_municipio["SG_UF_PROVA"].dropna().unique())
    return dbc.Container(fluid=True, children=[

        html.Div([
            html.H4("Contexto Municipal & IBGE", style={"fontFamily": "'Playfair Display', serif",
                                                         "color": AZUL_ESCURO}),
            html.P("Desempenho cruzado com dados populacionais do IBGE 2022.",
                   style={"color": CINZA_TEXTO, "fontSize": ".9rem"}),
        ], className="mb-4"),

        # Filtros
        dbc.Card(dbc.CardBody(
            dbc.Row([
                dbc.Col([
                    html.Label("UF da prova", className="fw-bold",
                               style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
                    dcc.Dropdown(
                        id="f3-uf",
                        options=[{"label": "Todas", "value": "Todas"}] +
                                [{"label": uf, "value": uf} for uf in ufs],
                        value="Todas", clearable=False,
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Mínimo de participantes por município",
                               className="fw-bold",
                               style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
                    dcc.Slider(id="f3-min-part", min=50, max=2000, step=50,
                               value=200,
                               marks={50: "50", 500: "500", 1000: "1k", 2000: "2k"},
                               tooltip={"placement": "bottom", "always_visible": False}),
                ], md=8),
            ])
        ), className="shadow-sm border-0 mb-4"),

        # Linha 1: barras porte + participantes por porte
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Média geral por porte do município",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Classificação populacional pelo IBGE 2022",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g3-porte-media", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ]), className="shadow-sm border-0"), md=6),

            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Participantes por porte do município",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Concentração de candidatos por tamanho de cidade",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g3-porte-part", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ]), className="shadow-sm border-0"), md=6),
        ], className="mb-4 g-3"),

        # Linha 2: scatter + top municípios
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("População do município × Média geral",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Tamanho do ponto = total de participantes · Cor = porte",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g3-scatter", config={"displayModeBar": False},
                          style={"height": "380px"}),
            ]), className="shadow-sm border-0"), md=7),

            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Top 15 municípios — maior média geral",
                        className="fw-bold mb-1", style={"color": AZUL_ESCURO}),
                html.P("Apenas municípios com mínimo de participantes definido no filtro",
                       style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                dcc.Graph(id="g3-top-municipios", config={"displayModeBar": False},
                          style={"height": "380px"}),
            ]), className="shadow-sm border-0"), md=5),
        ], className="mb-4 g-3"),
    ])


# ─────────────────────────────────────────────
#  LAYOUT PRINCIPAL
# ─────────────────────────────────────────────

_HEADER_STYLE = {
    "background": f"linear-gradient(135deg, {AZUL_ESCURO} 0%, #0f3460 100%)",
    "padding": "2rem 2.5rem 1.5rem",
    "marginBottom": "0",
}

app.layout = html.Div([

    # ── Header ──────────────────────────────
    html.Div([
        html.H1("O Raio-X da Desigualdade no ENEM",
                style={"fontFamily": "'Playfair Display', serif",
                       "color": BRANCO, "fontSize": "2rem", "marginBottom": ".3rem"}),
        html.P("Microdados ENEM 2022 integrados a indicadores socioeconômicos do IBGE — "
               "análise de desempenho, renda familiar, acesso à internet e contexto municipal.",
               style={"color": "rgba(255,255,255,.7)", "fontSize": ".9rem", "margin": 0}),
    ], style=_HEADER_STYLE),

    # ── Tabs ────────────────────────────────
    dbc.Tabs([
        dbc.Tab(layout_visao_geral(),
                label="① Visão Geral",      tab_id="tab1",
                label_style={"fontFamily": "'DM Sans', sans-serif", "fontWeight": "500"}),
        dbc.Tab(layout_socioeconomico(),
                label="② Socioeconômico",   tab_id="tab2",
                label_style={"fontFamily": "'DM Sans', sans-serif", "fontWeight": "500"}),
        dbc.Tab(layout_municipios(),
                label="③ Municípios & IBGE", tab_id="tab3",
                label_style={"fontFamily": "'DM Sans', sans-serif", "fontWeight": "500"}),
    ], active_tab="tab1",
       style={"backgroundColor": CINZA_CLARO, "paddingLeft": "1.5rem",
              "borderBottom": f"3px solid {AZUL_MEDIO}"}),

], style={"fontFamily": "'DM Sans', sans-serif", "backgroundColor": CINZA_CLARO,
          "minHeight": "100vh"})


# ─────────────────────────────────────────────
#  CALLBACKS — ABA 1  (estáticos, sem filtro)
# ─────────────────────────────────────────────

@app.callback(
    Output("g1-escola",   "figure"),
    Output("g1-internet", "figure"),
    Output("g1-renda",    "figure"),
    Input("g1-escola",    "id"),   # disparo único ao carregar
)
def montar_visao_geral(_):

    # — Escola (pizza)
    fig_escola = px.pie(
        df_escola[df_escola["TIPO_ESCOLA"] != "Não respondeu"],
        names="TIPO_ESCOLA", values="TOTAL_PARTICIPANTES",
        color_discrete_sequence=PALETA_CAT,
        hole=0.55,
    )
    fig_escola.update_traces(textposition="outside", textinfo="percent+label")
    _layout(fig_escola)
    fig_escola.update_layout(showlegend=False, margin=dict(l=10, r=10, t=15, b=10))

    # — Internet (barras horizontais)
    fig_internet = px.bar(
        df_internet.sort_values("MEDIA_GERAL"),
        x="MEDIA_GERAL", y="ACESSO_INTERNET",
        orientation="h",
        color="ACESSO_INTERNET",
        color_discrete_map={"Sim": VERDE_AGUA, "Não": LARANJA},
        text="MEDIA_GERAL",
    )
    fig_internet.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_internet.update_xaxes(range=[400, 600])
    _layout(fig_internet)
    fig_internet.update_layout(showlegend=False)

    # — Renda (barras agrupadas: objetivas + redação)
    df_plot = df_renda.copy()
    fig_renda = go.Figure()
    fig_renda.add_trace(go.Bar(
        name="Provas Objetivas",
        y=df_plot["RENDA_FAMILIAR"].astype(str),
        x=df_plot["MEDIA_OBJETIVAS"],
        orientation="h",
        marker_color=AZUL_MEDIO,
        opacity=0.85,
    ))
    fig_renda.add_trace(go.Bar(
        name="Redação",
        y=df_plot["RENDA_FAMILIAR"].astype(str),
        x=df_plot["MEDIA_REDACAO"],
        orientation="h",
        marker_color=VERDE_AGUA,
        opacity=0.85,
    ))
    fig_renda.update_layout(barmode="group", xaxis_range=[350, 850])
    _layout(fig_renda)
    fig_renda.update_layout(legend=dict(orientation="h", y=1.05))

    return fig_escola, fig_internet, fig_renda


# ─────────────────────────────────────────────
#  CALLBACKS — ABA 2
# ─────────────────────────────────────────────

@app.callback(
    Output("g2-boxplot",      "figure"),
    Output("g2-barras-duplas","figure"),
    Output("g2-heatmap",      "figure"),
    Input("f2-escola",   "value"),
    Input("f2-internet", "value"),
    Input("f2-renda",    "value"),
)
def atualizar_socioeconomico(escola, internet, renda):

    dados = DF_BOX_SAMPLE.copy()

    if escola != "Todos" and "TIPO_ESCOLA" in dados.columns:
        dados = dados[dados["TIPO_ESCOLA"] == escola]
    if internet != "Todos" and "ACESSO_INTERNET" in dados.columns:
        dados = dados[dados["ACESSO_INTERNET"] == internet]
    if renda != "Todas" and "RENDA_FAMILIAR" in dados.columns:
        dados = dados[dados["RENDA_FAMILIAR"] == renda]

    _vazio = go.Figure()
    _vazio.update_layout(
        template="plotly_white",
        annotations=[dict(text="Sem dados para os filtros selecionados",
                          showarrow=False, x=.5, y=.5, xref="paper", yref="paper",
                          font=dict(size=14, color=CINZA_TEXTO))]
    )

    if dados.empty:
        return _vazio, _vazio, _vazio

    # Boxplot
    dados_box = dados.dropna(subset=["RENDA_FAMILIAR", "NU_NOTA_REDACAO"]).copy()
    dados_box["RENDA_FAMILIAR"] = pd.Categorical(
        dados_box["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
    )
    dados_box = dados_box.sort_values("RENDA_FAMILIAR")

    fig_box = px.box(
        dados_box, y="RENDA_FAMILIAR", x="NU_NOTA_REDACAO",
        orientation="h",
        color_discrete_sequence=[AZUL_MEDIO],
        labels={"NU_NOTA_REDACAO": "Nota de Redação", "RENDA_FAMILIAR": ""},
    )
    _layout(fig_box)
    fig_box.update_layout(showlegend=False)

    # Barras duplas — usa agregado (independe dos filtros de amostra)
    df_ag = df_renda.copy()
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Objetivas",
        y=df_ag["RENDA_FAMILIAR"].astype(str),
        x=df_ag["MEDIA_OBJETIVAS"],
        orientation="h",
        marker_color=AZUL_MEDIO,
    ))
    fig_bar.add_trace(go.Bar(
        name="Redação",
        y=df_ag["RENDA_FAMILIAR"].astype(str),
        x=df_ag["MEDIA_REDACAO"],
        orientation="h",
        marker_color=VERDE_AGUA,
    ))
    fig_bar.update_layout(barmode="group", xaxis_range=[350, 850])
    _layout(fig_bar)
    fig_bar.update_layout(legend=dict(orientation="h", y=1.05))

    # Heatmap de densidade
    fig_heat = px.density_heatmap(
        dados.dropna(subset=["MEDIA_GERAL", "NU_NOTA_REDACAO"]),
        x="MEDIA_GERAL", y="NU_NOTA_REDACAO",
        nbinsx=40, nbinsy=40,
        color_continuous_scale="Blues",
        labels={"MEDIA_GERAL": "Média Geral", "NU_NOTA_REDACAO": "Nota de Redação"},
    )
    _layout(fig_heat)

    return fig_box, fig_bar, fig_heat


# ─────────────────────────────────────────────
#  CALLBACKS — ABA 3
# ─────────────────────────────────────────────

@app.callback(
    Output("g3-porte-media",    "figure"),
    Output("g3-porte-part",     "figure"),
    Output("g3-scatter",        "figure"),
    Output("g3-top-municipios", "figure"),
    Input("f3-uf",       "value"),
    Input("f3-min-part", "value"),
)
def atualizar_municipios(uf, min_part):

    # Porte (sempre global)
    df_p = df_porte.copy()

    fig_pm = px.bar(
        df_p, x="PORTE_MUNICIPIO", y="MEDIA_GERAL",
        color="PORTE_MUNICIPIO",
        text="MEDIA_GERAL",
        color_discrete_sequence=PALETA_SEQ,
        labels={"PORTE_MUNICIPIO": "", "MEDIA_GERAL": "Média Geral"},
    )
    fig_pm.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_pm.update_yaxes(range=[450, 600])
    _layout(fig_pm)
    fig_pm.update_layout(showlegend=False)

    fig_pp = px.bar(
        df_p, x="PORTE_MUNICIPIO", y="TOTAL_PARTICIPANTES",
        color="PORTE_MUNICIPIO",
        text="TOTAL_PARTICIPANTES",
        color_discrete_sequence=PALETA_SEQ,
        labels={"PORTE_MUNICIPIO": "", "TOTAL_PARTICIPANTES": "Participantes"},
    )
    fig_pp.update_traces(texttemplate="%{text:,}", textposition="outside")
    _layout(fig_pp)
    fig_pp.update_layout(showlegend=False)

    # Municipio filtrado
    df_m = df_municipio.copy()
    if uf != "Todas":
        df_m = df_m[df_m["SG_UF_PROVA"] == uf]
    df_m = df_m[df_m["TOTAL_PARTICIPANTES"] >= min_part]

    if df_m.empty:
        _vazio = go.Figure()
        _vazio.update_layout(
            template="plotly_white",
            annotations=[dict(text="Sem municípios com esses critérios",
                              showarrow=False, x=.5, y=.5,
                              xref="paper", yref="paper",
                              font=dict(size=13, color=CINZA_TEXTO))]
        )
        return fig_pm, fig_pp, _vazio, _vazio

    # Scatter
    fig_sc = px.scatter(
        df_m,
        x="POPULACAO_MUNICIPIO",
        y="MEDIA_GERAL",
        size="TOTAL_PARTICIPANTES",
        color="PORTE_MUNICIPIO",
        hover_name="NO_MUNICIPIO_PROVA",
        hover_data={"SG_UF_PROVA": True, "TOTAL_PARTICIPANTES": True,
                    "POPULACAO_MUNICIPIO": True, "PORTE_MUNICIPIO": False},
        color_discrete_sequence=PALETA_SEQ,
        size_max=40,
        log_x=True,
        labels={"POPULACAO_MUNICIPIO": "População (escala log)", "MEDIA_GERAL": "Média Geral"},
        category_orders={"PORTE_MUNICIPIO": ORDEM_PORTE},
    )
    _layout(fig_sc)

    # Top 15 municípios
    top15 = (
        df_m.sort_values("MEDIA_GERAL", ascending=False)
        .head(15)
        .sort_values("MEDIA_GERAL")
    )
    top15["LABEL"] = top15["NO_MUNICIPIO_PROVA"] + " - " + top15["SG_UF_PROVA"]
    fig_top = px.bar(
        top15, x="MEDIA_GERAL", y="LABEL",
        orientation="h",
        color="MEDIA_GERAL",
        color_continuous_scale=["#bfdbfe", AZUL_MEDIO, AZUL_ESCURO],
        text="MEDIA_GERAL",
        labels={"MEDIA_GERAL": "Média Geral", "LABEL": ""},
    )
    fig_top.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    _layout(fig_top)
    fig_top.update_layout(coloraxis_showscale=False)

    return fig_pm, fig_pp, fig_sc, fig_top


# ─────────────────────────────────────────────
#  EXECUÇÃO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)