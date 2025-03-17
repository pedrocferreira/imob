# Sistema de Imóveis Nova Torres

Este projeto consiste em um sistema completo para coletar, processar e consultar dados sobre imóveis disponíveis na Nova Torres Imobiliária. O sistema inclui um scraper para coleta de dados e um assistente virtual baseado em IA para responder perguntas sobre os imóveis.

## Acesso ao Sistema em Produção

O assistente imobiliário está disponível online:

**URL**: [http://ec2-13-38-76-17.eu-west-3.compute.amazonaws.com:8081](http://ec2-13-38-76-17.eu-west-3.compute.amazonaws.com:8081)

**Recursos disponíveis**:
- Interface web completa do assistente
- Busca de imóveis em tempo real
- Visualização de detalhes com fotos
- Interação em linguagem natural

## Componentes do Sistema

### 1. Coleta de Dados (Scraper)
- Extração automática de informações sobre imóveis do site da Nova Torres
- Download de fotos disponíveis para cada imóvel
- Geração de conjuntos de dados estruturados

### 2. Assistente Virtual de IA (RAG)
- Sistema de Retrieval Augmented Generation (RAG)
- Responde perguntas em linguagem natural sobre os imóveis
- Interface web amigável para consultas
- Interface de linha de comando para testes rápidos
- **Novo**: Personalização de respostas com base nos dados do cliente
- **Novo**: Gerenciamento de sessões para manter contexto nas conversas

## Estrutura do Projeto

```
projeto/
├── data/                      # Dados dos imóveis coletados
├── rag/                       # Sistema RAG (Retrieval Augmented Generation)
│   ├── app.py                 # API FastAPI
│   ├── assistente.py          # Classe do assistente imobiliário
│   ├── templates/             # Templates da interface web
│   └── run_rag.py             # Script de inicialização
├── src/                       # Scripts de coleta de dados
│   ├── scraper.py             # Script principal de raspagem
│   ├── scraper_v2.py          # Versão melhorada do scraper
│   └── prepare_data.py        # Preparação dos dados para IA
├── Dockerfile                 # Configuração para criação da imagem Docker
├── docker-compose.yml         # Configuração do ambiente Docker
├── .dockerignore              # Arquivos ignorados no contexto Docker
├── start-docker.sh            # Script para iniciar o sistema via Docker
├── baixar_imagens.py          # Script para baixar imagens dos imóveis
└── run.py                     # Script para execução do processo completo
```

## Instalação

### Método 1: Instalação Local

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd <nome-do-repositorio>
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure a API da OpenAI (opcional, para melhores resultados):
   - Edite o arquivo `rag/.env`
   - Adicione sua chave: `OPENAI_API_KEY=sua_chave_aqui`
   - Configure o modelo: `LLM_MODEL=gpt-3.5-turbo-0125` (ou outro modelo disponível)

### Método 2: Instalação via Docker (Recomendado)

1. Clone o repositório e prepare o ambiente:
```bash
git clone <url-do-repositorio>
cd <nome-do-repositorio>
```

2. Configure suas variáveis de ambiente:
```bash
# Crie o arquivo .env se não existir
touch rag/.env
# Edite o arquivo e adicione:
# OPENAI_API_KEY=sua_chave_aqui
# LLM_MODEL=gpt-3.5-turbo-0125
# HOST=0.0.0.0
# PORT=8080
```

3. Execute o script de inicialização Docker:
```bash
chmod +x start-docker.sh
./start-docker.sh
```

## Uso

### Coleta de Dados

Para executar o processo de raspagem e preparação de dados:

```bash
python run.py
```

### Assistente Virtual

#### Método 1: Execução Local

1. Processar os dados para o sistema RAG:
```bash
python rag/run_rag.py process
```

2. Iniciar a interface web:
```bash
python rag/run_rag.py server
```
Acesse http://localhost:8080 no navegador.

3. Interface de linha de comando:
```bash
python rag/run_rag.py cli
```

#### Método 2: Execução via Docker

Após iniciar o Docker com o script `start-docker.sh`:

1. Acesse a interface web em: http://localhost:8081

2. Para ver os logs da aplicação:
```bash
docker-compose logs -f
```

3. Para parar o serviço:
```bash
docker-compose down
```

## Funcionalidades

- Busca de imóveis por localização, preço, quantidade de quartos, etc.
- Perguntas em linguagem natural sobre imóveis específicos
- Visualização de imagens dos imóveis
- Respostas detalhadas sobre características, localização e vantagens dos imóveis
- **Novo**: Memória de cliente - o assistente lembra o nome e preferências do cliente
- **Novo**: Histórico de conversas - mantém o contexto entre perguntas na mesma sessão
- **Novo**: Personalização regional - respostas adaptadas ao estilo regional brasileiro

## Solução de Problemas

### Problemas com Docker

- **Porta em uso**: O script `start-docker.sh` detecta automaticamente se a porta está em uso e oferece opções para resolver
- **Logs**: Use `docker-compose logs -f` para ver logs detalhados em caso de falhas
- **Reiniciar**: Use `docker-compose down && ./start-docker.sh` para reiniciar completamente o sistema

## Licença

[Especificar a licença do projeto]

## Autor

[Seu nome/organização] 