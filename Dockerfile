FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para numpy, faiss-cpu e outras bibliotecas
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar o restante dos arquivos da aplicação
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Criar diretórios necessários
RUN mkdir -p uploads faiss_index

# Expor a porta que a aplicação usará
EXPOSE 80

# Comando para iniciar a aplicação com hot-reload ativado
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
