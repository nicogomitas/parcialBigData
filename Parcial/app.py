import requests
import boto3
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import os

# Crear un cliente de S3
s3_client = boto3.client('s3')

# Primera función Lambda: Descarga el contenido y lo sube a S3
def f(event, context):
    bucket_name = "parcial3-lambda1"  # Bucket específico para esta función
    base_path = "headlines/raw"

    urls = {
        "el_tiempo": "https://www.eltiempo.com/",
        "el_espectador": "https://www.elespectador.com/",
        "publimetro": "https://www.publimetro.co/"
    }

    today = datetime.utcnow().strftime("%Y-%m-%d")

    for source, url in urls.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text

            filename = f"{base_path}/{source}-contenido-{today}.html"

            s3_client.put_object(
                Bucket=bucket_name,
                Key=filename,
                Body=content,
                ContentType="text/html"
            )
            print(f"Contenido de {source} subido correctamente a {filename}")
        except Exception as e:
            print(f"Error al procesar {source}: {e}")


# Segunda función Lambda: Procesa los datos de S3 y genera un CSV

def process_data(event, context):
    bucket_name = "parcial3-lambda1"  # Bucket donde están los datos RAW
    processed_bucket_name = "parcial3-lambda2"  # Bucket destino para el CSV
    final_path = "headlines/final"

    for record in event['Records']:
        key = record['s3']['object']['key']
        source = key.split('/')[-1].split('-')[0]  # Extraer el nombre del periódico

        # Descargar el archivo desde S3
        obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        html_content = obj['Body'].read().decode('utf-8')

        # Procesar el HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        headlines = []
        for article in soup.find_all('article'):
            title = article.find('h2') or article.find('h3')
            link = article.find('a')
            if title and link:
                headlines.append({
                    "category": source,
                    "headline": title.get_text(strip=True),
                    "link": link['href']
                })

        # Generar un archivo CSV
        today = datetime.utcnow()
        year, month, day = today.strftime("%Y"), today.strftime("%m"), today.strftime("%d")
        csv_filename = f"{final_path}/periodico={source}/year={year}/month={month}/day={day}/headlines.csv"

        # Guardar los datos en el archivo CSV
        csv_content = "category,headline,link\n"
        csv_content += "\n".join([f"{h['category']},{h['headline']},{h['link']}" for h in headlines])

        # Subir el archivo CSV a S3
        s3_client.put_object(
            Bucket=processed_bucket_name,
            Key=csv_filename,
            Body=csv_content,
            ContentType="text/csv"
        )
        print(f"Archivo CSV subido correctamente a {csv_filename}")