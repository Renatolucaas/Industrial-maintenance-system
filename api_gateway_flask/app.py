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
                'TipoManutencao': {
                    'DataType': 'String', 
                    'StringValue': solicitacao['tipo_manutencao']
                }
            }
        )
        
        print(f"✅ Notificação SNS enviada: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar notificação SNS: {e}")
        return False
    # ========== BANCO DE DADOS LOCAL ==========

DB_FILE = 'local_database.json'

def carregar_dados():
    """Carrega dados do arquivo JSON local"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
    
    return {'solicitacoes': []}
def salvar_dados(dados):
    """Salva dados no arquivo JSON local"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
     except Exception as e:
        print(f"Erro ao salvar dados: {e}")
        return False
    
def criar_solicitacao_local(solicitacao_data):
    """Cria nova solicitação no banco local"""
    dados = carregar_dados()
    dados['solicitacoes'].append(solicitacao_data)
    salvar_dados(dados)
    return solicitacao_data['solicitacao_id']
def listar_todas_solicitacoes_local():
    """Lista todas as solicitações do banco local"""
    dados = carregar_dados()
    solicitacoes = dados.get('solicitacoes', [])
    solicitacoes.sort(key=lambda x: x.get('timestamp_solicitacao', ''), reverse=True)
    return solicitacoes

def obter_metricas_gerais_local():
    """Obtém métricas do sistema do banco local"""
    solicitacoes = listar_todas_solicitacoes_local()
    metricas = {
        'total_solicitacoes': len(solicitacoes),
        'por_status': {},
        'por_prioridade': {},
        'por_tipo': {},
        'ultimas_24h': 0
    }
    for solic in solicitacoes:
        status = solic.get('status', 'desconhecido')
        metricas['por_status'][status] = metricas['por_status'].get(status, 0) + 1
        prioridade = solic.get('prioridade', 'nao_informada')
        metricas['por_prioridade'][prioridade] = metricas['por_prioridade'].get(prioridade, 0) + 1
        tipo = solic.get('tipo_manutencao', 'nao_informado')
        metricas['por_tipo'][tipo] = metricas['por_tipo'].get(tipo, 0) + 1
    
    return metricas
# ========== BANCO DE DADOS AWS S3 ==========

def criar_solicitacao_aws(solicitacao_data):
    """Cria nova solicitação no S3"""
    try:
        from tinydb_storage import criar_solicitacao_db
        return criar_solicitacao_db(solicitacao_data, BUCKET_NAME)
    except Exception as e:
        print(f"❌ Erro ao salvar no S3: {e}")
        # Fallback para local
        return criar_solicitacao_local(solicitacao_data)
def listar_todas_solicitacoes_aws():
    """Lista todas as solicitações do S3"""
    try:
        from tinydb_storage import listar_todas_solicitacoes
        return listar_todas_solicitacoes(BUCKET_NAME)
    
