import requests
import pandas as pd
import time

def coletar_dados_ibge():
    base_url = "https://servicodados.ibge.gov.br/api/v3/agregados"
    
    # Exemplo: dados de população por município
    url = f"{base_url}/6579/periodos/2022/variaveis/9324?localidades=N6[all]"
    
    response = requests.get(url)
    dados = response.json()
    
    # Transformar em DataFrame
    registros = []
    for item in dados[0]["resultados"][0]["series"]:
        registros.append({
            "municipio": item["localidade"]["nome"],
            "codigo": item["localidade"]["id"],
            "valor": item["serie"]["2022"]
        })
    
    return pd.DataFrame(registros)

df = coletar_dados_ibge()
df.to_csv("dados_brutos.csv", index=False)
print(f"Coletados {len(df)} registros")