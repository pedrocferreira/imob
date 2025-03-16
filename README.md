# Sistema de Imóveis Nova Torres

Este projeto consiste em um sistema completo para coletar, processar e consultar dados sobre imóveis disponíveis na Nova Torres Imobiliária. O sistema inclui um scraper para coleta de dados e um assistente virtual baseado em IA para responder perguntas sobre os imóveis.

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
├── baixar_imagens.py          # Script para baixar imagens dos imóveis
└── run.py                     # Script para execução do processo completo
```

## Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd <nome-do-repositorio>
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
pip install -r requirements_rag.txt
```

3. Configure a API da OpenAI (opcional, para melhores resultados):
   - Edite o arquivo `rag/.env`
   - Adicione sua chave: `OPENAI_API_KEY=sua_chave_aqui`

## Uso

### Coleta de Dados

Para executar o processo de raspagem e preparação de dados:

```bash
python run.py
```

### Assistente Virtual

1. Processar os dados para o sistema RAG:
```bash
python rag/run_rag.py process
```

2. Iniciar a interface web:
```bash
python rag/run_rag.py server
```
Acesse http://localhost:8000 no navegador.

3. Interface de linha de comando:
```bash
python rag/run_rag.py cli
```

## Funcionalidades

- Busca de imóveis por localização, preço, quantidade de quartos, etc.
- Perguntas em linguagem natural sobre imóveis específicos
- Visualização de imagens dos imóveis
- Respostas detalhadas sobre características, localização e vantagens dos imóveis

## Licença

[Especificar a licença do projeto]

## Autor

[Seu nome/organização] 