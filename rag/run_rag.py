#!/usr/bin/env python3
"""Script de inicialização para o sistema RAG."""

import os
import sys
import argparse
from pathlib import Path

# Adicionar o diretório do projeto ao PATH
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

def check_openai_key():
    """Verifica se a chave da OpenAI está configurada."""
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
    
    key = os.getenv("OPENAI_API_KEY")
    if not key or key == "sua_chave_aqui":
        print("\nAVISO: Você precisa configurar sua chave da OpenAI API!")
        print("Por favor, edite o arquivo rag/.env e adicione sua chave API.")
        return False
    return True

def process_data():
    """Processa os dados e cria o banco de dados vetorial."""
    print("\n=== Processando dados e criando banco de dados vetorial ===\n")
    
    # Verificar se a chave da OpenAI está configurada
    check_openai_key()
    
    # Importar e executar o processador de dados
    from process_data import main as process_main
    print("Usando solução alternativa baseada em arquivo JSON (sem ChromaDB)")
    process_main()

def run_api():
    """Executa o servidor FastAPI."""
    print("\n=== Iniciando servidor da API ===\n")
    
    # Importar e executar o app
    from app import main as app_main
    app_main()

def run_cli():
    """Executa interface de linha de comando para testes."""
    print("\n=== Iniciando interface de linha de comando ===\n")
    
    # Importar o assistente e executar perguntas interativas
    from assistente import AssistenteImobiliaria
    
    try:
        assistente = AssistenteImobiliaria()
        print("Assistente inicializado com sucesso!")
        print("\nDigite suas perguntas sobre imóveis da Nova Torres Imobiliária.")
        print("Digite 'sair' para encerrar.\n")
        
        while True:
            pergunta = input("\n> ")
            if pergunta.lower() in ['sair', 'exit', 'quit', 'q']:
                print("Encerrando...")
                break
            
            if not pergunta.strip():
                continue
            
            resultado = assistente.responder(pergunta)
            print("\nResposta:", resultado['resposta'])
            
            if resultado['imoveis_relacionados']:
                print("\nImóveis relacionados:")
                for imovel in resultado['imoveis_relacionados']:
                    print(f"- {imovel['codigo']}: {imovel['titulo']} - {imovel['preco']}")
            
            if resultado['imagens_relacionadas']:
                print("\nImagens disponíveis:")
                for i, img in enumerate(resultado['imagens_relacionadas'][:3]):
                    print(f"- Imagem {i+1}: {img}")
    
    except Exception as e:
        print(f"Erro ao inicializar o assistente: {e}")
        return

def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description="Sistema RAG para Imobiliária Nova Torres")
    
    # Definir subparsers para diferentes comandos
    subparsers = parser.add_subparsers(dest="comando", help="Comando a ser executado")
    
    # Subparser para processar os dados
    process_parser = subparsers.add_parser("process", help="Processar dados e criar banco de dados vetorial")
    
    # Subparser para executar o servidor
    server_parser = subparsers.add_parser("server", help="Iniciar o servidor da API")
    
    # Subparser para a interface de linha de comando
    cli_parser = subparsers.add_parser("cli", help="Iniciar interface de linha de comando")
    
    # Subparser para o comando de ajuda
    help_parser = subparsers.add_parser("help", help="Exibir informações de ajuda")
    
    # Obter argumentos
    args = parser.parse_args()
    
    # Verificar se a chave da OpenAI está configurada
    has_key = check_openai_key()
    
    if args.comando == "process":
        if not has_key:
            print("Você pode continuar com os embeddings locais, mas será mais lento.")
            response = input("Deseja continuar? (s/N): ")
            if response.lower() not in ['s', 'sim', 'y', 'yes']:
                return
        process_data()
    
    elif args.comando == "server":
        if not has_key:
            print("A API requer uma chave da OpenAI para funcionar.")
            return
        run_api()
    
    elif args.comando == "cli":
        if not has_key:
            print("A interface de linha de comando requer uma chave da OpenAI para funcionar.")
            return
        run_cli()
    
    elif args.comando == "help" or not args.comando:
        print("\nSistema RAG para Imobiliária Nova Torres")
        print("=======================================\n")
        print("Este sistema permite usar IA para responder perguntas sobre imóveis da Nova Torres Imobiliária.\n")
        print("Passos para utilização:")
        print("1. Configure sua chave da OpenAI no arquivo 'rag/.env'")
        print("2. Execute 'python rag/run_rag.py process' para processar os dados e criar o banco de dados vetorial")
        print("3. Execute 'python rag/run_rag.py server' para iniciar o servidor web")
        print("   ou 'python rag/run_rag.py cli' para usar a interface de linha de comando\n")
        print("Comandos disponíveis:")
        print("- process: Processa os dados e cria o banco de dados vetorial")
        print("- server: Inicia o servidor web para a interface gráfica")
        print("- cli: Inicia a interface de linha de comando para testes rápidos")
        print("- help: Exibe esta ajuda\n")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 