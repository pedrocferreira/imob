#!/bin/bash

echo "===== Iniciando Túnel ngrok para Assistente Imobiliário ====="

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
echo "🔍 Verificando se a porta 80 está disponível..."
if ! curl -s http://localhost:80 > /dev/null; then
    echo "⚠️ AVISO: A porta 80 parece não estar respondendo localmente!"
    echo "⚠️ Verifique se o seu container Docker está rodando:"
    docker ps
    echo ""
    read -p "Continuar mesmo assim? (s/n): " resposta
    if [[ "$resposta" != "s" ]]; then
        echo "❌ Operação cancelada pelo usuário."
        exit 1
    fi
fi

echo ""
echo "===================================================="
echo "🚀 INICIANDO NGROK - AGUARDE A URL ABAIXO"
echo "===================================================="
echo ""
echo "A URL será exibida nas linhas 'Forwarding' abaixo"
echo "Use a URL HTTPS (segunda linha) para compartilhar"
echo "Pressione Ctrl+C para encerrar quando terminar"
echo ""

# Executar ngrok com diagnóstico de erros
set -x  # Mostrar comandos sendo executados
exec ngrok http 80 