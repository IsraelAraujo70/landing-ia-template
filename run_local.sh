#!/bin/bash

# Script para iniciar o servidor localmente para desenvolvimento

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python -m venv venv
fi

# Ativar o ambiente virtual
source venv/bin/activate

# Instalar dependências se necessário
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "Instalando dependências..."
    pip install -r requirements.txt
    touch venv/.dependencies_installed
fi

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "Criando arquivo .env a partir do exemplo..."
    cp .env.example .env
    echo "Por favor, edite o arquivo .env com sua chave da API OpenAI antes de continuar."
    exit 1
fi

# Criar diretórios necessários
mkdir -p uploads faiss_index

# Iniciar o servidor
echo "Iniciando o servidor..."
uvicorn app:app --reload --host 0.0.0.0 --port 8000
