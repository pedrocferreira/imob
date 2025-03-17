#!/bin/bash

# Script para iniciar o Assistente Imobiliário automaticamente
# Coloque em /etc/rc.local ou configure como serviço systemd

# Caminho para o diretório do projeto
PROJECT_DIR="/home/ec2-user/imob"

echo "[$(date)] Iniciando o Assistente Imobiliário automaticamente" >> /home/ec2-user/startup.log

# Entrar no diretório do projeto
cd $PROJECT_DIR

# Verificar e matar processos existentes na porta 8081
PORT_CHECK=$(netstat -tuln | grep ':8081 ')
if [ -n "$PORT_CHECK" ]; then
    echo "[$(date)] Encerrando processos na porta 8081" >> /home/ec2-user/startup.log
    sudo fuser -k 8081/tcp
    sleep 2
fi

# Iniciar o Docker
docker-compose down 2>/dev/null
docker-compose up --build -d

# Verificar se iniciou corretamente
if [ $? -eq 0 ]; then
    echo "[$(date)] Assistente iniciado com sucesso!" >> /home/ec2-user/startup.log
else
    echo "[$(date)] ERRO ao iniciar o Assistente!" >> /home/ec2-user/startup.log
fi 