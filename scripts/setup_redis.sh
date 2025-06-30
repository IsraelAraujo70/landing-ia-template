#!/bin/bash

# Script para configurar e iniciar Redis para desenvolvimento

echo "🔧 Configurando Redis para o sistema de autenticação..."

# Verifica se Redis está instalado
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis não está instalado. Instalando..."
    
    # Para Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    # Para CentOS/RHEL/Amazon Linux
    elif command -v yum &> /dev/null; then
        sudo yum install -y redis
    # Para macOS com Homebrew
    elif command -v brew &> /dev/null; then
        brew install redis
    else
        echo "❌ Sistema operacional não suportado. Instale Redis manualmente."
        exit 1
    fi
fi

# Verifica se Redis está rodando
if pgrep redis-server > /dev/null; then
    echo "✅ Redis já está rodando"
else
    echo "🚀 Iniciando Redis..."
    redis-server --daemonize yes --bind 127.0.0.1 --port 6379
    
    # Aguarda alguns segundos para o Redis inicializar
    sleep 2
    
    if pgrep redis-server > /dev/null; then
        echo "✅ Redis iniciado com sucesso"
    else
        echo "❌ Falha ao iniciar Redis"
        exit 1
    fi
fi

# Testa a conexão
echo "🔍 Testando conexão com Redis..."
if redis-cli ping | grep -q PONG; then
    echo "✅ Conexão com Redis funcionando"
    
    # Mostra informações do Redis
    echo ""
    echo "📊 Informações do Redis:"
    echo "Host: localhost"
    echo "Porta: 6379"
    echo "Database: 0"
    redis-cli info server | grep redis_version
    
    echo ""
    echo "🎉 Redis configurado e pronto para uso!"
    echo "💡 A aplicação agora usará Redis para armazenar sessions de autenticação"
    
else
    echo "❌ Falha na conexão com Redis"
    exit 1
fi