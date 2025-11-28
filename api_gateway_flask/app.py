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