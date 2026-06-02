from pathlib import Path
import zipfile


PASTA_RAIZ = Path(__file__).resolve().parents[1]
PASTA_PROCESSED = PASTA_RAIZ / "data" / "processed"
PASTA_ZIPS = PASTA_RAIZ / "data" / "zipped"

PASTA_ZIPS.mkdir(parents=True, exist_ok=True)


def zipar_arquivo(caminho_arquivo):
    nome_zip = caminho_arquivo.stem + ".zip"
    caminho_zip = PASTA_ZIPS / nome_zip

    print(f"Compactando: {caminho_arquivo.name}")

    with zipfile.ZipFile(caminho_zip, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(
            caminho_arquivo,
            arcname=caminho_arquivo.name
        )

    tamanho_original = caminho_arquivo.stat().st_size / (1024 ** 2)
    tamanho_zip = caminho_zip.stat().st_size / (1024 ** 2)

    print(f"Original: {tamanho_original:.2f} MB")
    print(f"ZIP:      {tamanho_zip:.2f} MB")
    print(f"Salvo em: {caminho_zip}\n")


def zipar_processed():
    arquivos_csv = list(PASTA_PROCESSED.glob("*.csv"))

    if not arquivos_csv:
        print("Nenhum CSV encontrado em data/processed.")
        return

    for arquivo in arquivos_csv:
        zipar_arquivo(arquivo)


if __name__ == "__main__":
    zipar_processed()