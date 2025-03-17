# Configuração do Ngrok para Assistente Imobiliário

Este branch contém configurações específicas para expor o Assistente Imobiliário à internet usando o ngrok, sem necessidade de configurar o Security Group da AWS.

## O que é o ngrok?

O ngrok é uma ferramenta que cria túneis seguros para expor serviços locais à internet pública, mesmo quando estão atrás de firewalls ou não têm IPs públicos.

## Opções de Uso

Este branch oferece 3 maneiras diferentes de usar o ngrok:

### 1. Modo Interativo (recomendado para testes rápidos)

```bash
./start-ngrok.sh
```

- Mostra logs e eventos em tempo real
- Executa em primeiro plano no terminal
- Para quando você fecha o terminal ou pressiona Ctrl+C

### 2. Modo Background (para uso temporário)

```bash
./start-ngrok-bg.sh
```

- Executa em segundo plano
- Mostra apenas a URL no terminal
- Continua executando mesmo se você fechar o terminal atual
- Para encerrar: `pkill -f ngrok`

### 3. Modo Serviço (para uso permanente)

```bash
sudo ./start-ngrok-service.sh
```

- Instala o ngrok como serviço do sistema
- Inicia automaticamente quando o servidor reinicia
- Permanece ativo independentemente do terminal
- Gerenciado via comandos systemd:
  - Status: `sudo systemctl status ngrok`
  - Parar: `sudo systemctl stop ngrok`
  - Reiniciar: `sudo systemctl restart ngrok`

## Alternar entre as versões (com e sem ngrok)

```bash
# Para usar o ngrok
git checkout configuracao-ngrok

# Para voltar à versão normal
git checkout humanizacao-respostas
```

## Importante

- A URL do ngrok muda a cada vez que o serviço é reiniciado
- Para usar um domínio fixo, é necessário um plano pago do ngrok
- O ngrok gratuito tem limitações de conexões simultâneas

## Configuração Atual

A configuração atual deste branch:
- O Docker escuta na porta 80 (alterado de 8081)
- O ngrok está configurado com o token de autenticação fornecido
- O painel de administração do ngrok é acessível em http://localhost:4040 