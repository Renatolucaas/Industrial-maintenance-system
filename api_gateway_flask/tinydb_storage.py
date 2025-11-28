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