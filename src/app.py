from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc


# ── Caminhos ──────────────────────────────────────────────────────────────────

PASTA_ANALYTICS = Path(__file__).resolve().parents[1] / "data" / "analytics"


# ── Paleta ────────────────────────────────────────────────────────────────────

AZUL_ESCURO = "#1a2e4a"
AZUL_MEDIO  = "#2563eb"
VERDE_AGUA  = "#0d9488"
LARANJA     = "#f97316"
CINZA_CLARO = "#f1f5f9"
CINZA_TEXTO = "#64748b"
BRANCO      = "#ffffff"

PALETA_SEQ = [AZUL_ESCURO, AZUL_MEDIO, VERDE_AGUA, "#38bdf8", "#7dd3fc"]
PALETA_CAT = [AZUL_MEDIO, VERDE_AGUA, LARANJA, "#8b5cf6", "#ec4899"]


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

# Amostras pré-processadas para gráficos pesados
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


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _vazio_fig(msg="Sem dados para os filtros selecionados"):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        annotations=[dict(
            text=msg, showarrow=False, x=.5, y=.5,
            xref="paper", yref="paper",
            font=dict(size=14, color=CINZA_TEXTO),
        )],
    )
    return fig


def _card(icone, titulo, valor, subtitulo, cor=AZUL_MEDIO):
    return dbc.Card(
        dbc.CardBody(
            html.Div([
                html.Span(icone, style={"fontSize": "1.6rem"}),
                html.Div([
                    html.P(titulo, className="mb-0",
                           style={"fontSize": ".7rem", "color": CINZA_TEXTO,
                                  "textTransform": "uppercase", "letterSpacing": "1px"}),
                    html.H4(valor, className="mb-0 fw-bold", style={"color": AZUL_ESCURO}),
                    html.P(subtitulo, className="mb-0",
                           style={"fontSize": ".75rem", "color": CINZA_TEXTO}),
                ], className="ms-3"),
            ], className="d-flex align-items-center"),
        ),
        className="shadow-sm border-0 h-100",
        style={"borderLeft": f"4px solid {cor} !important", "borderRadius": "10px"},
    )


def _aplicar_filtros(df, escola, internet, renda):
    """Aplica os filtros comuns da aba Socioeconômico."""
    if escola != "Todos" and "TIPO_ESCOLA" in df.columns:
        df = df[df["TIPO_ESCOLA"] == escola]
    if internet != "Todos" and "ACESSO_INTERNET" in df.columns:
        df = df[df["ACESSO_INTERNET"] == internet]
    if renda != "Todas" and "RENDA_FAMILIAR" in df.columns:
        df = df[df["RENDA_FAMILIAR"] == renda]
    return df


def _barras_renda(df_ag):
    """Gráfico de barras duplas (Objetivas × Redação) por renda — reutilizado em duas abas."""
    fig = go.Figure([
        go.Bar(
            name="Objetivas",
            y=df_ag["RENDA_FAMILIAR"].astype(str),
            x=df_ag["MEDIA_OBJETIVAS"],
            orientation="h",
            marker_color=AZUL_MEDIO,
        ),
        go.Bar(
            name="Redação",
            y=df_ag["RENDA_FAMILIAR"].astype(str),
            x=df_ag["MEDIA_REDACAO"],
            orientation="h",
            marker_color=VERDE_AGUA,
        ),
    ])
    fig.update_layout(barmode="group", xaxis_range=[350, 850])
    _layout(fig)
    fig.update_layout(
        legend=dict(
            orientation="h",
            x=1, xanchor="right",
            y=0, yanchor="top",
            bgcolor="rgba(255,255,255,0.8)",
        ),
        margin=dict(l=40, r=20, t=20, b=50),
    )
    return fig


# ── Layouts das abas ──────────────────────────────────────────────────────────

def _grafico_card(titulo, subtitulo=None, graph_id=None, altura=280):
    corpo = [html.H6(titulo, className="fw-bold mb-1", style={"color": AZUL_ESCURO})]
    if subtitulo:
        corpo.append(html.P(subtitulo, style={"fontSize": ".75rem", "color": CINZA_TEXTO}))
    if graph_id:
        corpo.append(dcc.Graph(id=graph_id, config={"displayModeBar": False},
                               style={"height": f"{altura}px"}))
    return dbc.Card(dbc.CardBody(corpo), className="shadow-sm border-0 h-100")


def layout_visao_geral():
    r = df_resumo.iloc[0]
    cards = [
        ("👥", "Participantes", f"{int(r['TOTAL_PARTICIPANTES']):,}".replace(",", "."),
         "Candidatos com nota válida", AZUL_MEDIO),
        ("📊", "Média Geral",     f"{r['MEDIA_GERAL']:.1f}",      "Todas as provas",     VERDE_AGUA),
        ("✍️", "Média Redação",  f"{r['MEDIA_REDACAO']:.1f}",    "Competência escrita", LARANJA),
        ("📐", "Média Objetivas", f"{r['MEDIA_OBJETIVAS']:.1f}",  "CN + CH + LC + MT",   AZUL_ESCURO),
        ("🌐", "Com Internet",   f"{r['PERCENTUAL_COM_INTERNET']:.1f}%", "Acesso residencial", VERDE_AGUA),
        ("🏙️", "Municípios",    f"{int(r['TOTAL_MUNICIPIOS_PROVA'])}",  "Com ao menos 1 prova", AZUL_MEDIO),
    ]
    return dbc.Container(fluid=True, children=[
        html.Div([
            html.H4("Visão Geral Executiva",
                    style={"fontFamily": "'Playfair Display', serif", "color": AZUL_ESCURO}),
            html.P("Panorama nacional dos candidatos ao ENEM 2022.",
                   style={"color": CINZA_TEXTO, "fontSize": ".9rem"}),
        ], className="mb-4"),

        dbc.Row([dbc.Col(_card(*c), md=2) for c in cards], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(_grafico_card("Participantes por tipo de escola",
                                  graph_id="g1-escola"), md=5),
            dbc.Col(_grafico_card("Desempenho médio × acesso à internet",
                                  graph_id="g1-internet"), md=7),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(_grafico_card(
                "Média geral, redação e provas objetivas por renda familiar",
                graph_id="g1-renda", altura=420,
            ), md=12),
        ], className="mb-4 g-3"),
    ])


def layout_socioeconomico():
    rendas_disp = [r for r in ORDEM_RENDA
                   if r in df_transformado["RENDA_FAMILIAR"].dropna().unique()]

    filtros = dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col([
            html.Label("Tipo de escola", className="fw-bold",
                       style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
            dcc.Dropdown(
                id="f2-escola",
                options=[{"label": "Todos", "value": "Todos"}] + [
                    {"label": v, "value": v}
                    for v in df_transformado["TIPO_ESCOLA"].dropna().unique()
                    if v != "Não respondeu"
                ],
                value="Todos", clearable=False,
            ),
        ], md=4),
        dbc.Col([
            html.Label("Acesso à internet", className="fw-bold",
                       style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
            dcc.Dropdown(
                id="f2-internet",
                options=[{"label": l, "value": v} for l, v in
                         [("Todos", "Todos"), ("Sim", "Sim"), ("Não", "Não")]],
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
            ),
        ], md=4),
    ])), className="shadow-sm border-0 mb-4")

    return dbc.Container(fluid=True, children=[
        html.Div([
            html.H4("Desigualdade Socioeconômica",
                    style={"fontFamily": "'Playfair Display', serif", "color": AZUL_ESCURO}),
            html.P("Explore como renda, escola e conectividade moldam o desempenho.",
                   style={"color": CINZA_TEXTO, "fontSize": ".9rem"}),
        ], className="mb-4"),
        filtros,
        dbc.Row([
            dbc.Col(_grafico_card(
                "Distribuição da nota de redação por renda",
                "Boxplot — mediana, quartis e outliers",
                "g2-boxplot", altura=400,
            ), md=7),
            dbc.Col(_grafico_card(
                "Objetivas vs Redação por renda",
                "Barras agrupadas — médias comparadas",
                "g2-barras-duplas", altura=400,
            ), md=5),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(_grafico_card(
                "Concentração: provas objetivas × redação",
                "Mapa de densidade — regiões mais escuras = maior concentração de candidatos",
                "g2-heatmap", altura=350,
            ), md=12),
        ], className="mb-4 g-3"),
    ])


def layout_municipios():
    ufs = sorted(df_municipio["SG_UF_PROVA"].dropna().unique())

    filtros = dbc.Card(dbc.CardBody(dbc.Row([
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
            html.Label("Mínimo de participantes por município", className="fw-bold",
                       style={"fontSize": ".8rem", "color": CINZA_TEXTO}),
            dcc.Slider(
                id="f3-min-part", min=50, max=2000, step=50, value=200,
                marks={50: "50", 500: "500", 1000: "1k", 2000: "2k"},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], md=8),
    ])), className="shadow-sm border-0 mb-4")

    return dbc.Container(fluid=True, children=[
        html.Div([
            html.H4("Contexto Municipal & IBGE",
                    style={"fontFamily": "'Playfair Display', serif", "color": AZUL_ESCURO}),
            html.P("Desempenho cruzado com dados populacionais do IBGE 2022.",
                   style={"color": CINZA_TEXTO, "fontSize": ".9rem"}),
        ], className="mb-4"),
        filtros,
        dbc.Row([
            dbc.Col(_grafico_card(
                "Média geral por porte do município",
                "Classificação populacional pelo IBGE 2022",
                "g3-porte-media",
            ), md=6),
            dbc.Col(_grafico_card(
                "Participantes por porte do município",
                "Concentração de candidatos por tamanho de cidade",
                "g3-porte-part",
            ), md=6),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(_grafico_card(
                "População do município × Média geral",
                "Tamanho do ponto = total de participantes · Cor = porte",
                "g3-scatter", altura=380,
            ), md=7),
            dbc.Col(_grafico_card(
                "Top 15 municípios — maior média geral",
                "Apenas municípios com mínimo de participantes definido no filtro",
                "g3-top-municipios", altura=380,
            ), md=5),
        ], className="mb-4 g-3"),
    ])


# ── App ───────────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700"
        "&family=DM+Sans:wght@400;500&display=swap",
    ],
    suppress_callback_exceptions=True,
)
server = app.server

_HEADER = {
    "background": f"linear-gradient(135deg, {AZUL_ESCURO} 0%, #0f3460 100%)",
    "padding": "2rem 2.5rem 1.5rem",
}

app.layout = html.Div([
    html.Div([
        html.H1("O Raio-X da Desigualdade no ENEM",
                style={"fontFamily": "'Playfair Display', serif",
                       "color": BRANCO, "fontSize": "2rem", "marginBottom": ".3rem"}),
        html.P(
            "Microdados ENEM 2022 integrados a indicadores socioeconômicos do IBGE — "
            "análise de desempenho, renda familiar, acesso à internet e contexto municipal.",
            style={"color": "rgba(255,255,255,.7)", "fontSize": ".9rem", "margin": 0},
        ),
    ], style=_HEADER),

    dbc.Tabs([
        dbc.Tab(layout_visao_geral(),     label="① Visão Geral",      tab_id="tab1",
                label_style={"fontFamily": "'DM Sans', sans-serif", "fontWeight": "500"}),
        dbc.Tab(layout_socioeconomico(),  label="② Socioeconômico",   tab_id="tab2",
                label_style={"fontFamily": "'DM Sans', sans-serif", "fontWeight": "500"}),
        dbc.Tab(layout_municipios(),      label="③ Municípios & IBGE", tab_id="tab3",
                label_style={"fontFamily": "'DM Sans', sans-serif", "fontWeight": "500"}),
    ], active_tab="tab1",
       style={"backgroundColor": CINZA_CLARO, "paddingLeft": "1.5rem",
              "borderBottom": f"3px solid {AZUL_MEDIO}"}),

], style={"fontFamily": "'DM Sans', sans-serif", "backgroundColor": CINZA_CLARO,
          "minHeight": "100vh"})


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("g1-escola",   "figure"),
    Output("g1-internet", "figure"),
    Output("g1-renda",    "figure"),
    Input("g1-escola",    "id"),
)
def montar_visao_geral(_):
    # Pizza — participantes por tipo de escola
    fig_escola = px.pie(
        df_escola[df_escola["TIPO_ESCOLA"] != "Não respondeu"],
        names="TIPO_ESCOLA", values="TOTAL_PARTICIPANTES",
        color_discrete_sequence=PALETA_CAT, hole=0.55,
    )
    fig_escola.update_traces(textposition="outside", textinfo="percent+label")
    _layout(fig_escola)
    fig_escola.update_layout(showlegend=False, margin=dict(l=10, r=10, t=15, b=10))

    # Barras horizontais — média por acesso à internet
    fig_internet = px.bar(
        df_internet.sort_values("MEDIA_GERAL"),
        x="MEDIA_GERAL", y="ACESSO_INTERNET", orientation="h",
        color="ACESSO_INTERNET",
        color_discrete_map={"Sim": VERDE_AGUA, "Não": LARANJA},
        text="MEDIA_GERAL",
    )
    fig_internet.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_internet.update_xaxes(range=[400, 600])
    _layout(fig_internet)
    fig_internet.update_layout(showlegend=False)

    return fig_escola, fig_internet, _barras_renda(df_renda)


@app.callback(
    Output("g2-boxplot",       "figure"),
    Output("g2-barras-duplas", "figure"),
    Output("g2-heatmap",       "figure"),
    Input("f2-escola",   "value"),
    Input("f2-internet", "value"),
    Input("f2-renda",    "value"),
)
def atualizar_socioeconomico(escola, internet, renda):
    # Boxplot — amostra filtrada
    dados_box = _aplicar_filtros(DF_BOX_SAMPLE.copy(), escola, internet, renda)
    dados_box = dados_box.dropna(subset=["RENDA_FAMILIAR", "NU_NOTA_REDACAO"])
    dados_box["RENDA_FAMILIAR"] = pd.Categorical(
        dados_box["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
    )
    dados_box = dados_box.sort_values("RENDA_FAMILIAR")

    if dados_box.empty:
        fig_box = _vazio_fig()
    else:
        fig_box = px.box(
            dados_box, y="RENDA_FAMILIAR", x="NU_NOTA_REDACAO", orientation="h",
            color_discrete_sequence=[AZUL_MEDIO],
            labels={"NU_NOTA_REDACAO": "Nota de Redação", "RENDA_FAMILIAR": ""},
        )
        _layout(fig_box)
        fig_box.update_layout(showlegend=False)

    # Barras duplas — agrega a partir da amostra filtrada para refletir os filtros
    dados_bar = _aplicar_filtros(DF_BOX_SAMPLE.copy(), escola, internet, renda)
    if dados_bar.empty:
        fig_bar = _vazio_fig()
    else:
        df_ag_filtrado = (
            dados_bar
            .dropna(subset=["RENDA_FAMILIAR", "MEDIA_OBJETIVAS", "NU_NOTA_REDACAO"])
            .groupby("RENDA_FAMILIAR", observed=True)
            .agg(MEDIA_OBJETIVAS=("MEDIA_OBJETIVAS", "mean"),
                 MEDIA_REDACAO=("NU_NOTA_REDACAO", "mean"))
            .reset_index()
        )
        df_ag_filtrado["RENDA_FAMILIAR"] = pd.Categorical(
            df_ag_filtrado["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True
        )
        df_ag_filtrado = df_ag_filtrado.sort_values("RENDA_FAMILIAR")
        fig_bar = _barras_renda(df_ag_filtrado)

    # Heatmap de densidade — amostra filtrada
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
            dados_heat,
            x="MEDIA_OBJETIVAS", y="NU_NOTA_REDACAO",
            nbinsx=50, nbinsy=50,
            color_continuous_scale="Blues",
            labels={
                "MEDIA_OBJETIVAS":   "Média das Provas Objetivas",
                "NU_NOTA_REDACAO":   "Nota de Redação",
                "count":             "Quantidade de candidatos",
            },
        )
        fig_heat.update_xaxes(range=[300, 750])
        fig_heat.update_yaxes(range=[300, 1000])
        fig_heat.update_traces(hovertemplate=(
            "Média objetivas: %{x}<br>"
            "Nota redação: %{y}<br>"
            "Quantidade na faixa: %{z}<extra></extra>"
        ))
        fig_heat.update_layout(
            coloraxis_colorbar_title="Qtd.",
            bargap=0,
        )
        # ← _layout chamado uma única vez, com o título que inclui n=
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
    # Barras por porte — sempre global
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

    fig_pm = _porte_bar("MEDIA_GERAL",        "Média Geral",    "%{text:.1f}", [450, 600])
    fig_pp = _porte_bar("TOTAL_PARTICIPANTES", "Participantes",  "%{text:,}")

    # Municípios filtrados
    df_m = df_municipio.copy()
    if uf != "Todas":
        df_m = df_m[df_m["SG_UF_PROVA"] == uf]
    df_m = df_m[df_m["TOTAL_PARTICIPANTES"] >= min_part]

    if df_m.empty:
        v = _vazio_fig("Sem municípios com esses critérios")
        return fig_pm, fig_pp, v, v

    fig_sc = px.scatter(
        df_m,
        x="POPULACAO_MUNICIPIO", y="MEDIA_GERAL",
        size="TOTAL_PARTICIPANTES",
        color="PORTE_MUNICIPIO",
        hover_name="NO_MUNICIPIO_PROVA",
        hover_data={"SG_UF_PROVA": True, "TOTAL_PARTICIPANTES": True,
                    "POPULACAO_MUNICIPIO": True, "PORTE_MUNICIPIO": False},
        color_discrete_sequence=PALETA_SEQ,
        size_max=40, log_x=True,
        labels={"POPULACAO_MUNICIPIO": "População (escala log)", "MEDIA_GERAL": "Média Geral"},
        category_orders={"PORTE_MUNICIPIO": ORDEM_PORTE},
    )
    _layout(fig_sc)

    top15 = (
        df_m.sort_values("MEDIA_GERAL", ascending=False).head(15)
        .sort_values("MEDIA_GERAL")
        .assign(LABEL=lambda d: d["NO_MUNICIPIO_PROVA"] + " - " + d["SG_UF_PROVA"])
    )
    fig_top = px.bar(
        top15, x="MEDIA_GERAL", y="LABEL", orientation="h",
        color="MEDIA_GERAL",
        color_continuous_scale=["#bfdbfe", AZUL_MEDIO, AZUL_ESCURO],
        text="MEDIA_GERAL",
        labels={"MEDIA_GERAL": "Média Geral", "LABEL": ""},
    )
    fig_top.update_traces(
        texttemplate="%{x:.1f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Média Geral: %{x:.1f}<extra></extra>",
    )
    _layout(fig_top)
    fig_top.update_layout(coloraxis_showscale=False)

    return fig_pm, fig_pp, fig_sc, fig_top


# ── Execução ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)