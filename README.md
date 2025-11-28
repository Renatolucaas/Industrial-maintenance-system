# Industrial Maintenance System

📋 Sistema de Manutenção Preventiva e Corretiva
🚀 Visão Geral
Sistema completo de gerenciamento de manutenções industriais que permite registrar, processar e acompanhar solicitações de manutenção preventiva e corretiva em tempo real. O sistema utiliza notificações via Amazon SNS para manter os usuários informados sobre o status de suas solicitações.

🏗️ Arquitetura do Sistema

![Diagrama da Arquitetura](C:\Users\Pichau\OneDrive\Documentos\Industrial-maintenance-system\images\diagrama.jpg)

Componentes Principais
Frontend Web: Interface Flask para gestão de solicitações

API Gateway: Endpoint para recebimento de solicitações

Lambda Functions: Processamento assíncrono das solicitações

SQS Queue: Fila para gerenciamento de mensagens

SNS: Sistema de notificações por email

TinyDB: Banco de dados NoSQL (armazenamento em S3)

S3 Bucket: Armazenamento de dados e arquivos

Fluxo de Dados
Solicitação: Usuário cria solicitação via interface web

Processamento: Lambda function processa e atribui técnico

Notificação: SNS envia email de confirmação

Armazenamento: Dados salvos no TinyDB (S3)

Acompanhamento: Usuário pode consultar status em tempo real

📋 Funcionalidades
✅ Principais Características
🎯 Identificação Completa

Operador responsável

Máquina/equipamento

Tipo de manutenção (preventiva/corretiva)

Prioridade (baixa, média, alta)

🔔 Sistema de Notificações

Confirmação de recebimento

Atualizações de status

Alertas para prioridades altas

Notificações de conclusão

📊 Dashboard de Monitoramento

Métricas em tempo real

Status por prioridade

Distribuição por tipo de manutenção

Histórico completo

🚨 Recursos Especiais
Notificações Urgentes: Alertas especiais para prioridades altas

Atribuição Automática: Sistema inteligente de distribuição para técnicos

Armazenamento Híbrido: Funciona tanto localmente quanto na AWS

Interface Responsiva: Design adaptável para diferentes dispositivos

🛠️ Tecnologias Utilizadas
Backend
Python 3.8+

Flask: Framework web

Boto3: SDK AWS para Python

TinyDB: Banco de dados NoSQL leve

AWS Lambda: Computação serverless

AWS Services
S3: Armazenamento de objetos

SNS: Serviço de notificações

SQS: Filas de mensagens

API Gateway: Gerenciamento de APIs

Frontend
HTML5/CSS3

Bootstrap 5: Framework CSS

JavaScript: Interatividade

⚙️ Configuração e Instalação
Pré-requisitos
Python 3.8 ou superior

Conta AWS (para produção)

Credenciais AWS configuradas