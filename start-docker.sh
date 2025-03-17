#!/bin/bash

echo "Iniciando o Assistente Imobiliário em Docker..."

# Verificar se o docker-compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose não encontrado. Por favor, instale-o para continuar."
    exit 1
fi

# Construir e iniciar os containers
docker-compose up --build -d

echo "Assistente Imobiliário está rodando em http://localhost:8080"
echo "Para verificar os logs, execute: docker-compose logs -f"
echo "Para parar o serviço, execute: docker-compose down" 