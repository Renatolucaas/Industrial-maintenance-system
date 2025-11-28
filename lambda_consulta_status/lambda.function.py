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
def buscar_status_s3(solicitacao_id):
    """Busca do S3 (produção)"""
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as tmp_file:
        try:
            s3.download_fileobj(S3_BUCKET, 'tinydb/status.json', tmp_file)
            tmp_file.seek(0)
            
            db = TinyDB(tmp_file.name)
            tabela = db.table('solicitacoes')
            
            from tinydb import Query
            Solicitacao = Query()
            
            resultado = tabela.get(Solicitacao.solicitacao_id == solicitacao_id)
            return resultado
            
        except Exception as e:
            print(f"Erro ao buscar dados do S3: {e}")
            return None

def buscar_status_local(solicitacao_id):
    """Busca local (desenvolvimento)"""
    try:
        # Usar arquivo local para desenvolvimento
        db = TinyDB('local_dev_db.json')
        tabela = db.table('solicitacoes')
        
        from tinydb import Query
        Solicitacao = Query()
        
        resultado = tabela.get(Solicitacao.solicitacao_id == solicitacao_id)
        
        # Se não encontrar, criar dados de exemplo
        if not resultado:
            print("📝 Criando dados de exemplo para desenvolvimento...")
            dados_exemplo = {
                'solicitacao_id': 'sol_dev_001',
                'operador_id': 'op_001',
                'maquina_id': 'maq_123',
                'tipo_manutencao': 'preventiva',
                'descricao_problema': 'Barulho anormal no motor',
                'prioridade': 'alta',
                'status': 'recebida',
                'timestamp': '2025-11-21T10:00:00',
                'localizacao': 'setor_b',
                'turno': 'primeiro'
            }
            tabela.insert(dados_exemplo)
            resultado = dados_exemplo if solicitacao_id == 'sol_dev_001' else None
        
        return resultado
        
    except Exception as e:
        print(f"Erro ao buscar dados localmente: {e}")
        return None

# Código para teste local
if __name__ == '__main__':
    print("🧪 Testando Lambda Consulta Status Localmente...")
    
    # Teste
    event = {
        'queryStringParameters': {
            'solicitacao_id': 'sol_dev_001'
        }
    }
    
    resultado = lambda_handler(event, None)
    print(f"🎯 Resultado: {resultado}")