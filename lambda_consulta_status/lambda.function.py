import json
import boto3
import os
from tinydb import TinyDB
import tempfile

# Configuração que funciona localmente e na AWS
try:
    S3_BUCKET = os.environ['S3_BUCKET']
    s3 = boto3.client('s3')
    AWS_MODE = True
except KeyError:
    # Modo desenvolvimento local
    S3_BUCKET = None
    s3 = None
    AWS_MODE = False
    print("⚠️ Modo desenvolvimento local ativado")

def lambda_handler(event, context):
    solicitacao_id = event['queryStringParameters']['solicitacao_id']
    