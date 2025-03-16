# Sistema RAG para Imobiliária Nova Torres

Este é um sistema de Retrieval Augmented Generation (RAG) desenvolvido para a Imobiliária Nova Torres. O sistema permite responder perguntas sobre os imóveis disponíveis usando processamento de linguagem natural.

## Estrutura do Projeto

```
rag/
├── .env                  # Configurações e API keys
├── app.py                # API FastAPI
├── assistente.py         # Classe do assistente imobiliário
├── db/                   # Banco de dados vetorial
├── process_data.py       # Processador de dados para gerar embeddings
├── run_rag.py            # Script de inicialização
└── templates/            # Templates HTML para interface web
    └── index.html        # Interface da aplicação
```

## Requisitos

- Python 3.8+
- Chave da API OpenAI (para melhores resultados)
- Dados de imóveis extraídos pelo scraper (já devem estar em `data/`)

## Configuração

1. Instale as dependências necessárias:
   ```
   pip install -r requirements_rag.txt
   ```

2. Configure sua chave da API OpenAI:
   - Edite o arquivo `rag/.env`
   - Adicione sua chave: `OPENAI_API_KEY=sua_chave_aqui`

## Uso

O sistema pode ser utilizado de três formas diferentes:

### 1. Processamento de dados

Para processar os dados e criar o banco de dados vetorial:

```bash
python rag/run_rag.py process
```

### 2. Interface Web

Para iniciar a interface web:

```bash
python rag/run_rag.py server
```

Depois, acesse http://localhost:8000 no seu navegador.

### 3. Interface de Linha de Comando

Para iniciar a interface de linha de comando:

```bash
python rag/run_rag.py cli
```

## Funcionalidades

O sistema permite:

- Responder perguntas sobre imóveis específicos
- Buscar imóveis por características (número de quartos, preço, localização)
- Apresentar imagens relacionadas aos imóveis
- Fornecer detalhes e comparações entre propriedades

## Como funciona

O sistema usa Retrieval Augmented Generation (RAG), que:

1. Gera embeddings (representações vetoriais) dos dados de imóveis
2. Armazena esses embeddings em um banco de dados vetorial (ChromaDB)
3. Quando uma pergunta é feita, encontra as informações mais relevantes
4. Usa um modelo de linguagem para gerar uma resposta contextualizada

## Solução de problemas

- Se o sistema responde incorretamente, tente reprocessar os dados com `python rag/run_rag.py process`
- Verifique se a chave da API OpenAI está configurada corretamente
- Para problemas com embeddings locais, verifique se o modelo está sendo baixado corretamente

## Limitações

- O sistema responde apenas com base nos dados extraídos dos imóveis
- O desempenho do modelo local de embeddings é inferior ao da OpenAI
- A interface web suporta apenas consultas baseadas em texto (sem upload de imagens) 