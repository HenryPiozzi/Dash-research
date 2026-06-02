from pathlib import Path
import zipfile
import shutil


PASTA_RAIZ = Path(__file__).resolve().parents[1]
PASTA_PROCESSED = PASTA_RAIZ / "data" / "processed"
PASTA_ZIPS = PASTA_RAIZ / "data" / "zipped"

PASTA_PROCESSED.mkdir(parents=True, exist_ok=True)
PASTA_ZIPS.mkdir(parents=True, exist_ok=True)


def mostrar_tamanho(caminho):
    tamanho_mb = caminho.stat().st_size / (1024 ** 2)
    return f"{tamanho_mb:.2f} MB"


def listar_arquivos_processed():
    print("\nArquivos em data/processed:")

    arquivos = list(PASTA_PROCESSED.glob("*"))

    if not arquivos:
        print("Nenhum arquivo encontrado.")
        return

    for arquivo in arquivos:
        if arquivo.is_file():
            print(f"- {arquivo.name} ({mostrar_tamanho(arquivo)})")


def listar_arquivos_zipped():
    print("\nArquivos em data/zipped:")

    arquivos = list(PASTA_ZIPS.glob("*.zip"))

    if not arquivos:
        print("Nenhum ZIP encontrado.")
        return

    for arquivo in arquivos:
        print(f"- {arquivo.name} ({mostrar_tamanho(arquivo)})")


def zipar_arquivo(caminho_arquivo):
    nome_zip = caminho_arquivo.stem + ".zip"
    caminho_zip = PASTA_ZIPS / nome_zip

    print(f"\nCompactando: {caminho_arquivo.name}")

    with zipfile.ZipFile(caminho_zip, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(
            caminho_arquivo,
            arcname=caminho_arquivo.name
        )

    tamanho_original = mostrar_tamanho(caminho_arquivo)
    tamanho_zip = mostrar_tamanho(caminho_zip)

    print(f"Original: {tamanho_original}")
    print(f"ZIP:      {tamanho_zip}")
    print(f"Salvo em: {caminho_zip}")


def zipar_processed():
    arquivos_csv = list(PASTA_PROCESSED.glob("*.csv"))

    if not arquivos_csv:
        print("\nNenhum CSV encontrado em data/processed.")
        return

    print("\nCSVs encontrados para compactar:")
    for arquivo in arquivos_csv:
        print(f"- {arquivo.name} ({mostrar_tamanho(arquivo)})")

    confirmar = input("\nDeseja compactar todos os CSVs? Digite SIM: ").strip()

    if confirmar != "SIM":
        print("Operação cancelada.")
        return

    for arquivo in arquivos_csv:
        zipar_arquivo(arquivo)

    print("\nCompactação concluída.")


def extrair_zip(caminho_zip):
    print(f"\nExtraindo: {caminho_zip.name}")

    with zipfile.ZipFile(caminho_zip, "r") as zipf:
        arquivos_no_zip = zipf.namelist()

        print("Arquivos dentro do ZIP:")
        for nome in arquivos_no_zip:
            print(f"- {nome}")

        for nome in arquivos_no_zip:
            destino = PASTA_PROCESSED / nome

            if destino.exists():
                print(f"Aviso: {destino.name} já existe em data/processed.")
                sobrescrever = input("Deseja sobrescrever? Digite SIM: ").strip()

                if sobrescrever != "SIM":
                    print(f"Pulando: {destino.name}")
                    continue

            zipf.extract(nome, PASTA_PROCESSED)
            print(f"Extraído para: {destino}")


def extrair_zips_para_processed():
    arquivos_zip = list(PASTA_ZIPS.glob("*.zip"))

    if not arquivos_zip:
        print("\nNenhum ZIP encontrado em data/zipped.")
        return

    print("\nZIPs encontrados:")
    for i, arquivo in enumerate(arquivos_zip, start=1):
        print(f"{i} - {arquivo.name} ({mostrar_tamanho(arquivo)})")

    print("0 - Cancelar")

    escolha = input("\nEscolha um ZIP para extrair ou digite TODOS: ").strip()

    if escolha == "0":
        print("Operação cancelada.")
        return

    if escolha.upper() == "TODOS":
        confirmar = input("Deseja extrair todos os ZIPs? Digite SIM: ").strip()

        if confirmar != "SIM":
            print("Operação cancelada.")
            return

        for arquivo in arquivos_zip:
            extrair_zip(arquivo)

        print("\nExtração concluída.")
        return

    try:
        indice = int(escolha)

        if indice < 1 or indice > len(arquivos_zip):
            print("Opção inválida.")
            return

        extrair_zip(arquivos_zip[indice - 1])
        print("\nExtração concluída.")

    except ValueError:
        print("Opção inválida.")


def apagar_csvs_processed():
    arquivos_csv = list(PASTA_PROCESSED.glob("*.csv"))

    if not arquivos_csv:
        print("\nNenhum CSV encontrado para apagar.")
        return

    print("\nCSVs encontrados em data/processed:")
    for arquivo in arquivos_csv:
        print(f"- {arquivo.name} ({mostrar_tamanho(arquivo)})")

    confirmar = input("\nTem certeza que deseja apagar os CSVs? Digite SIM: ").strip()

    if confirmar != "SIM":
        print("Operação cancelada.")
        return

    for arquivo in arquivos_csv:
        arquivo.unlink()
        print(f"Apagado: {arquivo.name}")

    print("\nCSVs apagados.")


def apagar_zips():
    arquivos_zip = list(PASTA_ZIPS.glob("*.zip"))

    if not arquivos_zip:
        print("\nNenhum ZIP encontrado para apagar.")
        return

    print("\nZIPs encontrados em data/zipped:")
    for arquivo in arquivos_zip:
        print(f"- {arquivo.name} ({mostrar_tamanho(arquivo)})")

    confirmar = input("\nTem certeza que deseja apagar os ZIPs? Digite SIM: ").strip()

    if confirmar != "SIM":
        print("Operação cancelada.")
        return

    for arquivo in arquivos_zip:
        arquivo.unlink()
        print(f"Apagado: {arquivo.name}")

    print("\nZIPs apagados.")


def menu():
    while True:
        print("\n===== MENU ZIP DATA =====")
        print("1 - Listar arquivos em data/processed")
        print("2 - Listar ZIPs em data/zipped")
        print("3 - Compactar CSVs de processed para zipped")
        print("4 - Extrair ZIPs de zipped para processed")
        print("5 - Apagar CSVs de processed")
        print("6 - Apagar ZIPs de zipped")
        print("0 - Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            listar_arquivos_processed()
        elif opcao == "2":
            listar_arquivos_zipped()
        elif opcao == "3":
            zipar_processed()
        elif opcao == "4":
            extrair_zips_para_processed()
        elif opcao == "5":
            apagar_csvs_processed()
        elif opcao == "6":
            apagar_zips()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()