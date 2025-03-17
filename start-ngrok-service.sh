#!/bin/bash

echo "===== Configurando ngrok como serviço do sistema ====="

# Verificar se está rodando como root/sudo
if [ "$EUID" -ne 0 ]; then 
  echo "⚠️ Este script precisa ser executado como root (sudo)."
  echo "Execute: sudo ./start-ngrok-service.sh"
  exit 1
fi

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "⚙️ Instalando ngrok..."
    curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.tgz | tar xvz
    mv ngrok /usr/local/bin/
    echo "✅ ngrok instalado com sucesso!"
fi

# Configurar token
echo "🔑 Configurando token de autenticação..."
su -c "ngrok authtoken 2uQhUIL3Tvqz0if62yPUcJVOsSm_75gZdr2NFomLuq59WFLAE" ec2-user

# Copiar arquivo de serviço
echo "📄 Instalando serviço systemd..."
cp ngrok.service /etc/systemd/system/

# Recarregar systemd
echo "🔄 Recarregando configurações do systemd..."
systemctl daemon-reload

# Iniciar e habilitar serviço
echo "🚀 Iniciando serviço ngrok..."
systemctl start ngrok
systemctl enable ngrok

# Verificar status
echo "🔍 Verificando status do serviço..."
systemctl status ngrok --no-pager

# Aguardar ngrok iniciar
echo "⏳ Aguardando ngrok iniciar..."
sleep 5

# Mostrar URL
echo "📡 Obtendo URL do túnel..."
if curl -s http://localhost:4040/api/tunnels > /dev/null; then
    HTTP_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"http://[^"]*' | grep -o 'http://[^"]*')
    HTTPS_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*')
    
    echo ""
    echo "=================================================="
    echo "✅ NGROK INICIADO COMO SERVIÇO DO SISTEMA!"
    echo "=================================================="
    echo ""
    echo "🔗 HTTP URL: $HTTP_URL"
    echo "🔒 HTTPS URL: $HTTPS_URL (Recomendado)"
    echo ""
    echo "📊 Painel de controle: http://localhost:4040"
    echo ""
    echo "O ngrok continuará funcionando mesmo após você sair do terminal."
    echo "Para verificar o status: sudo systemctl status ngrok"
    echo "Para parar: sudo systemctl stop ngrok"
    echo "Para reiniciar: sudo systemctl restart ngrok"
    echo ""
else
    echo "❌ ERRO: Ngrok não está respondendo na porta 4040!"
    echo "Verifique o status do serviço: sudo systemctl status ngrok"
    echo "Veja os logs: sudo journalctl -u ngrok -f"
fi 