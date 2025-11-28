import json
import boto3
import os
from tinydb import TinyDB
import tempfile
from datetime import datetime

# Configuração S3 para TinyDB
s3 = boto3.client('s3')
sns = boto3.client('sns')  # NOVO

S3_BUCKET = os.environ['S3_BUCKET']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']  # NOVO

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            solicitacao = json.loads(record['body'])
            
            # Processar solicitação
            solicitacao['status'] = 'em_andamento'
            solicitacao['tecnico_atribuido'] = atribuir_tecnico(solicitacao)
            solicitacao['data_processamento'] = datetime.now().isoformat()
            
            # Salvar no TinyDB (S3)
            salvar_no_tinydb(solicitacao)
            
            # NOTIFICAÇÃO SNS - Solicitação em processamento
            mensagem_processamento = f"""
            ⚙️ SOLICITAÇÃO EM PROCESSAMENTO

            ID: {solicitacao['solicitacao_id']}
            Máquina: {solicitacao['maquina_id']}
            Técnico Atribuído: {solicitacao['tecnico_atribuido']}
            Prioridade: {solicitacao['prioridade']}
            Status: 🔄 Em Andamento

            Horário do Processamento: {solicitacao['data_processamento']}
            """
            
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=mensagem_processamento,
                Subject=f"⚙️ Em Processamento - {solicitacao['maquina_id']}",
                MessageAttributes={
                    'Status': {
                        'DataType': 'String',
                        'StringValue': 'em_andamento'
                    },
                    'Tecnico': {
                        'DataType': 'String',
                        'StringValue': solicitacao['tecnico_atribuido']
                    }
                }
            )
            
            # Notificação especial para prioridade ALTA
            if solicitacao['prioridade'] == 'alta':
                mensagem_urgente = f"""
                🚨🚨 SOLICITAÇÃO URGENTE 🚨🚨

                ATENÇÃO: Prioridade ALTA detectada!

                ID: {solicitacao['solicitacao_id']}
                Máquina: {solicitacao['maquina_id']}
                Técnico: {solicitacao['tecnico_atribuido']}
                Descrição: {solicitacao['descricao_problema']}

                Ação imediata requerida!
                """
                
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=mensagem_urgente,
                    Subject=f"🚨 URGENTE - {solicitacao['maquina_id']}",
                    MessageAttributes={
                        'Prioridade': {
                            'DataType': 'String',
                            'StringValue': 'URGENTE'
                        }
                    }
                )
                
            print(f"Processado: {solicitacao['solicitacao_id']}")
            
        except Exception as e:
            # Notificação de erro no processamento
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=f"❌ ERRO no processamento: {str(e)}\nSolicitação: {solicitacao}",
                Subject="🚨 ERRO Processamento - Sistema Manutenção"
            )
            print(f"Erro processando solicitação: {e}")

def salvar_no_tinydb(solicitacao):
    # Usar S3 como storage para TinyDB
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
        db = TinyDB(tmp_file.name)
        tabela = db.table('solicitacoes')
        tabela.insert(solicitacao)
        
        # Upload para S3
        with open(tmp_file.name, 'rb') as file_data:
            s3.upload_fileobj(file_data, S3_BUCKET, 'tinydb/status.json')

def atribuir_tecnico(solicitacao):
    # Lógica simples de atribuição
    tecnicos = ['tec_001', 'tec_002', 'tec_003']
    return tecnicos[hash(solicitacao['maquina_id']) % len(tecnicos)]