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
    except Exception as e:
        print(f"❌ Erro ao carregar do S3: {e}")
        # Fallback para local
        return listar_todas_solicitacoes_local()
def obter_metricas_gerais_aws():
    """Obtém métricas do sistema do S3"""
    try:
        from tinydb_storage import obter_metricas_gerais
        return obter_metricas_gerais(BUCKET_NAME)
    except Exception as e:
        print(f"❌ Erro ao carregar métricas do S3: {e}")
        # Fallback para local
        return obter_metricas_gerais_local()
    
    # ========== FUNÇÕES UNIFICADAS ==========

def criar_solicitacao(solicitacao_data):
    """Cria solicitação no ambiente apropriado"""
    if AMBIENTE == "aws":
        return criar_solicitacao_aws(solicitacao_data)
    else:
        return criar_solicitacao_local(solicitacao_data)
def obter_metricas():
    """Obtém métricas do ambiente apropriado"""
    if AMBIENTE == "aws":
        return obter_metricas_gerais_aws()
    else:
        return obter_metricas_gerais_local()
    
    # ========== ROTAS DE PÁGINAS ==========

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/nova-solicitacao', methods=['GET'])
def nova_solicitacao():
    return render_template('nova_solicitacao.html')

@app.route('/solicitacoes', methods=['GET'])
def listar_solicitacoes_route():
    try:
        todas_solicitacoes = listar_solicitacoes()
        return render_template('solicitacoes.html', solicitacoes=todas_solicitacoes)
    except Exception as e:
        return render_template('error.html', error=f"Erro ao carregar solicitações: {str(e)}")
    
@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        metricas = obter_metricas()
        return render_template('dashboard.html', metricas=metricas)
    except Exception as e:
        return render_template('error.html', error=f"Erro ao carregar dashboard: {str(e)}")
    
    # ========== ROTAS SNS - NOTIFICAÇÕES ==========

@app.route('/teste-email', methods=['GET', 'POST'])
def teste_email():
    """Página para testar envio de emails via SNS"""

    if request.method == 'POST':
        try:
            # Dados do formulário
            email_destino = request.form.get('email', 'seu-email@empresa.com')
            mensagem_teste = request.form.get('mensagem', 'Esta é uma mensagem de teste do Sistema de Manutenção Industrial')
            
            # Configurar SNS
            sns = boto3.client('sns', region_name=SNS_REGION)
            
            # Mensagem de teste
            mensagem_completa = f"""
🔔 TESTE DE NOTIFICAÇÃO - SISTEMA DE MANUTENÇÃO INDUSTRIAL

Mensagem: {mensagem_teste}

📋 Detalhes do Teste:
- Sistema: Manutenção Industrial
- Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- Tipo: Teste de Notificação
- Status: ✅ Funcionando

Esta é uma mensagem de teste para verificar se o sistema 
de notificações está funcionando corretamente.

---
Sistema Automático - Não responder
"""
# Publicar no SNS
            response = sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=mensagem_completa,
                Subject="🔔 TESTE - Sistema de Manutenção Industrial",
                MessageAttributes={
                    'TipoTeste': {
                        'DataType': 'String',
                        'StringValue': 'NotificacaoEmail'
                    }
                }
            )
            return render_template('sucesso.html', 
                                mensagem=f"Email de teste enviado com sucesso! Message ID: {response['MessageId']}",
                                solicitacao_id=response['MessageId'])
            
        except Exception as e:
            return render_template('error.html', error=f"Erro ao enviar email: {str(e)}")
         # GET - Mostrar formulário de teste
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste de Email - SNS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h4>📧 Teste de Notificação por Email</h4>
                        </div>
                        <div class="card-body">
                            <p>Esta página testa o envio de notificações via Amazon SNS.</p>
                            
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Email para teste (opcional):</label>
                                    <input type="email" class="form-control" name="email" 
                                           placeholder="seu-email@empresa.com" 
                                           value="seu-email@empresa.com">
                                    <div class="form-text">Se você já está inscrito no tópico SNS, receberá o email.</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Mensagem de teste:</label>
                                    <textarea class="form-control" name="mensagem" rows="3">Esta é uma mensagem de teste do Sistema de Manutenção Industrial. Se você recebeu este email, o sistema de notificações está funcionando!</textarea>
                                </div>
                                
                                <button type="submit" class="btn btn-success">📨 Enviar Email de Teste</button>
                                <a href="/inscrever-email" class="btn btn-info">📝 Inscrever Email</a>
                                <a href="/" class="btn btn-secondary">Voltar</a>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
@app.route('/inscrever-email', methods=['GET', 'POST'])
def inscrever_email():
    """Inscrever um email no tópico SNS"""
    
    if request.method == 'POST':
        try:
            email = request.form['email']
            
            # Configurar SNS
            sns = boto3.client('sns', region_name=SNS_REGION)
            
            # Inscrever email no tópico
            response = sns.subscribe(
                TopicArn=SNS_TOPIC_ARN,
                Protocol='email',
                Endpoint=email,
                ReturnSubscriptionArn=True
            )
            return render_template('sucesso.html', 
                                mensagem=f"Email {email} inscrito com sucesso! Verifique sua caixa de entrada para confirmar a inscrição.",
                                solicitacao_id=response['SubscriptionArn'])
            
        except Exception as e:
            return render_template('error.html', error=f"Erro ao inscrever email: {str(e)}")
        
       
       # ========== ROTAS API ==========

@app.route('/api/solicitacao/manutencao', methods=['POST'])
def criar_solicitacao_route():
    try:
        # Dados do formulário
        dados_solicitacao = {
            'solicitacao_id': str(uuid.uuid4()),
            'operador_id': request.form['operador_id'],
            'maquina_id': request.form['maquina_id'],
            'tipo_manutencao': request.form['tipo_manutencao'],
            'prioridade': request.form['prioridade'],
            'descricao_problema': request.form['descricao_problema'],
            'status': 'recebida',
            'timestamp_solicitacao': datetime.now().isoformat()
        }

        # Salvar no banco de dados
        solicitacao_id = criar_solicitacao(dados_solicitacao)
        