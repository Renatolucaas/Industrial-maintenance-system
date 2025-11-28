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