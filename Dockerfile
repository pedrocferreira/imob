FROM python:3.9-slim

WORKDIR /app

# Copiar arquivos de dependências e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor a porta que a aplicação utiliza
EXPOSE 8080

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Comando para iniciar a aplicação
CMD ["python", "rag/run_rag.py", "server"] 