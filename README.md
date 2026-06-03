# Desigualdade no ENEM - Dashboard Interativo

Este repositório contém o projeto final da disciplina de Estudos Avançados de Banco de Dados. O objetivo do trabalho é analisar os microdados do ENEM integrados a dados populacionais do IBGE, buscando identificar padrões, correlações e desigualdades no desempenho educacional brasileiro.

O projeto utiliza Python para todo o pipeline de dados, incluindo coleta, limpeza, transformação, integração, agregação e visualização. A interface final foi desenvolvida com Dash e Plotly.

---

## Objetivo do Projeto

O dashboard busca responder perguntas como:

- Como a renda familiar se relaciona com o desempenho no ENEM?
- Existe diferença de desempenho entre candidatos com e sem acesso à internet?
- O tipo de escola influencia a média geral e a nota de redação?
- Como o porte populacional do município se relaciona com o desempenho dos candidatos?
- Quais estados ou municípios apresentam maiores médias ou maior concentração de participantes?

---

## Tecnologias Utilizadas

- Python
- Pandas
- Plotly
- Dash
- Dash Bootstrap Components
- Requests
- Jupyter Notebook
- API do IBGE
- Microdados do ENEM

---

## Estrutura do Repositório

O projeto está organizado da seguinte forma:

```text
ENEM-Data-Dashboard/
│
├── data/
│   │
│   ├── analytics/
│   │   ├── agregado_outliers_uf_2022.csv
│   │   ├── agregado_porte_municipio_2022.csv
│   │   ├── agregado_renda_2022.csv
│   │   ├── agregado_tipo_escola_2022.csv
│   │   ├── enem_2022_ibge_integrado.csv
│   │   ├── enem_2022_ibge_transformado.csv
│   │   ├── enem_2022_limpo.csv
│   │   ├── enem_2023_limpo.csv
│   │   ├── ibge_populacao_municipios_2022_limpo.csv
│   │   └── resumo_geral_2022.csv
│   │
│   ├── processed/
│   │   └── Arquivos processados a partir dos microdados originais do ENEM.
│   │
│   ├── raw/
│   │   └── Arquivos brutos coletados ou baixados automaticamente.
│   │
│   ├── zipped/
│   │   └── Arquivos compactados utilizados para armazenamento e transporte.
│   │
│   └── uf_brasil.geojson
│
├── notebooks/
│   ├── data/
│   │   └── Arquivos auxiliares utilizados durante a execução dos notebooks.
│   │
│   ├── 01_preparacao_dados.ipynb
│   ├── 02_transformação_dados.ipynb
│   ├── 03_tabela_apresentacao.ipynb
│   └── mapa_uf.png
│
├── src/
│   ├── app.py
│   ├── data_processor.py
│   ├── enem_collector.py
│   ├── outliers_estado.py
│   └── zip_processed.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Descrição dos Principais Arquivos

### `src/enem_collector.py`

Script responsável pela coleta dos microdados do ENEM. Ele realiza o download dos arquivos necessários e organiza os dados brutos dentro da estrutura do projeto.

### `src/data_processor.py`

Script responsável por processar os microdados do ENEM. Ele seleciona as colunas necessárias, trata os arquivos brutos e gera bases intermediárias para uso nos notebooks.

### `notebooks/01_preparacao_dados.ipynb`

Notebook responsável pela preparação inicial dos dados. Nele são realizadas etapas como:

- coleta dos dados populacionais do IBGE;
- leitura dos dados processados do ENEM;
- limpeza dos dados do ENEM;
- limpeza dos dados do IBGE;
- tratamento de valores ausentes;
- remoção de inconsistências;
- padronização de campos;
- integração entre ENEM e IBGE;
- concatenação e organização das bases limpas.

### `notebooks/02_transformação_dados.ipynb`

Notebook responsável pela transformação dos dados. Nele são realizadas etapas como:

- criação de novas variáveis;
- cálculo da média geral;
- cálculo da média das provas objetivas;
- cálculo de diferenças entre grupos;
- agregações por renda familiar;
- agregações por tipo de escola;
- agregações por porte de município;
- agregações por UF;
- geração dos arquivos finais utilizados pelo dashboard.

### `notebooks/03_tabela_apresentacao.ipynb`

Notebook auxiliar utilizado para gerar tabelas e informações utilizadas na apresentação do projeto.

### `src/app.py`

Arquivo principal do dashboard. Ele carrega os arquivos tratados e transformados da pasta `data/analytics/` e gera a interface interativa em Dash.

### `src/outliers_estado.py`

Script auxiliar utilizado para análise de outliers por estado.

### `src/zip_processed.py`

Script auxiliar para compactação e organização de arquivos processados.

### `data/analytics/`

Pasta que contém as bases finais utilizadas pelo dashboard, incluindo bases limpas, integradas, transformadas e agregadas.

---

## Como Rodar o Projeto

Siga os passos abaixo para executar o projeto localmente.

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd ENEM-Data-Dashboard
```

### 2. Criar o ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

---

## Pipeline de Execução

Para reconstruir todo o projeto desde a coleta até o dashboard, execute os arquivos na seguinte ordem.

---

### 1. Coletar os dados do ENEM

Execute o script:

```bash
python src/enem_collector.py
```

Esse script é responsável por baixar/coletar os microdados do ENEM e armazená-los na estrutura do projeto.

---

### 2. Processar os dados do ENEM

Depois da coleta, execute:

```bash
python src/data_processor.py
```

Esse script processa os arquivos brutos do ENEM, seleciona as colunas necessárias e gera bases intermediárias para uso nos notebooks.

---

### 3. Rodar o notebook de preparação dos dados

Abra e execute todas as células do notebook:

```text
notebooks/01_preparacao_dados.ipynb
```

Esse notebook realiza:

- coleta dos dados populacionais do IBGE;
- tratamento dos dados do ENEM;
- tratamento dos dados do IBGE;
- padronização de formatos;
- tratamento de valores ausentes;
- remoção de inconsistências;
- integração entre ENEM e IBGE;
- concatenação dos dados;
- geração das bases limpas.

---

### 4. Rodar o notebook de transformação dos dados

Depois, execute todas as células do notebook:

```text
notebooks/02_transformação_dados.ipynb
```

Esse notebook realiza:

- criação de novas variáveis;
- cálculo da média geral;
- cálculo da média das provas objetivas;
- cálculo de indicadores;
- agregações por renda familiar;
- agregações por tipo de escola;
- agregações por porte de município;
- agregações por UF;
- geração dos arquivos finais na pasta `data/analytics/`.

---

### 5. Executar o dashboard

Após a geração dos arquivos finais, execute:

```bash
python src/app.py
```

O terminal exibirá um endereço local semelhante a:

```text
http://127.0.0.1:8050/
```

Abra esse endereço no navegador para acessar o dashboard.

---

## Ordem Resumida de Execução

```text
1. python src/enem_collector.py
2. python src/data_processor.py
3. Executar notebooks/01_preparacao_dados.ipynb
4. Executar notebooks/02_transformação_dados.ipynb
5. python src/app.py
```

---

## Execução Direta do Dashboard

Caso os arquivos finais da pasta `data/analytics/` já estejam disponíveis no repositório, o dashboard pode ser executado diretamente com:

```bash
python src/app.py
```

Nesse caso, não é necessário rodar novamente todo o pipeline de coleta, tratamento e transformação.

---

## Observação Sobre os Dados

Os microdados do ENEM são arquivos grandes. Por isso, alguns arquivos brutos e intermediários podem não estar versionados no GitHub, dependendo das regras definidas no `.gitignore`.

Caso os arquivos finais da pasta `data/analytics/` não estejam disponíveis, será necessário seguir todo o pipeline de execução descrito neste README.

---

## Funcionalidades do Dashboard

O dashboard está dividido em três áreas principais.

### 1. Visão Geral

Apresenta indicadores gerais do ENEM 2022, como:

- total de participantes;
- média geral;
- média da redação;
- média das provas objetivas;
- percentual de candidatos com internet;
- número de municípios analisados.

### 2. Desigualdade Socioeconômica

Explora relações entre desempenho e variáveis socioeconômicas, como:

- renda familiar;
- acesso à internet;
- tipo de escola;
- comparação entre redação e provas objetivas;
- distribuição da nota de redação por renda;
- mapa de densidade entre provas objetivas e redação;
- análise de gap de desempenho por renda.

### 3. Municípios e IBGE

Utiliza a integração com dados populacionais do IBGE para analisar:

- desempenho por porte populacional do município;
- concentração de participantes por porte de município;
- relação entre população municipal e média geral;
- ranking de municípios por desempenho;
- análise regional por UF.

---

## Bases Geradas

Durante o pipeline, são gerados arquivos na pasta `data/analytics/`, como:

```text
agregado_outliers_uf_2022.csv
agregado_porte_municipio_2022.csv
agregado_renda_2022.csv
agregado_tipo_escola_2022.csv
enem_2022_ibge_integrado.csv
enem_2022_ibge_transformado.csv
enem_2022_limpo.csv
enem_2023_limpo.csv
ibge_populacao_municipios_2022_limpo.csv
resumo_geral_2022.csv
```

Essas bases são utilizadas pelo dashboard para gerar os gráficos, cards e análises interativas.

---

## Possíveis Problemas e Soluções

### Erro de arquivo não encontrado

Caso apareça erro informando que algum arquivo `.csv` não foi encontrado, verifique se os notebooks foram executados na ordem correta:

```text
01_preparacao_dados.ipynb
02_transformação_dados.ipynb
```

Também confirme se os arquivos foram gerados na pasta:

```text
data/analytics/
```

### Erro de dependência não instalada

Execute novamente:

```bash
pip install -r requirements.txt
```

### Dashboard não abre no navegador

Verifique no terminal o endereço exibido pelo Dash. Normalmente será:

```text
http://127.0.0.1:8050/
```

Copie e cole esse endereço no navegador.

---

## Equipe

| Nome | GitHub |
|---|---|
| Bruno Reitano Figuerola | [@Brunoreit](https://github.com/Brunoreit) |
| Enzo Garofalo Pampana | [@enzo-garofalo](https://github.com/enzo-garofalo) |
| Henry Gabriel Piozzi | [@HenryPiozzi](https://github.com/HenryPiozzi) |
| Rogério Medina | [@RogerioMedina](https://github.com/RogerioMedina) |
