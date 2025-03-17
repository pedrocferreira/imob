#!/bin/bash

echo "==== Verificação de Porta 8081 ===="
echo "Testando conectividade interna..."
curl -s http://localhost:8081 > /dev/null && echo "✅ Porta 8081 está funcionando localmente" || echo "❌ Porta 8081 NÃO está funcionando localmente"

echo -e "\nVerificando processos na porta 8081..."
sudo netstat -tuln | grep 8081

echo -e "\nVerificando containers Docker..."
docker ps | grep 8081

echo -e "\nVerificação do firewall local..."
sudo iptables -L INPUT -n | grep 8081

# Imprime configurações de rede relevantes
echo -e "\nInformações de IP e rede:"
hostname -I
curl -s http://checkip.amazonaws.com

echo -e "\n==== CONCLUSÃO ===="
echo "Se a porta 8081 está funcionando localmente mas não externamente, você precisa:"
echo "1. Verificar o Security Group no Console AWS (https://console.aws.amazon.com/ec2/)"
echo "2. Adicionar uma regra de entrada (Inbound Rule) para a porta TCP 8081"
echo "3. Origem: 0.0.0.0/0 (qualquer IP)" 