#!/bin/bash

echo "Iniciando o Assistente Imobiliário em Docker..."

# Verificar se o docker-compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose não encontrado. Por favor, instale-o para continuar."
    exit 1
fi

# Verificar se a porta já está em uso
PORT_CHECK=$(netstat -tuln | grep ':8081 ')
if [ -n "$PORT_CHECK" ]; then
    echo "AVISO: A porta 8081 já está em uso!"
    echo "Escolha uma opção:"
    echo "1. Encerrar o processo atual e continuar"
    echo "2. Sair do script"
    read -p "Opção (1/2): " OPTION
    
    if [ "$OPTION" == "1" ]; then
        echo "Encerrando processo na porta 8081..."
        sudo fuser -k 8081/tcp || echo "Falha ao encerrar o processo. Tente manualmente."
    else
        echo "Operação cancelada pelo usuário."
        exit 0
    fi
fi

# Construir e iniciar os containers
docker-compose down 2>/dev/null
docker-compose up --build -d

# Verificar se o container iniciou com sucesso
if [ $? -eq 0 ]; then
    echo "Assistente Imobiliário está rodando em http://localhost:8081"
    echo "Para verificar os logs, execute: docker-compose logs -f"
    echo "Para parar o serviço, execute: docker-compose down"
else
    echo "Ocorreu um erro ao iniciar o container. Verifique os logs com: docker-compose logs"
fi 