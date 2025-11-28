from flask import Flask, request, jsonify, render_template
import boto3
import os
import uuid
from datetime import datetime
import json

app = Flask(__name__)

# ========== CONFIGURAÇÃO INTELIGENTE ==========

def detectar_ambiente():
    
    """
    Detecta automaticamente se estamos em ambiente AWS ou desenvolvimento local
    """
     # Verifica se as credenciais AWS estão configuradas
    try:
        # Tenta acessar o S3
        s3 = boto3.client('s3')
        s3.list_buckets()

         # AWS está configurada
        BUCKET_NAME = "tinydb-storage-123456789" 

        # Verifica se o bucket existe
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
            return "aws", BUCKET_NAME
        except:
            print("⚠️ Bucket S3 não encontrado, usando modo local")
            return "local", None
        
    except Exception as e:
        print(f"⚠️ AWS não configurada, usando modo local: {e}")
        return "local", None

AMBIENTE, BUCKET_NAME = detectar_ambiente()
print(f"🎯 Ambiente detectado: {AMBIENTE.upper()}")

# ========== CONFIGURAÇÃO SNS ==========

# Configuração do SNS - COM SEU ARN REAL
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-2:626064810617:age-estimation-system-dev-notifications'
SNS_REGION = 'us-east-2'

def enviar_notificacao_sns(solicitacao):
    """Envia notificação via SNS quando uma solicitação é criada"""
    try:
        sns = boto3.client('sns', region_name=SNS_REGION)
        
        mensagem = f"""
🚨 NOVA SOLICITAÇÃO DE MANUTENÇÃO CRIADA 🚨

📋 ID da Solicitação: {solicitacao['solicitacao_id']}
🔧 Máquina: {solicitacao['maquina_id']}
📝 Tipo: {solicitacao['tipo_manutencao'].title()}
⚡ Prioridade: {solicitacao['prioridade'].title()}
👤 Operador: {solicitacao['operador_id']}

📄 Descrição do Problema:
{solicitacao['descricao_problema']}

⏰ Data/Hora: {solicitacao['timestamp_solicitacao']}
📊 Status: 📥 Recebida

---
Sistema de Manutenção Industrial
"""
        
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=mensagem,
            Subject=f"🔧 Nova Solicitação - {solicitacao['maquina_id']}",
            MessageAttributes={
                'Prioridade': {
                    'DataType': 'String',
                    'StringValue': solicitacao['prioridade']
                },