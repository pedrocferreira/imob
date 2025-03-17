#!/bin/bash

echo "===== Iniciando Túnel ngrok em modo background ====="

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "⚙️ Instalando ngrok..."
    curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.tgz | tar xvz
    sudo mv ngrok /usr/local/bin/
    echo "✅ ngrok instalado com sucesso!"
fi

# Configurar token
echo "🔑 Configurando token de autenticação..."
ngrok authtoken 2uQhUIL3Tvqz0if62yPUcJVOsSm_75gZdr2NFomLuq59WFLAE

# Encerrar instâncias existentes
echo "🔄 Encerrando instâncias anteriores do ngrok..."
pkill -f ngrok 2>/dev/null || true
sleep 2

# Verificar porta 80
echo "🔍 Verificando porta 80..."
if ! curl -s http://localhost:80 -o /dev/null; then
    echo "⚠️ AVISO: A porta 80 não está respondendo! Verifique seu container Docker."
    exit 1
fi

# Iniciar ngrok em background
echo "🚀 Iniciando ngrok em background..."
nohup ngrok http 80 > /dev/null 2>&1 &

# Aguardar ngrok iniciar
echo "⏳ Aguardando ngrok iniciar..."
sleep 5

# Obter URLs
echo "📡 Obtendo URLs do ngrok..."
API_URL="http://localhost:4040/api/tunnels"
URLS=$(curl -s $API_URL)

if [[ -z "$URLS" || "$URLS" == *"\"tunnels\":[]"* ]]; then
    echo "❌ ERRO: Ngrok falhou ao iniciar ou criar túnel!"
    echo "Tente executar o comando manualmente: ngrok http 80"
    exit 1
fi

HTTP_URL=$(echo $URLS | grep -o '"public_url":"http://[^"]*' | grep -o 'http://[^"]*')
HTTPS_URL=$(echo $URLS | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*')

echo ""
echo "=================================================="
echo "✅ TÚNEL NGROK ATIVO!"
echo "=================================================="
echo ""
echo "🔗 HTTP URL: $HTTP_URL"
echo "🔒 HTTPS URL: $HTTPS_URL (Recomendado)"
echo ""
echo "📊 Painel de controle: http://localhost:4040"
echo ""
echo "O túnel permanecerá ativo em segundo plano."
echo "Para encerrar, execute: pkill -f ngrok"
echo "" 