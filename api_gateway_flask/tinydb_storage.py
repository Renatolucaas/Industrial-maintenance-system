import json
import boto3
import tempfile
import os
from tinydb import TinyDB, Query
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TinyDBS3Storage:
    """
    Classe para gerenciar TinyDB com armazenamento no S3
    """
    
    def __init__(self, bucket_name, s3_key='tinydb/industrial_manutencao.json'):
        self.bucket_name = bucket_name
        self.s3_key = s3_key
        self.s3_client = boto3.client('s3')
        self.local_db_path = None
        
    def _download_from_s3(self):
        """
        Download do arquivo JSON do S3 para arquivo temporário local
        """
        try:
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False)
            self.local_db_path = temp_file.name
             # Download do S3
            self.s3_client.download_fileobj(self.bucket_name, self.s3_key, temp_file)
            temp_file.seek(0)
            
            logger.info(f"Database baixado do S3: {self.s3_key}")
            return True
            
        except self.s3_client.exceptions.NoSuchKey:
            logger.info("Arquivo não encontrado no S3, criando novo database")
            # Criar arquivo vazio
            with open(self.local_db_path, 'w') as f:
                json.dump({}, f)
            return True
        except Exception as e:
            logger.error(f"Erro ao baixar do S3: {str(e)}")
            return False
    def _upload_to_s3(self):
        """
        Upload do arquivo JSON local para S3
        """
        try:
            if self.local_db_path and os.path.exists(self.local_db_path):
                with open(self.local_db_path, 'rb') as file_data:
                    self.s3_client.upload_fileobj(
                        file_data, 
                        self.bucket_name, 
                        self.s3_key
                    )
                logger.info(f"Database enviado para S3: {self.s3_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar para S3: {str(e)}")
            return False
        
    def get_database(self):
        """
        Retorna instância do TinyDB com sync automático no S3
        """
        if not self.local_db_path:
            success = self._download_from_s3()
            if not success:
                raise Exception("Falha ao inicializar database do S3")
            
            db = TinyDB(self.local_db_path)
        
        # Monkey patch para sync automático
        original_insert = db.insert
        original_update = db.update
        original_remove = db.remove
        original_truncate = db.truncate
        
        def insert_with_sync(document):
            result = original_insert(document)
            self._upload_to_s3()
            return result
        
        def update_with_sync(fields, cond=None):
            result = original_update(fields, cond)
            self._upload_to_s3()
            return result
        
        def remove_with_sync(cond=None):
            result = original_remove(cond)
            self._upload_to_s3()
            return result
        
        def truncate_with_sync():
            result = original_truncate()
            self._upload_to_s3()
            return result
        
        db.insert = insert_with_sync
        db.update = update_with_sync
        db.remove = remove_with_sync
        db.truncate = truncate_with_sync
        
        return db
    
    def close(self):
        """
        Limpeza do arquivo temporário
        """
        if self.local_db_path and os.path.exists(self.local_db_path):
            try:
                os.unlink(self.local_db_path)
            except:
                pass

# ========== FUNÇÕES PRINCIPAIS ==========

def criar_solicitacao_db(solicitacao_data, bucket_name):
    """
    Cria nova solicitação no database
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        
        solicitacao_id = tabela.insert(solicitacao_data)
        logger.info(f"Solicitação {solicitacao_id} salva no database")
        
        return solicitacao_id
    except Exception as e:
        logger.error(f"Erro ao criar solicitação: {str(e)}")
        raise e
    finally:
        storage.close()

def buscar_solicitacao_por_id(solicitacao_id, bucket_name):
    """
    Busca solicitação por ID
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        
        Solicitacao = Query()
        resultado = tabela.get(Solicitacao.solicitacao_id == solicitacao_id)
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao buscar solicitação: {str(e)}")
        return None
    finally:
        storage.close()

def listar_todas_solicitacoes(bucket_name):
    """
    Lista todas as solicitações do sistema
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        todas = tabela.all()
        
        # Ordenar por timestamp (mais recentes primeiro)
        todas.sort(key=lambda x: x.get('timestamp_solicitacao', ''), reverse=True)
        
        return todas
    except Exception as e:
        logger.error(f"Erro ao listar solicitações: {str(e)}")
        return []
    finally:
        storage.close()

def atualizar_status_solicitacao(solicitacao_id, novo_status, bucket_name, tecnico_responsavel=None):
    """
    Atualiza status da solicitação
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        
        Solicitacao = Query()
        updates = {
            'status': novo_status,
            'timestamp_atualizacao': datetime.now().isoformat()
        }
        
        if tecnico_responsavel:
            updates['tecnico_responsavel'] = tecnico_responsavel
        
        tabela.update(updates, Solicitacao.solicitacao_id == solicitacao_id)
        logger.info(f"Status da solicitação {solicitacao_id} atualizado para {novo_status}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar status: {str(e)}")
        return False
    finally:
        storage.close()

def listar_solicitacoes_por_filtro(filtro, valor, bucket_name):
    """
    Lista solicitações por filtro específico
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        
        Solicitacao = Query()
        resultados = tabela.search(getattr(Solicitacao, filtro) == valor)
        
        return resultados
    except Exception as e:
        logger.error(f"Erro ao filtrar solicitações: {str(e)}")
        return []
    finally:
        storage.close()

def obter_metricas_gerais(bucket_name):
    """
    Obtém métricas gerais do sistema
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        
        todas_solicitacoes = tabela.all()
        
        metricas = {
            'total_solicitacoes': len(todas_solicitacoes),
            'por_status': {},
            'por_prioridade': {},
            'por_tipo': {},
            'por_maquina': {},
            'ultimas_24h': 0
        }
        
        # Calcular métricas
        for solic in todas_solicitacoes:
            # Por status
            status = solic.get('status', 'desconhecido')
            metricas['por_status'][status] = metricas['por_status'].get(status, 0) + 1
            
            # Por prioridade
            prioridade = solic.get('prioridade', 'nao_informada')
            metricas['por_prioridade'][prioridade] = metricas['por_prioridade'].get(prioridade, 0) + 1
            
            # Por tipo
            tipo = solic.get('tipo_manutencao', 'nao_informado')
            metricas['por_tipo'][tipo] = metricas['por_tipo'].get(tipo, 0) + 1
            
            # Por máquina
            maquina = solic.get('maquina_id', 'desconhecida')
            metricas['por_maquina'][maquina] = metricas['por_maquina'].get(maquina, 0) + 1
        
        return metricas
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}")
        # Retornar métricas vazias em caso de erro
        return {
            'total_solicitacoes': 0,
            'por_status': {},
            'por_prioridade': {},
            'por_tipo': {},
            'por_maquina': {},
            'ultimas_24h': 0
        }
    finally:
        storage.close()

def limpar_todas_solicitacoes(bucket_name):
    """
    Limpa todas as solicitações (apenas para desenvolvimento)
    """
    storage = TinyDBS3Storage(bucket_name)
    try:
        db = storage.get_database()
        tabela = db.table('solicitacoes')
        tabela.truncate()
        logger.info("Todas as solicitações foram removidas")
        return True
    except Exception as e:
        logger.error(f"Erro ao limpar solicitações: {str(e)}")
        return False
    finally:
        storage.close()

        # ========== EXEMPLO DE USO ==========

if __name__ == "__main__":
    print("🧪 Testando TinyDB com S3...")
    
    # Teste da classe
    try:
        storage = TinyDBS3Storage("tinydb-storage-123456789")  # Use seu bucket real
        db = storage.get_database()
        
        # Criar tabela de solicitações
        tabela = db.table('solicitacoes')
        
        # Inserir dados de exemplo
        solicitacao_exemplo = {
            'solicitacao_id': 'sol_test_001',
            'operador_id': 'op_test_001',
            'maquina_id': 'maq_test_001',
            'tipo_manutencao': 'preventiva',
            'descricao_problema': 'Teste de sistema',
            'prioridade': 'media',
            'status': 'recebida',
            'timestamp_solicitacao': datetime.now().isoformat()
        }
        
        tabela.insert(solicitacao_exemplo)
        print("✅ Dados de teste inseridos com sucesso!")
        
        # Listar todas
        todas = tabela.all()
        print(f"📋 Total de solicitações: {len(todas)}")
        
        storage.close()
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
