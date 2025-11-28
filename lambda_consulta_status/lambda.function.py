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
    try:
        if AWS_MODE:
            # Buscar do S3 (produção)
            status = buscar_status_s3(solicitacao_id)
        else:
            # Buscar localmente (desenvolvimento)
            status = buscar_status_local(solicitacao_id)
        
        if status:
            return {
                'statusCode': 200,
                'body': json.dumps(status)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Solicitação não encontrada'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }