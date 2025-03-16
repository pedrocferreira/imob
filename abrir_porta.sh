#!/bin/bash

# Abrir a porta 8080 para tráfego TCP
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# Salvar as regras para que persistam após reboot
if command -v iptables-save &> /dev/null; then
    sudo iptables-save | sudo tee /etc/sysconfig/iptables
    echo "Regras salvas em /etc/sysconfig/iptables"
else
    echo "Não foi possível salvar as regras permanentemente. Elas serão perdidas após reiniciar."
fi

echo "Porta 8080 aberta no firewall local. Agora você precisa abrir no grupo de segurança da AWS."
echo "Instruções para abrir no grupo de segurança da AWS:"
echo "1. Acesse o Console AWS em https://console.aws.amazon.com/"
echo "2. Vá para EC2 > Instâncias"
echo "3. Selecione sua instância"
echo "4. Na aba 'Segurança', clique no grupo de segurança"
echo "5. Em 'Regras de entrada', clique em 'Editar regras de entrada'"
echo "6. Adicione uma nova regra:"
echo "   - Tipo: TCP personalizado"
echo "   - Intervalo de portas: 8080"
echo "   - Origem: 0.0.0.0/0"
echo "   - Descrição: API Assistente Imobiliário"
echo "7. Salve as regras" 