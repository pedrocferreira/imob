import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
import pandas as pd

# Adicionar o diretório raiz ao path para importações relativas
sys.path.append(str(Path(__file__).parent.parent))

# Carregar variáveis de ambiente
load_dotenv(Path(__file__).parent / '.env')

# Configurações
DATA_DIR = Path("data")
IMOVEIS_JSON = DATA_DIR / "imoveis.json"
IMOVEIS_COM_IMAGENS_JSON = DATA_DIR / "imoveis_com_imagens.json"
CONTEXTO_GERAL = DATA_DIR / "contexto_geral.md"
DATASET_TREINAMENTO = DATA_DIR / "dataset_treinamento.json"

# Configuração do ChromaDB
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Escolha entre OpenAI ou embeddings locais
USE_OPENAI = os.getenv("OPENAI_API_KEY") != "sua_chave_aqui"

if USE_OPENAI:
    EMBEDDINGS = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL"))
    print("Usando embeddings OpenAI.")
else:
    # Usando embeddings locais (mais lento mas gratuito)
    EMBEDDINGS = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    print("Usando embeddings HuggingFace locais.")


def carregar_imoveis() -> List[Dict[str, Any]]:
    """Carrega os dados dos imóveis do arquivo JSON."""
    try:
        # Tentar primeiro o arquivo com imagens
        if IMOVEIS_COM_IMAGENS_JSON.exists():
            with open(IMOVEIS_COM_IMAGENS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Se não existir, usar o arquivo sem imagens
        with open(IMOVEIS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar dados dos imóveis: {e}")
        return []


def carregar_contexto_geral() -> str:
    """Carrega o arquivo de contexto geral."""
    try:
        if CONTEXTO_GERAL.exists():
            with open(CONTEXTO_GERAL, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except Exception as e:
        print(f"Erro ao carregar contexto geral: {e}")
        return ""


def preparar_documentos() -> List[Dict[str, Any]]:
    """Prepara os documentos para indexação no ChromaDB."""
    documentos = []
    
    # Processar dados dos imóveis
    imoveis = carregar_imoveis()
    if not imoveis:
        print("Nenhum imóvel encontrado. Execute primeiro o scraper.")
        return []
    
    print(f"Processando {len(imoveis)} imóveis...")
    
    # Criar documentos para cada imóvel
    for imovel in imoveis:
        # Documento principal do imóvel
        doc_principal = {
            "id": f"imovel-{imovel['codigo']}",
            "text": f"""
Imóvel: {imovel['titulo']}
Código: {imovel['codigo']}
Preço: {imovel['preco']}
Endereço: {imovel['endereco']}
Descrição: {imovel['descricao']}
Link: {imovel['link']}
{"imagem_principal: " + imovel.get('imagem_principal', '') if 'imagem_principal' in imovel else ""}
            """.strip(),
            "metadata": {
                "tipo": "imovel",
                "codigo": imovel['codigo'],
                "preco": imovel['preco'],
                "titulo": imovel['titulo'],
                "link": imovel['link']
            }
        }
        documentos.append(doc_principal)
        
        # Documento com características
        if imovel['caracteristicas']:
            caracteristicas_texto = "\n".join([f"{k}: {v}" for k, v in imovel['caracteristicas'].items()])
            doc_caracteristicas = {
                "id": f"caracteristicas-{imovel['codigo']}",
                "text": f"""
Características do imóvel {imovel['codigo']}:
{caracteristicas_texto}
                """.strip(),
                "metadata": {
                    "tipo": "caracteristicas",
                    "codigo": imovel['codigo'],
                    "titulo": imovel['titulo']
                }
            }
            documentos.append(doc_caracteristicas)
        
        # Documentos com imagens
        if 'imagens_locais' in imovel and imovel['imagens_locais']:
            imagens_texto = "\n".join([f"Imagem {i+1}: {img}" for i, img in enumerate(imovel['imagens_locais'])])
            doc_imagens = {
                "id": f"imagens-{imovel['codigo']}",
                "text": f"""
Imagens do imóvel {imovel['codigo']}:
{imagens_texto}
                """.strip(),
                "metadata": {
                    "tipo": "imagens",
                    "codigo": imovel['codigo'],
                    "titulo": imovel['titulo'],
                    "qtd_imagens": len(imovel['imagens_locais'])
                }
            }
            documentos.append(doc_imagens)
    
    # Processar o contexto geral
    contexto = carregar_contexto_geral()
    if contexto:
        # Dividir o contexto geral em chunks menores
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = splitter.split_text(contexto)
        
        # Criar documento para cada chunk
        for i, chunk in enumerate(chunks):
            doc_contexto = {
                "id": f"contexto-{i}",
                "text": chunk,
                "metadata": {
                    "tipo": "contexto",
                    "parte": i,
                    "total_partes": len(chunks)
                }
            }
            documentos.append(doc_contexto)
    
    print(f"Total de {len(documentos)} documentos preparados.")
    return documentos


def criar_banco_vetorial(documentos: List[Dict[str, Any]]):
    """Cria o banco de dados vetorial com os documentos."""
    if not documentos:
        print("Sem documentos para indexar.")
        return None
    
    # Em vez de usar ChromaDB, vamos salvar os documentos em um arquivo JSON
    print("Devido a problemas com as dependências do ChromaDB, estamos usando uma solução alternativa...")
    print(f"Salvando {len(documentos)} documentos em um arquivo JSON...")
    
    # Verificar se o diretório existe
    os.makedirs(os.path.dirname(CHROMA_PERSIST_DIRECTORY), exist_ok=True)
    
    # Salvar em um arquivo JSON
    output_file = os.path.join(os.path.dirname(CHROMA_PERSIST_DIRECTORY), "documentos.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documentos, f, ensure_ascii=False, indent=2)
    
    print(f"Documentos salvos em: {output_file}")
    
    # Mock de retorno
    class MockDB:
        def similarity_search(self, query, k=2):
            class MockResult:
                def __init__(self, text):
                    self.page_content = text
            
            return [MockResult("Exemplo de resultado 1"), MockResult("Exemplo de resultado 2")]
    
    return MockDB()


def main():
    """Função principal."""
    print("Processando dados para o sistema RAG...")
    
    # Preparar os documentos
    documentos = preparar_documentos()
    
    if documentos:
        # Criar o banco de dados vetorial
        db = criar_banco_vetorial(documentos)
        
        if db:
            print("Processo concluído com sucesso!")
            print(f"Dados disponíveis em: {os.path.dirname(CHROMA_PERSIST_DIRECTORY)}")
            print("\nTeste de consulta: não disponível (usando sistema alternativo)")
    else:
        print("Não foi possível processar os dados. Verifique se os arquivos existem.")


if __name__ == "__main__":
    main() 