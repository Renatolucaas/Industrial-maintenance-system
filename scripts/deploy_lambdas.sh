#!/bin/bash

AWS_PROFILE="default"
AWS_REGION="us-east-1"
S3_BUCKET="seu-bucket-deploy-$(date +%Y%m%d)"

echo "=== DEPLOY DAS LAMBDAS ==="

# Criar bucket S3 para deploy (se não existir)
aws s3 mb s3://$S3_BUCKET --region $AWS_REGION --profile $AWS_PROFILE

# Fazer upload dos pacotes
echo "Upload dos pacotes Lambda..."
aws s3 cp packages/ s3://$S3_BUCKET/lambda-packages/ --recursive --profile $AWS_PROFILE

# Implantar Lambdas (exemplo CloudFormation)
echo "Implantando stack CloudFormation..."
aws cloudformation deploy \
    --template-file infrastructure/cloudformation.yaml \
    --stack-name manutencao-industrial \
    --parameter-overrides \
        S3Bucket=$S3_BUCKET \
        Environment=production \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION \
    --profile $AWS_PROFILE

echo "=== DEPLOY CONCLUÍDO ==="