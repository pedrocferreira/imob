import os
import json
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import shutil
from urllib.parse import urljoin

# Configurações
DATA_DIR = Path("data")
IMOVEIS_JSON = DATA_DIR / "imoveis.json"
IMAGES_DIR = DATA_DIR / "images_new"
ORIG_IMAGES_DIR = DATA_DIR / "images"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def carregar_imoveis():
    """Carrega os dados dos imóveis do arquivo JSON."""
    print(f"Carregando dados de {IMOVEIS_JSON}...")
    
    if not IMOVEIS_JSON.exists():
        print(f"Arquivo {IMOVEIS_JSON} não encontrado!")
        return []
    
    with open(IMOVEIS_JSON, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    print(f"Carregados {len(dados)} imóveis.")
    return dados

def obter_imagens_imovel(url, codigo):
    """Obtém imagens de um imóvel a partir da sua URL."""
    print(f"Processando imóvel {codigo}: {url}")
    
    try:
        # Fazer a requisição com retry
        for tentativa in range(3):
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
                break
            except Exception as e:
                print(f"  Tentativa {tentativa+1} falhou: {e}")
                if tentativa < 2:
                    print("  Tentando novamente em 5 segundos...")
                    time.sleep(5)
                else:
                    raise
        
        # Processar o conteúdo HTML com BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Estratégia 1: Buscar na galeria de imagens
        imagens = []
        
        # Buscar todas as imagens na página
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            
            # Filtrar imagens irrelevantes
            if not src or any(x in src.lower() for x in ['logo', 'icon', 'banner']):
                continue
                
            # Corrigir URLs relativos
            if src.startswith('//'):
                src = 'https:' + src
            elif not src.startswith('http'):
                src = urljoin(url, src)
            
            # Adicionar à lista se não for duplicada
            if src not in imagens:
                imagens.append(src)
        
        # Imprimir estatísticas
        print(f"  Encontradas {len(imagens)} imagens potenciais")
        
        # Filtrar para imagens do imóvel apenas (heurística simples)
        imagens_imovel = [img for img in imagens if any(x in img.lower() for x in ['imovel', 'property', 'galeria', 'foto', 'image'])]
        
        # Se não encontrou nada específico, usar todas as imagens maiores
        if not imagens_imovel:
            print("  Usando todas as imagens disponíveis")
            imagens_imovel = imagens
        
        return imagens_imovel
        
    except Exception as e:
        print(f"  Erro ao processar imóvel {codigo}: {e}")
        return []

def baixar_imagem(img_url, diretorio, nome_arquivo):
    """Baixa uma imagem e salva no diretório especificado."""
    caminho_completo = diretorio / nome_arquivo
    
    try:
        response = requests.get(img_url, headers=HEADERS, stream=True, timeout=10)
        
        if response.status_code == 200:
            with open(caminho_completo, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"    ✓ Imagem salva em {caminho_completo}")
            return True
        else:
            print(f"    ✗ Erro ao baixar imagem: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    ✗ Erro ao baixar imagem: {e}")
        return False

def usar_imagens_existentes(codigo):
    """Verifica se já existem imagens para este imóvel e as copia."""
    origem = ORIG_IMAGES_DIR / str(codigo)
    destino = IMAGES_DIR / str(codigo)
    
    # Se o diretório de origem existe e tem arquivos
    if origem.exists() and list(origem.glob('*.jpg')):
        print(f"  Copiando imagens existentes para o imóvel {codigo}")
        
        # Garantir que o diretório de destino exista
        destino.mkdir(exist_ok=True, parents=True)
        
        # Copiar cada arquivo
        for i, arquivo in enumerate(sorted(origem.glob('*.jpg'))):
            novo_nome = f"{i+1}.jpg"
            shutil.copy2(arquivo, destino / novo_nome)
            print(f"    ✓ Copiado {arquivo.name} para {novo_nome}")
        
        return True
    return False

def baixar_imagens_alternativas(codigo):
    """Baixa imagens de placeholder para garantir que sempre haja uma imagem."""
    diretorio = IMAGES_DIR / str(codigo)
    diretorio.mkdir(exist_ok=True, parents=True)
    
    # Se não tem nenhum arquivo, criar pelo menos um placeholder
    if not list(diretorio.glob('*.jpg')):
        print(f"  Criando imagem placeholder para imóvel {codigo}")
        placeholder_url = f"https://placehold.co/800x600/0d6efd/white?text=Im%C3%B3vel%20{codigo}"
        baixar_imagem(placeholder_url, diretorio, "1.jpg")
        return True
    
    return False

def main():
    """Função principal."""
    print("\n===== BAIXADOR DE IMAGENS DE IMÓVEIS =====\n")
    
    # Criar diretório para as novas imagens
    IMAGES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Carregar os imóveis
    imoveis = carregar_imoveis()
    if not imoveis:
        print("Nenhum imóvel encontrado. Abortando.")
        return
    
    # Processar cada imóvel
    # Lista de códigos prioritários
    codigos_prioritarios = ["-1800"]
    processados = set()
    
    # Primeiro processar os imóveis prioritários
    print("Processando imóveis prioritários...")
    for codigo_prioritario in codigos_prioritarios:
        for idx, imovel in enumerate(imoveis):
            if imovel.get("codigo") == codigo_prioritario:
                codigo = imovel.get("codigo", "")
                link = imovel.get("link", "")
                
                if not codigo or not link:
                    print(f"Imóvel prioritário {codigo_prioritario} não tem código ou link. Pulando.")
                    continue
                
                print(f"\n[Prioritário] Processando imóvel {codigo}")
                
                # Criar diretório para este imóvel
                diretorio_imovel = IMAGES_DIR / str(codigo)
                diretorio_imovel.mkdir(exist_ok=True, parents=True)
                
                # Verificar se já temos imagens para este imóvel
                if usar_imagens_existentes(codigo):
                    processados.add(codigo)
                    continue
                
                # Obter imagens da página do imóvel
                imagens = obter_imagens_imovel(link, codigo)
                
                # Baixar as imagens
                for j, img_url in enumerate(imagens[:10]):  # Limitar a 10 imagens por imóvel
                    nome_arquivo = f"{j+1}.jpg"
                    baixar_imagem(img_url, diretorio_imovel, nome_arquivo)
                
                # Se não encontrou imagens, criar pelo menos um placeholder
                if not imagens:
                    baixar_imagens_alternativas(codigo)
                
                processados.add(codigo)
                break
    
    # Processar os demais imóveis
    for i, imovel in enumerate(tqdm(imoveis[:20], desc="Processando imóveis")):  # Limitando a 20 imóveis no total
        codigo = imovel.get("codigo", "")
        
        # Pular os que já foram processados
        if codigo in processados:
            continue
            
        link = imovel.get("link", "")
        
        if not codigo or not link:
            print(f"Imóvel {i} não tem código ou link. Pulando.")
            continue
        
        print(f"\n[{i+1}/{len(imoveis)}] Processando imóvel {codigo}")
        
        # Criar diretório para este imóvel
        diretorio_imovel = IMAGES_DIR / str(codigo)
        diretorio_imovel.mkdir(exist_ok=True, parents=True)
        
        # Verificar se já temos imagens para este imóvel
        if usar_imagens_existentes(codigo):
            continue
        
        # Obter imagens da página do imóvel
        imagens = obter_imagens_imovel(link, codigo)
        
        # Baixar as imagens
        for j, img_url in enumerate(imagens[:10]):  # Limitar a 10 imagens por imóvel
            nome_arquivo = f"{j+1}.jpg"
            baixar_imagem(img_url, diretorio_imovel, nome_arquivo)
        
        # Se não encontrou imagens, criar pelo menos um placeholder
        if not imagens:
            baixar_imagens_alternativas(codigo)
        
        # Pausa entre imóveis para não sobrecarregar o servidor
        if i < len(imoveis) - 1:
            time.sleep(1)
    
    print("\n===== PROCESSO CONCLUÍDO =====")
    print(f"As imagens foram salvas em: {IMAGES_DIR}")
    print("Para usar estas imagens, modifique o arquivo app.py para apontar para o novo diretório.")

if __name__ == "__main__":
    main() 