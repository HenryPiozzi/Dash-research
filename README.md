# Desigualdade no ENEM - Dashboard Interativo

Este repositório contém o projeto final da disciplina de Estudos Avançados de Banco de Dados. O objetivo do trabalho é analisar os microdados do ENEM integrados a indicadores socioeconômicos para identificar padrões, correlações e desigualdades no desempenho educacional brasileiro.

O projeto utiliza Python para todo o pipeline de ciência de dados (coleta, limpeza, transformação) e a biblioteca Dash para a construção da interface interativa.

## Estrutura do Repositório

O projeto está organizado da seguinte forma para garantir a separação entre o processamento de dados pesados e a execução do dashboard:

```text
dashboard-enem-desigualdade/
│
├── data/
│   ├── raw/          <- Arquivos originais e brutos (ex: CSV do ENEM). Nunca devem ser modificados.
│   └── processed/    <- Base de dados final, limpa e integrada, gerada após o tratamento no notebook.
│
├── notebooks/
│   └── 01_preparacao_dados.ipynb <- Jupyter Notebook onde é feita a coleta automática (API IBGE), tratamento, filtros e o merge de arquivos.
│
├── src/
│   └── app.py         <- Arquivo principal do dashboard desenvolvido em Dash (consome os dados da pasta processed).
│
├── README.md         <- Documentação e guia do projeto (este arquivo).
└── .gitignore        <- Configuração para impedir que arquivos de dados pesados sejam enviados ao GitHub.

## Como o Grupo Deve Trabalhar (Fluxo de Desenvolvimento)

1.  **Preparação do Ambiente e Dependências:**
    Certifique-se de criar e ativar o ambiente virtual (`.venv`). Para instalar todas as dependências necessárias para o projeto rodar (como Pandas, Requests e as bibliotecas do Dash), execute no terminal:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Atualização de Dependências (Caso instale algo novo):**
    Se você instalar alguma biblioteca nova durante o desenvolvimento (ex: componentes visuais do Dash), atualize o arquivo do repositório para o restante do grupo rodando:
    ```bash
    pip freeze > requirements.txt
    ```