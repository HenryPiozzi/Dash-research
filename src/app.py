from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc



# CAMINHOS DO PROJETO

PASTA_RAIZ = Path(__file__).resolve().parents[1]
PASTA_PROCESSED = PASTA_RAIZ / "data" / "processed"

ARQUIVOS_DADOS = {
    "2022": PASTA_PROCESSED / "enem_2022_tratado.csv",
    "2023": PASTA_PROCESSED / "enem_2023_tratado.csv"
}

COR_PRINCIPAL = "#2c3e50"
COR_DESTAQUE = "#18bc9c"

# MAPAS DE TRADUÇÃO


MAPA_RENDA = {
    "A": "Nenhuma renda",
    "B": "Até 1 salário mínimo",
    "C": "1 a 1,5 salários",
    "D": "1,5 a 2 salários",
    "E": "2 a 2,5 salários",
    "F": "2,5 a 3 salários",
    "G": "3 a 4 salários",
    "H": "4 a 5 salários",
    "I": "5 a 6 salários",
    "J": "6 a 7 salários",
    "K": "7 a 8 salários",
    "L": "8 a 9 salários",
    "M": "9 a 10 salários",
    "N": "10 a 12 salários",
    "O": "12 a 15 salários",
    "P": "15 a 20 salários",
    "Q": "Acima de 20 salários"
}

ORDEM_RENDA = list(MAPA_RENDA.values())

MAPA_INTERNET = {
    "A": "Não",
    "B": "Sim"
}

MAPA_TIPO_ESCOLA = {
    1: "Não respondeu",
    2: "Pública",
    3: "Privada"
}

MAPA_DEPENDENCIA = {
    1: "Federal",
    2: "Estadual",
    3: "Municipal",
    4: "Privada"
}

MAPA_LOCALIZACAO = {
    1: "Urbana",
    2: "Rural"
}



# CARREGAMENTO E PREPARAÇÃO DOS DADOS


def carregar_dados():
    bases = []

    for ano, caminho in ARQUIVOS_DADOS.items():
        if caminho.exists():
            print(f"Lendo arquivo: {caminho}")
            df_temp = pd.read_csv(caminho, sep=";", encoding="utf-8")
            df_temp["ANO_BASE"] = ano
            bases.append(df_temp)
        else:
            print(f"Aviso: arquivo não encontrado: {caminho}")

    if not bases:
        raise FileNotFoundError("Nenhum arquivo tratado foi encontrado em data/processed.")

    df = pd.concat(bases, ignore_index=True)

    colunas_notas = [
        "NU_NOTA_CN",
        "NU_NOTA_CH",
        "NU_NOTA_LC",
        "NU_NOTA_MT",
        "NU_NOTA_REDACAO"
    ]

    for coluna in colunas_notas:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df["MEDIA_GERAL"] = df[colunas_notas].mean(axis=1)

    if "NU_IDADE" in df.columns:
        df["NU_IDADE"] = pd.to_numeric(df["NU_IDADE"], errors="coerce")

        df["FAIXA_ETARIA"] = pd.cut(
            df["NU_IDADE"],
            bins=[0, 17, 20, 25, 30, 40, 100],
            labels=[
                "Até 17",
                "18 a 20",
                "21 a 25",
                "26 a 30",
                "31 a 40",
                "Acima de 40"
            ]
        )

    if "Q006" in df.columns:
        df["RENDA_FAMILIAR"] = df["Q006"].map(MAPA_RENDA)

    if "Q025" in df.columns:
        df["ACESSO_INTERNET"] = df["Q025"].map(MAPA_INTERNET)

    if "TP_ESCOLA" in df.columns:
        df["TIPO_ESCOLA"] = df["TP_ESCOLA"].map(MAPA_TIPO_ESCOLA)

    if "TP_DEPENDENCIA_ADM_ESC" in df.columns:
        df["DEPENDENCIA_ESCOLA"] = df["TP_DEPENDENCIA_ADM_ESC"].map(MAPA_DEPENDENCIA)

    if "TP_LOCALIZACAO_ESC" in df.columns:
        df["LOCALIZACAO_ESCOLA"] = df["TP_LOCALIZACAO_ESC"].map(MAPA_LOCALIZACAO)
    
    df = df[df["TIPO_ESCOLA"] != "Não respondeu"]

    return df


df = carregar_dados()


def gerar_agregados_macro(dataframe):
    agregados = {}
    chaves = ["Todos"] + list(dataframe["ANO_BASE"].unique())
    
    for c in chaves:
        sub_df = dataframe if c == "Todos" else dataframe[dataframe["ANO_BASE"] == c]
        
        agregados[c] = {
            "total": len(sub_df),
            "media": sub_df["MEDIA_GERAL"].mean(),
            "renda_comum": sub_df["RENDA_FAMILIAR"].mode().iloc[0] if "RENDA_FAMILIAR" in sub_df.columns and not sub_df["RENDA_FAMILIAR"].dropna().empty else "N/A",
            "pct_internet": sub_df["ACESSO_INTERNET"].eq("Sim").mean() * 100 if "ACESSO_INTERNET" in sub_df.columns else 0,
            
            "df_escola": sub_df["TIPO_ESCOLA"].value_counts().reset_index(name="TOTAL"),
            
            "df_renda": sub_df.dropna(subset=["RENDA_FAMILIAR"]).groupby("RENDA_FAMILIAR", as_index=False)["MEDIA_GERAL"].mean(),
            
            "df_dependencia": sub_df.dropna(subset=["DEPENDENCIA_ESCOLA"]).groupby("DEPENDENCIA_ESCOLA", as_index=False)["MEDIA_GERAL"].mean().sort_values("MEDIA_GERAL", ascending=False)
        }
    return agregados


DADOS_AGREGADOS_DASH1 = gerar_agregados_macro(df)

# menor amostra de dispersão para o dash2
DF_SAMPLE_DASH2 = df.sample(min(len(df), 5000), random_state=42) if not df.empty else df

# APP


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True
)

server = app.server



# FUNÇÕES VISUAIS


def aplicar_layout_padrao(fig, titulo_limpo=""):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=30, t=50, b=50),
        title=dict(text=titulo_limpo, font=dict(size=15, color=COR_PRINCIPAL, family="sans-serif")),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=11, color="#7f8c8d")
    )
    return fig


def criar_card_indicador(titulo, valor, descricao):
    return dbc.Card(
        dbc.CardBody([
            html.H6(titulo, className="card-title text-muted small uppercase text-center"),
            html.H2(valor, className="fw-bold text-center my-2", style={"color": COR_PRINCIPAL}),
            html.P(descricao, className="mb-0 text-muted small text-center")
        ]),
        className="shadow-sm border-0 h-100"
    )


def figura_sem_dados():
    fig = go.Figure()
    fig.update_layout(template="plotly_white", title="Nenhum dado encontrado para os filtros.", xaxis_visible=False, yaxis_visible=False)
    return fig



# LAYOUTS DAS ABAS


def layout_visao_geral():
    anos_disponiveis = sorted(df["ANO_BASE"].dropna().unique())

    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3(
                                "Dashboard 1: Visão Geral do Desempenho",
                                className="mb-2 text-secondary fw-bold"
                            ),
                            html.P(
                                "Painel executivo com os principais indicadores da base analisada.",
                                className="text-muted"
                            )
                        ],
                        md=8
                    ),
                    dbc.Col(
                        [
                            html.Label("Filtrar ano Letivo:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filtro-ano-visao",
                                options=[{"label": "Todos", "value": "Todos"}] + [
                                    {"label": ano, "value": ano}
                                    for ano in anos_disponiveis
                                ],
                                value="Todos",
                                clearable=False
                            )
                        ],
                        md=4
                    )
                ],
                className="mb-4"
            ),

            dbc.Row(
                [
                    dbc.Col(html.Div(id="card-participantes"), md=3),
                    dbc.Col(html.Div(id="card-media-geral"), md=3),
                    dbc.Col(html.Div(id="card-renda-mais-comum"), md=3),
                    dbc.Col(html.Div(id="card-internet"), md=3),
                ],
                className="mb-4"
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Média geral por ano", className="text-secondary fw-bold"),
                                    dcc.Graph(id="grafico-media-ano")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Participantes por tipo de escola", className="text-secondary fw-bold"),
                                    dcc.Graph(id="grafico-tipo-escola")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=6
                    )
                ],
                className="mb-4"
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Média geral por renda familiar", className="text-secondary fw-bold"),
                                    dcc.Graph(id="grafico-renda")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Média por dependência administrativa da escola",
                                        className="text-secondary fw-bold"
                                    ),
                                    dcc.Graph(id="grafico-dependencia")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=6
                    )
                ],
                className="mb-4"
            )
        ]
    )


def layout_socioeconomico():
    anos_disponiveis = sorted(df["ANO_BASE"].dropna().unique())

    tipos_escola = sorted(
        df["TIPO_ESCOLA"].dropna().unique()
    ) if "TIPO_ESCOLA" in df.columns else []

    rendas = [
        renda for renda in ORDEM_RENDA
        if "RENDA_FAMILIAR" in df.columns and renda in df["RENDA_FAMILIAR"].dropna().unique()
    ]

    return dbc.Container(
        fluid=True,
        children=[
            html.H3("Dashboard 2: Exploração Socioeconômica", className="mb-2 text-secondary fw-bold"),
            html.P(
                "Análise interativa cruzando renda familiar, tipo de escola, acesso à internet e desempenho.",
                className="text-muted"
            ),

            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Ano:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filtro-ano-socio",
                                options=[{"label": "Todos", "value": "Todos"}] + [
                                    {"label": ano, "value": ano}
                                    for ano in anos_disponiveis
                                ],
                                value="Todos",
                                clearable=False
                            )
                        ],
                        md=4
                    ),
                    dbc.Col(
                        [
                            html.Label("Tipo de escola:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filtro-tipo-escola",
                                options=[{"label": "Todos", "value": "Todos"}] + [
                                    {"label": tipo, "value": tipo}
                                    for tipo in tipos_escola
                                ],
                                value="Todos",
                                clearable=False
                            )
                        ],
                        md=4
                    ),
                    dbc.Col(
                        [
                            html.Label("Renda familiar:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filtro-renda",
                                options=[{"label": "Todas", "value": "Todas"}] + [
                                    {"label": renda, "value": renda}
                                    for renda in rendas
                                ],
                                value="Todas",
                                clearable=False
                            )
                        ],
                        md=4
                    )
                ],
                className="mb-4"
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Relação entre média geral e redação",
                                        className="text-secondary fw-bold"
                                    ),
                                    dcc.Graph(id="grafico-dinamico-dispersao")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=12
                    )
                ],
                className="mb-4"
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Redação por faixa de renda",
                                        className="text-secondary fw-bold"
                                    ),
                                    dcc.Graph(id="grafico-box-renda-redacao")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Média geral por acesso à internet",
                                        className="text-secondary fw-bold"
                                    ),
                                    dcc.Graph(id="grafico-internet-media")
                                ]
                            ),
                            className="shadow-sm border-0"
                        ),
                        md=6
                    )
                ],
                className="mb-4"
            )
        ]
    )


def layout_escolas():
    return dbc.Container(
        fluid=True,
        children=[
            html.H3("Dashboard 3: Escola e Contexto", className="mb-2 text-secondary fw-bold"),
            html.P(
                "Aba reservada para cruzamentos com dados externos, como população municipal do IBGE ou investimentos públicos.",
                className="text-muted"
            ),
            dbc.Alert(
                "Próxima etapa: integrar a base do ENEM com dados do IBGE usando CO_MUNICIPIO_ESC.",
                color="info"
            )
        ]
    )



# LAYOUT PRINCIPAL


app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            dbc.Col(
                [
                    html.H1(
                        "O Raio-X da Desigualdade no ENEM",
                        className="text-center my-4 text-primary fw-bold", style={"color": COR_PRINCIPAL}
                    ),
                    html.P(
                        "Análise dos microdados do ENEM com foco em desempenho, renda familiar, acesso à internet e perfil escolar.",
                        className="text-center text-muted mb-4"
                    )
                ]
            )
        ),

        html.Hr(),

        dbc.Tabs(
            [
                dbc.Tab(
                    layout_visao_geral(),
                    label="Dashboard 1 — Visão Geral",
                    tab_id="tab-visao-geral"
                ),
                dbc.Tab(
                    layout_socioeconomico(),
                    label="Dashboard 2 — Perfil Socioeconômico",
                    tab_id="tab-socioeconomico"
                ),
                dbc.Tab(
                    layout_escolas(),
                    label="Dashboard 3 — Escola e Contexto",
                    tab_id="tab-escolas"
                ),
            ],
            active_tab="tab-visao-geral",
            className="mb-4"
        )
    ],
    className="px-4"
)



# CALLBACK — DASHBOARD 1


@app.callback(
    Output("card-participantes", "children"),
    Output("card-media-geral", "children"),
    Output("card-renda-mais-comum", "children"),
    Output("card-internet", "children"),
    Output("grafico-media-ano", "figure"),
    Output("grafico-tipo-escola", "figure"),
    Output("grafico-renda", "figure"),
    Output("grafico-dependencia", "figure"),
    Input("filtro-ano-visao", "value")
)
def atualizar_visao_geral(ano_selecionado):

    cache = DADOS_AGREGADOS_DASH1[ano_selecionado]

    card_participantes = criar_card_indicador("Amostra Analisada", f"{cache['total']:,.0f}".replace(",", "."), "Total de candidatos")
    card_media = criar_card_indicador("Nota Média Geral", f"{cache['media']:.1f}", "Desempenho nacional unificado")
    card_renda = criar_card_indicador("Renda Predominante", cache["renda_comum"], "Moda socioeconômica familiar")
    card_internet = criar_card_indicador("Acesso à Internet", f"{cache['pct_internet']:.1f}%", "Candidatos conectados em casa")

    # grafico1 - Evolução Anual
    df_media_ano = df.groupby("ANO_BASE", as_index=False)["MEDIA_GERAL"].mean()
    fig_media_ano = px.bar(df_media_ano, x="ANO_BASE", y="MEDIA_GERAL", text_auto=".1f", color_discrete_sequence=[COR_PRINCIPAL])
    fig_media_ano.update_yaxes(range=[400, 650])

    # grafico2 - Tipo de Escola
    fig_tipo_escola = px.pie(cache["df_escola"], names="TIPO_ESCOLA", values="TOTAL", hole=0.5, color_discrete_sequence=[COR_PRINCIPAL, COR_DESTAQUE])
    aplicar_layout_padrao(fig_tipo_escola, "Proporção de Alunos por Rede de Ensino")

    # grafico3 - storytelling aplicado
    df_renda = cache["df_renda"].copy()
    df_renda["RENDA_FAMILIAR"] = pd.Categorical(df_renda["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True)
    df_renda = df_renda.sort_values("RENDA_FAMILIAR")
    
    fig_renda = px.bar(df_renda, x="MEDIA_GERAL", y="RENDA_FAMILIAR", orientation="h", color_discrete_sequence=[COR_PRINCIPAL])
    fig_renda.update_xaxes(range=[350, 680])
    aplicar_layout_padrao(fig_renda, "Média Geral por Faixa de Renda")

    # grafico4 - dependencia administrativa
    fig_dependencia = px.bar(cache["df_dependencia"], x="DEPENDENCIA_ESCOLA", y="MEDIA_GERAL", text_auto=".1f", color_discrete_sequence=[COR_DESTAQUE])
    fig_dependencia.update_yaxes(range=[400, 650])
    aplicar_layout_padrao(fig_dependencia, "Desempenho Médio por Dependência Administrativa")

    return card_participantes, card_media, card_renda, card_internet, fig_media_ano, fig_tipo_escola, fig_renda, fig_dependencia



# CALLBACK — DASHBOARD 2


@app.callback(
    Output("grafico-dinamico-dispersao", "figure"),
    Output("grafico-box-renda-redacao", "figure"),
    Output("grafico-internet-media", "figure"),
    Input("filtro-ano-socio", "value"),
    Input("filtro-tipo-escola", "value"),
    Input("filtro-renda", "value")
)
def atualizar_dashboard_socioeconomico(ano, tipo_escola, renda):
    dados = df.copy()

    if ano != "Todos":
        dados = dados[dados["ANO_BASE"] == ano]

    if tipo_escola != "Todos" and "TIPO_ESCOLA" in dados.columns:
        dados = dados[dados["TIPO_ESCOLA"] == tipo_escola]

    if renda != "Todas" and "RENDA_FAMILIAR" in dados.columns:
        dados = dados[dados["RENDA_FAMILIAR"] == renda]

    if dados.empty:
        fig_vazia = figura_sem_dados()
        return fig_vazia, fig_vazia, fig_vazia

    # grafico1 - mapa de densidade dinâmico
    fig_dispersao = px.density_heatmap(
        dados, 
        x="MEDIA_GERAL", 
        y="NU_NOTA_REDACAO",
        nbinsx=40,
        nbinsy=40,
        color_continuous_scale="Blues", # <-- A mágica visual acontece aqui
        labels={"MEDIA_GERAL": "Média do Candidato", "NU_NOTA_REDACAO": "Nota de Redação"}
    )
    fig_dispersao = aplicar_layout_padrao(fig_dispersao, "Concentração: Média Geral vs Redação")

    # grafico2 - Boxplot de Renda Horizontal
    dados_box = dados.dropna(subset=["RENDA_FAMILIAR", "NU_NOTA_REDACAO"]).copy()
    dados_box["RENDA_FAMILIAR"] = pd.Categorical(dados_box["RENDA_FAMILIAR"], categories=ORDEM_RENDA, ordered=True)
    dados_box = dados_box.sort_values("RENDA_FAMILIAR")
    
    fig_box = px.box(dados_box, y="RENDA_FAMILIAR", x="NU_NOTA_REDACAO", orientation="h", color_discrete_sequence=[COR_DESTAQUE])
    aplicar_layout_padrao(fig_box, "Dispersão e Quartis da Nota de Redação por Renda")

    # grafico3 - filtro de internet
    df_internet = dados.dropna(subset=["ACESSO_INTERNET"]).groupby("ACESSO_INTERNET", as_index=False)["MEDIA_GERAL"].mean()
    fig_internet = px.bar(df_internet, x="ACESSO_INTERNET", y="MEDIA_GERAL", text_auto=".1f", color_discrete_sequence=[COR_PRINCIPAL])
    fig_internet.update_yaxes(range=[400, 650])
    aplicar_layout_padrao(fig_internet, "Impacto Conectividade: Média por Presença de Internet")

    return fig_dispersao, fig_box, fig_internet



# EXECUÇÃO


if __name__ == "__main__":
    app.run(debug=True)