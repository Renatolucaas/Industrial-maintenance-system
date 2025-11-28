import json
import boto3
import uuid
from datetime import datetime
import os

sqs = boto3.client('sqs')
sns = boto3.client('sns')  # NOVO

SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']  # NOVO

def lambda_handler(event, context):
    try:
        # Parse do corpo da requisição
        body = json.loads(event['body'])
        
        # Criar solicitação de manutenção
        solicitacao = {
            'solicitacao_id': str(uuid.uuid4()),
            'operador_id': body['operador_id'],
            'maquina_id': body['maquina_id'],
            'tipo_manutencao': body['tipo_manutencao'],
            'descricao_problema': body['descricao_problema'],
            'prioridade': body.get('prioridade', 'media'),
            'timestamp': datetime.now().isoformat(),
            'status': 'recebida'
        }
        
        # Enviar para SQS
        response_sqs = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(solicitacao)
        )
        
        # NOTIFICAÇÃO SNS - Nova solicitação recebida
        mensagem_notificacao = f"""
        🚨 NOVA SOLICITAÇÃO DE MANUTENÇÃO 🚨

        ID: {solicitacao['solicitacao_id']}
        Máquina: {solicitacao['maquina_id']}
        Tipo: {solicitacao['tipo_manutencao']}
        Prioridade: {solicitacao['prioridade']}
        Operador: {solicitacao['operador_id']}
        Descrição: {solicitacao['descricao_problema']}
        Horário: {solicitacao['timestamp']}

        Status: 📥 Recebida
        """
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=mensagem_notificacao,
            Subject=f"🔧 Nova Solicitação - {solicitacao['maquina_id']}",
            MessageAttributes={
                'Prioridade': {
                    'DataType': 'String',
                    'StringValue': solicitacao['prioridade']
                },
                'TipoManutencao': {
                    'DataType': 'String', 
                    'StringValue': solicitacao['tipo_manutencao']
                }
            }
        )
        
        return {
            'statusCode': 202,
            'body': json.dumps({
                'message': 'Solicitação recebida com sucesso',
                'solicitacao_id': solicitacao['solicitacao_id'],
                'status': 'em_processamento'
            })
        }
        
    except Exception as e:
        # Notificação de erro
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"❌ ERRO no sistema: {str(e)}",
            Subject="🚨 ERRO - Sistema Manutenção"
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }