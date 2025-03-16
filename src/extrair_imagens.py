import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

# Configurações
BASE_URL = "https://www.novatorres.com.br"
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
DATA_FILE = os.path.join(OUTPUT_DIR, "imoveis.json")
UPDATED_DATA_FILE = os.path.join(OUTPUT_DIR, "imoveis_com_imagens.json")

# Garantir que os diretórios existam
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def obter_pagina(url):
    """Obtém o conteúdo de uma página e retorna o objeto BeautifulSoup."""
    try:
        print(f"Acessando: {url}")
        
        # Fazer a requisição com retry
        for tentativa in range(3):
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
                break
            except Exception as e:
                print(f"Tentativa {tentativa+1} falhou: {e}")
                if tentativa < 2:  # Se não for a última tentativa
                    print("Tentando novamente em 5 segundos...")
                    time.sleep(5)
                else:
                    raise  # Re-lança a exceção se todas as tentativas falharem
        
        # Processar o conteúdo
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def extrair_imagens_royal_slider(soup):
    """Extrai imagens específicas do componente royalSlider usado no site."""
    imagens = []
    
    # Método 1: Extrair das miniaturas (mais confiável)
    miniaturas = soup.select(".rsThumb img.rsTmb, .rsNavItem img")
    for img in miniaturas:
        if img.has_attr('src'):
            img_url = img['src']
            # Corrigir URLs relativos (que começam com //)
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            
            # Substituir '/it/' por '/il/' para obter imagens em tamanho maior
            # it = thumbnail, im = média, il = grande
            img_url_grande = img_url.replace('/it/', '/il/')
            
            if img_url_grande not in imagens:
                imagens.append(img_url_grande)
    
    # Método 2: Extrair das imagens principais
    slides = soup.select(".rsSlide img.rsImg, .rsMainSlideImage")
    for img in slides:
        if img.has_attr('src'):
            img_url = img['src']
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
                
            # Verificar atributo data-rsbigimg para imagens em tamanho maior
            if img.has_attr('data-rsbigimg'):
                img_url_grande = img['data-rsbigimg']
                if img_url_grande.startswith('//'):
                    img_url_grande = 'https:' + img_url_grande
                
                if img_url_grande not in imagens:
                    imagens.append(img_url_grande)
            elif img_url not in imagens:
                imagens.append(img_url)
    
    # Método 3: Buscar em spans com background-image
    bg_spans = soup.select("span.bg")
    for span in bg_spans:
        style = span.get('style', '')
        match = re.search(r'background-image: url\((.*?)\)', style)
        if match:
            img_url = match.group(1)
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
                
            # Substituir '/it/' por '/il/' para obter imagens em tamanho maior
            img_url_grande = img_url.replace('/it/', '/il/')
            
            if img_url_grande not in imagens:
                imagens.append(img_url_grande)
    
    return imagens

def extrair_imagens_imovel(link):
    """Extrai apenas as imagens de um imóvel."""
    soup = obter_pagina(link)
    if not soup:
        return []
    
    try:
        imagens = []
        
        # Método principal: extrator específico para o royalSlider
        royal_slider_images = extrair_imagens_royal_slider(soup)
        if royal_slider_images:
            imagens.extend(royal_slider_images)
        
        # Métodos alternativos se o royalSlider não funcionar
        if not imagens:
            # 1. Buscar todas as imagens na página
            todas_imagens = soup.select("img")
            for img in todas_imagens:
                if img.has_attr('src'):
                    img_url = img['src']
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif not img_url.startswith('http'):
                        img_url = urljoin(BASE_URL, img_url)
                    
                    # Filtrar imagens pequenas, ícones e placeholders
                    if (not any(termo in img_url.lower() for termo in ["icon", "logo", "placeholder"]) and
                        not img_url.endswith(".gif")):
                        imagens.append(img_url)
        
        # Remover duplicatas mantendo a ordem
        imagens_unicas = []
        for img in imagens:
            if img not in imagens_unicas:
                imagens_unicas.append(img)
        
        return imagens_unicas
    
    except Exception as e:
        print(f"Erro ao extrair imagens do imóvel {link}: {e}")
        return []

def baixar_imagens(codigo, imagens):
    """Baixa as imagens do imóvel e retorna os caminhos locais."""
    diretorio_imovel = os.path.join(IMAGES_DIR, codigo)
    os.makedirs(diretorio_imovel, exist_ok=True)
    
    caminhos_locais = []
    
    print(f"Baixando {len(imagens)} imagens para o imóvel {codigo}...")
    
    for i, img_url in enumerate(imagens):
        try:
            if not img_url.startswith('http'):
                continue
            
            response = requests.get(img_url, headers=HEADERS, stream=True, timeout=15)
            
            if response.status_code == 200:
                # Determinar extensão
                content_type = response.headers.get('Content-Type', '')
                ext = '.jpg'  # Padrão
                
                if 'image/png' in content_type:
                    ext = '.png'
                elif 'image/gif' in content_type:
                    ext = '.gif'
                elif 'image/webp' in content_type:
                    ext = '.webp'
                
                # Salvar a imagem
                nome_arquivo = f"{i+1}{ext}"
                caminho_arquivo = os.path.join(diretorio_imovel, nome_arquivo)
                
                with open(caminho_arquivo, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                caminho_relativo = os.path.relpath(caminho_arquivo, OUTPUT_DIR)
                caminhos_locais.append(caminho_relativo)
                print(f"  ✓ Imagem {i+1} salva em {caminho_relativo}")
            else:
                print(f"  ✗ Erro ao baixar imagem {i+1}: Status code {response.status_code}")
        
        except Exception as e:
            print(f"  ✗ Erro ao baixar imagem {i+1}: {e}")
    
    return caminhos_locais

def main():
    """Função principal para extrair apenas as imagens."""
    print("\n" + "="*60)
    print("EXTRAÇÃO DE IMAGENS - NOVA TORRES IMOBILIÁRIA")
    print("="*60)
    
    # Carregar os imóveis já extraídos
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            imoveis = json.load(f)
        print(f"Carregados {len(imoveis)} imóveis do arquivo {DATA_FILE}")
    except Exception as e:
        print(f"Erro ao carregar arquivo de imóveis: {e}")
        return
    
    tempo_inicio = time.time()
    total_imagens = 0
    
    # Limitar a apenas 10 imóveis para teste
    imoveis_teste = imoveis
    print(f"Limitando o processamento a 10 imóveis para teste")
    
    # Para cada imóvel, extrair e baixar as imagens
    for i, imovel in enumerate(tqdm(imoveis_teste, desc="Processando imóveis")):
        print(f"\n[Imóvel {i+1}/{len(imoveis_teste)}] {imovel['codigo']}")
        
        link = imovel['link']
        print(f"Extraindo imagens de: {link}")
        
        # Extrair imagens
        imagens = extrair_imagens_imovel(link)
        print(f"Encontradas {len(imagens)} imagens")
        
        # Baixar imagens
        caminhos_locais = baixar_imagens(imovel['codigo'], imagens)
        
        # Atualizar o objeto do imóvel
        imovel['imagens'] = imagens
        imovel['imagens_locais'] = caminhos_locais
        total_imagens += len(caminhos_locais)
        
        # Salvar progresso a cada imóvel para teste
        with open(UPDATED_DATA_FILE, 'w', encoding='utf-8') as f:
            # Manter apenas os imóveis processados no arquivo de teste
            imoveis_processados = imoveis_teste[:i+1]
            json.dump(imoveis_processados, f, ensure_ascii=False, indent=4)
        print(f"Progresso salvo em {UPDATED_DATA_FILE}")
        
        # Esperar para não sobrecarregar o servidor
        if i < len(imoveis_teste) - 1:
            print("Aguardando 3 segundos antes do próximo imóvel...")
            time.sleep(3)
    
    # Tempo total
    tempo_total = time.time() - tempo_inicio
    minutos = int(tempo_total // 60)
    segundos = int(tempo_total % 60)
    
    print("\n" + "="*60)
    print(f"EXTRAÇÃO DE IMAGENS CONCLUÍDA EM {minutos} minutos e {segundos} segundos!")
    print(f"Total de imóveis processados: {len(imoveis_teste)}")
    print(f"Total de imagens extraídas: {total_imagens}")
    print("="*60)

if __name__ == "__main__":
    main() 