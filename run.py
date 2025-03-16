import os
import sys
import argparse
import time

def executar_comando(comando):
    """Executa um comando no sistema operacional."""
    print(f"\n>>> Executando: {comando}")
    retorno = os.system(comando)
    if retorno != 0:
        print(f"Erro na execução do comando. Código de retorno: {retorno}")
        return False
    return True

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Execução de scripts para IA de Imobiliária')
    parser.add_argument('--scraper', action='store_true', help='Executar apenas o scraper')
    parser.add_argument('--preparar', action='store_true', help='Executar apenas a preparação de dados')
    parser.add_argument('--v2', action='store_true', help='Usar a versão 2 do scraper (mais robusta)')
    parser.add_argument('--simples', action='store_true', help='Usar versão simples (sem Selenium/navegador)')
    parser.add_argument('--imagens', action='store_true', help='Executar apenas a extração de imagens')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SISTEMA DE RASPAGEM E PREPARAÇÃO DE DADOS - IMOBILIÁRIA")
    print("=" * 60)
    
    # Verificar se as dependências estão instaladas
    print("\nVerificando dependências...")
    if not executar_comando("pip3 install -r requirements.txt"):
        print("Falha ao instalar dependências. Abortando.")
        return
    
    tempo_inicio = time.time()
    
    # Execução específica para extração de imagens
    if args.imagens:
        print("\n" + "=" * 60)
        print("ETAPA ESPECIAL: EXTRAÇÃO DE IMAGENS DOS IMÓVEIS")
        print("=" * 60)
        
        if not executar_comando("python3 src/extrair_imagens.py"):
            print("Falha na extração de imagens. Abortando.")
            return
    
    # Execução dos scripts conforme os argumentos (se não for apenas extração de imagens)
    elif args.scraper or (not args.scraper and not args.preparar and not args.imagens):
        print("\n" + "=" * 60)
        print("ETAPA 1: RASPAGEM DE DADOS")
        print("=" * 60)
        
        # Decidir qual script usar
        if args.simples:
            scraper_script = "src/scraper_requests.py"
            print("Usando versão simplificada do scraper (sem Selenium/navegador)")
        else:
            scraper_script = "src/scraper_v2.py" if args.v2 else "src/scraper.py"
            print(f"Usando script: {scraper_script}")
        
        if not executar_comando(f"python3 {scraper_script}"):
            print("Falha na raspagem de dados. Abortando.")
            return
    
    if args.preparar or (not args.scraper and not args.preparar and not args.imagens):
        print("\n" + "=" * 60)
        print("ETAPA 2: PREPARAÇÃO DOS DADOS PARA IA")
        print("=" * 60)
        
        if not executar_comando("python3 src/prepare_data.py"):
            print("Falha na preparação dos dados. Abortando.")
            return
    
    tempo_total = time.time() - tempo_inicio
    minutos = int(tempo_total // 60)
    segundos = int(tempo_total % 60)
    
    print("\n" + "=" * 60)
    print(f"PROCESSO CONCLUÍDO EM {minutos} minutos e {segundos} segundos!")
    print("=" * 60)
    
    # Exibir resumo dos arquivos gerados
    print("\nArquivos gerados:")
    if os.path.exists("data/imoveis.json"):
        print(f"- data/imoveis.json ({os.path.getsize('data/imoveis.json') / 1024:.1f} KB)")
    
    if os.path.exists("data/imoveis_com_imagens.json"):
        print(f"- data/imoveis_com_imagens.json ({os.path.getsize('data/imoveis_com_imagens.json') / 1024:.1f} KB)")
    
    if os.path.exists("data/imoveis.csv"):
        print(f"- data/imoveis.csv ({os.path.getsize('data/imoveis.csv') / 1024:.1f} KB)")
    
    if os.path.exists("data/dataset_treinamento.json"):
        print(f"- data/dataset_treinamento.json ({os.path.getsize('data/dataset_treinamento.json') / 1024:.1f} KB)")
    
    if os.path.exists("data/dataset_treinamento.csv"):
        print(f"- data/dataset_treinamento.csv ({os.path.getsize('data/dataset_treinamento.csv') / 1024:.1f} KB)")
    
    if os.path.exists("data/contexto_geral.md"):
        print(f"- data/contexto_geral.md ({os.path.getsize('data/contexto_geral.md') / 1024:.1f} KB)")
    
    # Contar imagens baixadas
    total_imagens = 0
    for raiz, dirs, arquivos in os.walk("data/images"):
        for arquivo in arquivos:
            if arquivo.endswith((".jpg", ".png", ".gif", ".webp")):
                total_imagens += 1
    
    print(f"- Total de imagens baixadas: {total_imagens}")
    
    print("\nPróximos passos:")
    print("1. Verifique os dados extraídos em data/imoveis.json e data/imoveis.csv")
    print("2. Use os dados de treinamento em data/dataset_treinamento.json para treinar sua IA")
    print("3. Use o contexto geral em data/contexto_geral.md como referência para a IA")

if __name__ == "__main__":
    main() 