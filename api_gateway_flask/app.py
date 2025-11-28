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