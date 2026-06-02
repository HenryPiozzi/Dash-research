import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
import zipfile
import certifi
import urllib3
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


URL_INEP = "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem"

ANOS_DESEJADOS = ["2022", "2023"]

PASTA_RAIZ = Path(__file__).resolve().parents[1]
PASTA_DATA = PASTA_RAIZ / "data"
PASTA_RAW = PASTA_DATA / "raw"

PASTA_RAW.mkdir(parents=True, exist_ok=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def buscar_link_microdados_enem(ano):
    print(f"\nAcessando página oficial do INEP para buscar ENEM {ano}...")

    resposta = requests.get(URL_INEP, timeout=30)
    resposta.raise_for_status()

    soup = BeautifulSoup(resposta.text, "html.parser")

    for link in soup.find_all("a"):
        texto = link.get_text(strip=True).lower()
        href = link.get("href")

        if not href:
            continue

        if f"microdados do enem {ano}" in texto:
            return urljoin(URL_INEP, href)

    raise Exception(f"Não encontrei o link dos microdados do ENEM {ano}.")


def criar_sessao_com_retry():
    sessao = requests.Session()

    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    sessao.mount("http://", adapter)
    sessao.mount("https://", adapter)

    return sessao


def baixar_arquivo(url, destino, max_tentativas=3):
    if destino.exists() and destino.stat().st_size > 0:
        print(f"Arquivo ZIP já existe: {destino}")
        print("Pulando download.")
        return

    print(f"Baixando arquivo de:\n{url}")

    for tentativa in range(max_tentativas):
        try:
            sessao = criar_sessao_com_retry()

            try:
                resposta = sessao.get(
                    url,
                    stream=True,
                    timeout=300,
                    verify=certifi.where()
                )
            except requests.exceptions.SSLError:
                print("Falha na validação SSL. Tentando sem verificação de certificado...")
                resposta = sessao.get(
                    url,
                    stream=True,
                    timeout=300,
                    verify=False
                )

            resposta.raise_for_status()

            tamanho_total = int(resposta.headers.get("content-length", 0))
            baixado = 0

            if destino.exists():
                destino.unlink()

            with open(destino, "wb") as arquivo:
                for bloco in resposta.iter_content(chunk_size=1024 * 1024):
                    if bloco:
                        arquivo.write(bloco)
                        baixado += len(bloco)

                        if tamanho_total > 0:
                            porcentagem = (baixado / tamanho_total) * 100
                            print(
                                f"\rBaixando... {porcentagem:.2f}% "
                                f"({baixado / (1024 ** 2):.1f} MB / "
                                f"{tamanho_total / (1024 ** 2):.1f} MB)",
                                end=""
                            )
                        else:
                            print(
                                f"\rBaixado: {baixado / (1024 ** 2):.1f} MB",
                                end=""
                            )

            print(f"\nArquivo salvo em: {destino}")
            return

        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        ) as erro:
            tentativa_atual = tentativa + 1
            print(f"\nErro na tentativa {tentativa_atual}/{max_tentativas}: {type(erro).__name__}")

            if tentativa_atual < max_tentativas:
                tempo_espera = 2 ** tentativa_atual
                print(f"Aguardando {tempo_espera}s antes de tentar novamente...")
                time.sleep(tempo_espera)
            else:
                print("Download falhou após todas as tentativas.")
                raise

        finally:
            if "sessao" in locals():
                sessao.close()


def extrair_zip(caminho_zip, pasta_saida):
    if pasta_saida.exists() and any(pasta_saida.iterdir()):
        print(f"Pasta já extraída: {pasta_saida}")
        print("Pulando extração.")
        return

    print(f"Extraindo arquivo para: {pasta_saida}")

    pasta_saida.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
        zip_ref.extractall(pasta_saida)

    print("Extração concluída.")
 

def coletar_ano(ano):
    link_microdados = buscar_link_microdados_enem(ano)

    arquivo_zip = PASTA_RAW / f"microdados_enem_{ano}.zip"
    pasta_extraida = PASTA_RAW / f"enem_{ano}"

    baixar_arquivo(link_microdados, arquivo_zip)
    extrair_zip(arquivo_zip, pasta_extraida)

    print(f"\nColeta finalizada para ENEM {ano}.")


def main():
    for ano in ANOS_DESEJADOS:
        coletar_ano(ano)


if __name__ == "__main__":
    main()