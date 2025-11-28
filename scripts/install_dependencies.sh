#!/bin/bash

echo "=== INSTALANDO DEPENDÊNCIAS DO PROJETO ==="

# Criar diretório para pacotes
mkdir -p packages

# Lambda Ingestão
echo "Instalando Lambda Ingestão..."
cd lambda_ingestao
pip install -r requirements.txt -t .
zip -r ../packages/lambda_ingestao.zip .
cd ..

# Lambda Processor
echo "Instalando Lambda Processor..."
cd lambda_processor
pip install -r requirements.txt -t .
zip -r ../packages/lambda_processor.zip .
cd ..

# Lambda Consulta Status
echo "Instalando Lambda Consulta Status..."
cd lambda_consulta_status
pip install -r requirements.txt -t .
zip -r ../packages/lambda_consulta_status.zip .
cd ..

# API Flask
echo "Instalando API Flask..."
cd api_gateway_flask
pip install -r requirements.txt
cd ..

echo "=== INSTALAÇÃO CONCLUÍDA ==="
echo "Pacotes criados em: packages/"