from pathlib import Path
import pandas as pd
import shutil


ANOS_DESEJADOS = ["2022", "2023"]

PASTA_RAIZ = Path(__file__).resolve().parents[1]
PASTA_DATA = PASTA_RAIZ / "data"
PASTA_RAW = PASTA_DATA / "raw"
PASTA_PROCESSED = PASTA_DATA / "processed"

PASTA_RAW.mkdir(parents=True, exist_ok=True)
PASTA_PROCESSED.mkdir(parents=True, exist_ok=True)


COLUNAS_DESEJADAS = [
    # Identificação geral
    "NU_ANO",
    "SG_UF_PROVA",

    # Perfil do participante
    "TP_SEXO",
    "TP_FAIXA_ETARIA",

    # Tipo de escola informado pelo participante
    "TP_ESCOLA",

    # Dados da escola
    "SG_UF_ESC",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "TP_SIT_FUNC_ESC",

    # Dados socioeconômicos
    "Q006",  # renda familiar
    "Q025",  # acesso à internet

    # Notas
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO"
]

COLUNAS_NOTAS = [
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO"
]


def localizar_csv_principal(ano):
    pasta_ano = PASTA_RAW / f"enem_{ano}"

    if not pasta_ano.exists():
        print(f"Pasta não encontrada para o ano {ano}: {pasta_ano}")
        return None

    arquivos_csv = list(pasta_ano.rglob("*.csv"))

    for arquivo in arquivos_csv:
        if "MICRODADOS_ENEM" in arquivo.name.upper():
            return arquivo

    print(f"CSV principal não encontrado para o ano {ano}.")
    return None


def listar_arquivos():
    print("\nArquivos encontrados em data/raw:\n")

    if not PASTA_RAW.exists() or not any(PASTA_RAW.iterdir()):
        print("Nenhum arquivo encontrado.")
        return

    for item in PASTA_RAW.rglob("*"):
        if item.is_file():
            tamanho_mb = item.stat().st_size / (1024 ** 2)
            print(f"{item} - {tamanho_mb:.2f} MB")


def obter_colunas_csv(csv_path):
    df_amostra = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin1",
        nrows=0
    )

    return df_amostra.columns.tolist()


def visualizar_colunas():
    ano = input("Digite o ano que deseja visualizar: ").strip()

    csv_path = localizar_csv_principal(ano)

    if csv_path is None:
        return

    colunas = obter_colunas_csv(csv_path)

    print(f"\nColunas encontradas no ENEM {ano}:\n")

    for coluna in colunas:
        print(coluna)

    colunas_faltantes = [col for col in COLUNAS_DESEJADAS if col not in colunas]

    if colunas_faltantes:
        print("\nColunas desejadas que NÃO foram encontradas:")
        for coluna in colunas_faltantes:
            print(f"- {coluna}")
    else:
        print("\nTodas as colunas desejadas foram encontradas.")


def visualizar_amostra():
    ano = input("Digite o ano que deseja visualizar: ").strip()

    csv_path = localizar_csv_principal(ano)

    if csv_path is None:
        return

    colunas_existentes = obter_colunas_csv(csv_path)
    colunas_para_ler = [col for col in COLUNAS_DESEJADAS if col in colunas_existentes]

    if not colunas_para_ler:
        print("Nenhuma das colunas desejadas foi encontrada.")
        return

    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin1",
        usecols=colunas_para_ler,
        nrows=10
    )

    print(f"\nAmostra do ENEM {ano}:\n")
    print(df)


def processar_dados():
    for ano in ANOS_DESEJADOS:
        csv_path = localizar_csv_principal(ano)

        if csv_path is None:
            print(f"Pulando ano {ano}.")
            continue

        print(f"\nProcessando ENEM {ano}...")
        print(f"Arquivo: {csv_path}")

        colunas_existentes = obter_colunas_csv(csv_path)

        colunas_para_ler = [
            coluna for coluna in COLUNAS_DESEJADAS
            if coluna in colunas_existentes
        ]

        colunas_faltantes = [
            coluna for coluna in COLUNAS_DESEJADAS
            if coluna not in colunas_existentes
        ]

        if colunas_faltantes:
            print(f"\nAtenção: o ano {ano} não possui algumas colunas:")
            for coluna in colunas_faltantes:
                print(f"- {coluna}")

        if not colunas_para_ler:
            print(f"Nenhuma coluna desejada encontrada no ano {ano}. Pulando.")
            continue

        df = pd.read_csv(
            csv_path,
            sep=";",
            encoding="latin1",
            usecols=colunas_para_ler
        )

        # Garante que todas as colunas desejadas existam no DataFrame final.
        # Se alguma não existia no CSV original, ela entra vazia.
        for coluna in COLUNAS_DESEJADAS:
            if coluna not in df.columns:
                df[coluna] = pd.NA

        df = df[COLUNAS_DESEJADAS]

        colunas_notas_existentes = [
            coluna for coluna in COLUNAS_NOTAS
            if coluna in df.columns
        ]

        if colunas_notas_existentes:
            df = df.dropna(
                subset=colunas_notas_existentes,
                how="all"
            )

        arquivo_saida = PASTA_PROCESSED / f"enem_{ano}_tratado.csv"

        df.to_csv(
            arquivo_saida,
            index=False,
            sep=";",
            encoding="utf-8"
        )

        print(f"\nBase processada gerada em: {arquivo_saida}")
        print(f"Total de linhas: {len(df)}")
        print(f"Total de colunas: {len(df.columns)}")

        print("\nPrimeiras linhas:")
        print(df.head())


def copiar_dicionarios():
    arquivos_dicionario = [
        arquivo
        for arquivo in PASTA_RAW.rglob("*")
        if arquivo.is_file()
        and "dicionario" in arquivo.name.lower()
    ]

    if not arquivos_dicionario:
        print("Nenhum arquivo de dicionário encontrado.")
        return

    for arquivo in arquivos_dicionario:
        destino = PASTA_PROCESSED / arquivo.name
        print(f"Copiando dicionário: {arquivo} -> {destino}")
        shutil.copy2(arquivo, destino)

    print("Dicionários copiados.")


def apagar_zips():
    arquivos_zip = list(PASTA_RAW.glob("*.zip"))

    if not arquivos_zip:
        print("Nenhum ZIP encontrado para apagar.")
        return

    print("\nZIPs encontrados:")
    for arquivo in arquivos_zip:
        print(f"- {arquivo}")

    confirmar = input("\nTem certeza que deseja apagar os ZIPs? Digite SIM: ").strip()

    if confirmar == "SIM":
        for arquivo in arquivos_zip:
            arquivo.unlink()
            print(f"Apagado: {arquivo}")
    else:
        print("Operação cancelada.")


def apagar_pastas_extraidas():
    pastas = [
        pasta
        for pasta in PASTA_RAW.iterdir()
        if pasta.is_dir() and pasta.name.startswith("enem_")
    ]

    if not pastas:
        print("Nenhuma pasta extraída encontrada para apagar.")
        return

    print("\nPastas extraídas encontradas:")
    for pasta in pastas:
        print(f"- {pasta}")

    confirmar = input("\nTem certeza que deseja apagar as pastas extraídas? Digite SIM: ").strip()

    if confirmar == "SIM":
        for pasta in pastas:
            shutil.rmtree(pasta)
            print(f"Apagada: {pasta}")
    else:
        print("Operação cancelada.")


def apagar_raw_completo():
    if not PASTA_RAW.exists() or not any(PASTA_RAW.iterdir()):
        print("A pasta raw já está vazia.")
        return

    print(f"\nVocê está prestes a apagar todo o conteúdo de: {PASTA_RAW}")
    print("Isso remove ZIPs e pastas extraídas, mas mantém data/processed.")

    confirmar = input("Digite SIM para confirmar: ").strip()

    if confirmar == "SIM":
        for item in PASTA_RAW.iterdir():
            if item.is_file():
                item.unlink()
                print(f"Arquivo apagado: {item}")
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"Pasta apagada: {item}")
    else:
        print("Operação cancelada.")


def menu():
    while True:
        print("\n===== MENU DE PROCESSAMENTO ENEM =====")
        print("1 - Listar arquivos em data/raw")
        print("2 - Visualizar colunas de um ano")
        print("3 - Visualizar amostra de um ano")
        print("4 - Processar dados")
        print("5 - Copiar dicionários para data/processed")
        print("6 - Apagar apenas arquivos ZIP")
        print("7 - Apagar pastas extraídas")
        print("8 - Apagar tudo de data/raw")
        print("0 - Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            listar_arquivos()
        elif opcao == "2":
            visualizar_colunas()
        elif opcao == "3":
            visualizar_amostra()
        elif opcao == "4":
            processar_dados()
        elif opcao == "5":
            copiar_dicionarios()
        elif opcao == "6":
            apagar_zips()
        elif opcao == "7":
            apagar_pastas_extraidas()
        elif opcao == "8":
            apagar_raw_completo()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()