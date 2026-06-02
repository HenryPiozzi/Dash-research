import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# DADOS TESTE (mudar para pd.read_csv)
data_teste = {
    'TIPO_ESCOLA': ['Pública', 'Pública', 'Privada', 'Privada', 'Pública'],
    'FAIXA_RENDA': ['Baixa', 'Média', 'Alta', 'Alta', 'Baixa'],
    'INTERNET': ['Sim', 'Não', 'Sim', 'Sim', 'Não'],
    'NOTA_MEDIA': [520, 480, 690, 710, 450],
    'NU_NOTA_REDACAO': [600, 440, 850, 920, 500],
    'POPULACAO': [100000, 50000, 500000, 500000, 30000]
}
df = pd.DataFrame(data_teste)

def criar_grafico_estatico_1(dataframe):
    fig = px.bar(dataframe, x='INTERNET', y='NOTA_MEDIA', title="[Gráfico 1] Título Aqui", barmode='group')
    return fig

def criar_grafico_estatico_2(dataframe):
    fig = px.box(dataframe, x='FAIXA_RENDA', y='NU_NOTA_REDACAO', title="[Gráfico 2] Título Aqui")
    return fig

def criar_grafico_dinamico(dataframe_filtrado):
    if dataframe_filtrado.empty:
        fig = go.Figure()
        fig.update_layout(title="Nenhum dado encontrado para estes filtros.", xaxis_visible=False, yaxis_visible=False)
        return fig
        
    fig = px.scatter(
        dataframe_filtrado, 
        x="NOTA_MEDIA", 
        y="NU_NOTA_REDACAO",
        title="[Gráfico Dinâmico] Reage aos Filtros",
    )
    return fig

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    
    # Cabeçalho
    dbc.Row([
        dbc.Col(html.H1("O Raio-X da Desigualdade no ENEM", className="text-center my-4 text-primary"), width=12)
    ]),
    html.Hr(),
    
    # DASHBOARD 1: VISÃO GERAL
    html.H3("Dashboard 1: Visão Geral do Desempenho", className="mb-3 text-secondary"),
    
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Amostra Analisada", className="card-title text-muted"),
            html.H2(id="card-amostra", children=f"{len(df)} candidatos", className="text-info")
        ])), width=6),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Nota Média Geral", className="card-title text-muted"),
            html.H2(id="card-media", children=f"{df['NOTA_MEDIA'].mean():.1f}", className="text-success")
        ])), width=6),
    ], className="mb-4"),
    
    # Espaço gráficos estáticos (Chamando as funções)
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-estatico-1', figure=criar_grafico_estatico_1(df)), width=6),
        dbc.Col(dcc.Graph(id='grafico-estatico-2', figure=criar_grafico_estatico_2(df)), width=6),
    ], className="mb-5"),
    
    html.Hr(),
    
    # DASHBOARD 2: EXPLORAÇÃO INTERATIVA
    html.H3("Dashboard 2: Exploração Detalhada", className="mb-3 text-secondary"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Filtro 1 (Escola):"),
            dcc.Dropdown(
                id='filtro-1',
                options=[{'label': x, 'value': x} for x in df['TIPO_ESCOLA'].unique()],
                value=df['TIPO_ESCOLA'].unique()[0], 
                clearable=False
            )
        ], width=6),
        
        dbc.Col([
            html.Label("Filtro 2 (Renda):"),
            dcc.Dropdown(
                id='filtro-2',
                options=[{'label': x, 'value': x} for x in df['FAIXA_RENDA'].unique()],
                value=df['FAIXA_RENDA'].unique()[0],
                clearable=False
            )
        ], width=6),
    ], className="mb-4"),
    
    # Espaço gráfico dinâmico
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-dinamico-principal'), width=12)
    ])

], fluid=True)


@app.callback(
    Output('grafico-dinamico-principal', 'figure'),
    Input('filtro-1', 'value'),
    Input('filtro-2', 'value')
)
def atualizar_dashboard_interativo(valor_filtro_1, valor_filtro_2):
    # Aplica a lógica de filtragem
    df_filtrado = df[(df['TIPO_ESCOLA'] == valor_filtro_1) & (df['FAIXA_RENDA'] == valor_filtro_2)]

    figura_atualizada = criar_grafico_dinamico(df_filtrado)
    
    return figura_atualizada


if __name__ == '__main__':
    app.run(debug=True)