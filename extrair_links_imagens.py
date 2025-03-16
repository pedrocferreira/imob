import os
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import re

# Configurações
DATA_DIR = Path("data")
IMOVEIS_JSON = DATA_DIR / "imoveis.json"
IMOVEIS_COM_IMAGENS_JSON = DATA_DIR / "imoveis_com_links.json"

# Criar diretórios se não existirem
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Headers para simular um navegador real
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
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

def extrair_imagens_royal_slider(soup, url_base):
    """Extrai imagens específicas do componente royalSlider usado no site."""
    imagens = []
    
    # Método 1: Extrair das imagens do slider principal (melhor qualidade)
    slides_principais = soup.select(".rsSlide img.rsImg, .rsMainSlideImage, .royalSlider .rsSlide img")
    for img in slides_principais:
        # Tentar data-rsbigimg primeiro (melhor qualidade)
        if img.has_attr('data-rsbigimg'):
            img_url = img['data-rsbigimg']
        # Caso contrário, usar src
        elif img.has_attr('src'):
            img_url = img['src']
        else:
            continue
            
        # Corrigir URLs relativos
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif not img_url.startswith('http'):
            img_url = url_base + ('' if img_url.startswith('/') else '/') + img_url
        
        # Substituir para obter versão de maior qualidade
        img_url_grande = img_url.replace('/it/', '/il/').replace('/im/', '/il/')
        
        if img_url_grande not in imagens:
            imagens.append(img_url_grande)
    
    # Método 2: Buscar em spans com background-image
    bg_spans = soup.select(".royalSlider .rsSlide span.bg, .royalSlider span.bg")
    for span in bg_spans:
        style = span.get('style', '')
        match = re.search(r'background-image: url\((.*?)\)', style)
        if match:
            img_url = match.group(1)
            # Remover aspas se existirem
            img_url = img_url.strip("'").strip('"')
            
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif not img_url.startswith('http'):
                img_url = url_base + ('' if img_url.startswith('/') else '/') + img_url
                
            # Substituir para obter versão de maior qualidade
            img_url_grande = img_url.replace('/it/', '/il/').replace('/im/', '/il/')
            
            if img_url_grande not in imagens:
                imagens.append(img_url_grande)
    
    # Método 3: Miniaturas da galeria (converter para alta qualidade)
    miniaturas = soup.select(".rsThumb img.rsTmb, .rsNavItem img")
    for img in miniaturas:
        if img.has_attr('src'):
            img_url = img['src']
            
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif not img_url.startswith('http'):
                img_url = url_base + ('' if img_url.startswith('/') else '/') + img_url
            
            # Substituir '/it/' por '/il/' para obter imagens em tamanho maior
            img_url_grande = img_url.replace('/it/', '/il/').replace('/im/', '/il/')
            
            if img_url_grande not in imagens:
                imagens.append(img_url_grande)
    
    return imagens

def extrair_todas_imagens(soup, url_base):
    """Extrai todas as imagens da página como fallback."""
    imagens = []
    
    todas_img = soup.select("img")
    for img in todas_img:
        if img.has_attr('src'):
            img_url = img['src']
            
            # Ignorar imagens muito pequenas, ícones, etc.
            if any(termo in img_url.lower() for termo in ['icon', 'logo', 'banner', 'btn', 'button']):
                continue
                
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif not img_url.startswith('http'):
                img_url = url_base + ('' if img_url.startswith('/') else '/') + img_url
            
            # Tentar converter para versão grande
            img_url_grande = img_url.replace('/it/', '/il/').replace('/im/', '/il/')
            
            if img_url_grande not in imagens:
                imagens.append(img_url_grande)
    
    return imagens

def extrair_links_imagens(link, codigo):
    """Extrai apenas os links das imagens de um imóvel sem baixá-las."""
    try:
        print(f"Processando imóvel {codigo}: {link}")
        
        # Extrair o domínio base para URLs relativas
        url_parts = link.split('/')
        url_base = '/'.join(url_parts[:3])  # http(s)://dominio.com
        
        # Fazer a requisição com retry
        for tentativa in range(3):
            try:
                response = requests.get(link, headers=HEADERS, timeout=30)
                response.raise_for_status()
                break
            except Exception as e:
                print(f"  Tentativa {tentativa+1} falhou: {e}")
                if tentativa < 2:
                    print("  Tentando novamente em 5 segundos...")
                    time.sleep(5)
                else:
                    raise
        
        # Processar o HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Tentar extrair do royalSlider (método específico para o site)
        imagens = extrair_imagens_royal_slider(soup, url_base)
        
        # 2. Se não encontrou imagens no royalSlider, tentar método mais genérico
        if not imagens:
            print("  Método específico não encontrou imagens. Usando método alternativo...")
            imagens = extrair_todas_imagens(soup, url_base)
        
        # Verificar e reportar resultados
        if imagens:
            print(f"  ✓ Encontradas {len(imagens)} imagens")
            # Mostrar as primeiras 3 para debug
            for i, img in enumerate(imagens[:3]):
                print(f"    - Imagem {i+1}: {img}")
        else:
            print(f"  ✗ Nenhuma imagem encontrada para o imóvel {codigo}")
        
        return imagens
    
    except Exception as e:
        print(f"  ✗ Erro ao processar o imóvel {codigo}: {e}")
        return []

def main():
    """Função principal."""
    print("\n===== EXTRATOR DE LINKS DE IMAGENS DE IMÓVEIS =====\n")
    
    # Carregar os imóveis
    imoveis = carregar_imoveis()
    if not imoveis:
        print("Nenhum imóvel encontrado. Abortando.")
        return
    
    # Lista para armazenar os imóveis com links de imagens
    imoveis_atualizados = []
    
    # Processar cada imóvel
    for i, imovel in enumerate(tqdm(imoveis, desc="Processando imóveis")):
        codigo = imovel.get("codigo", "")
        link = imovel.get("link", "")
        
        if not codigo or not link:
            print(f"\n[{i+1}/{len(imoveis)}] Imóvel sem código ou link. Pulando.")
            imoveis_atualizados.append(imovel)
            continue
        
        print(f"\n[{i+1}/{len(imoveis)}] Processando imóvel {codigo}")
        
        # Extrair links das imagens
        links_imagens = extrair_links_imagens(link, codigo)
        
        # Atualizar o objeto do imóvel com os links das imagens
        if links_imagens:
            # Guardar todos os links
            imovel["links_imagens"] = links_imagens
            
            # Guardar o primeiro link como imagem principal
            imovel["imagem_principal"] = links_imagens[0]
        else:
            # Usar URL de placeholder
            placeholder_url = f"https://placehold.co/800x600/0d6efd/white?text=Im%C3%B3vel%20{codigo}"
            imovel["imagem_principal"] = placeholder_url
            imovel["links_imagens"] = [placeholder_url]
        
        # Adicionar o imóvel atualizado à lista
        imoveis_atualizados.append(imovel)
        
        # Salvar o progresso a cada 10 imóveis
        if (i + 1) % 10 == 0:
            with open(IMOVEIS_COM_IMAGENS_JSON, 'w', encoding='utf-8') as f:
                json.dump(imoveis_atualizados, f, ensure_ascii=False, indent=4)
            print(f"Progresso salvo em {IMOVEIS_COM_IMAGENS_JSON} ({i+1}/{len(imoveis)} imóveis)")
        
        # Pequena pausa entre requisições
        if i < len(imoveis) - 1:
            time.sleep(2)
    
    # Salvar o resultado final
    with open(IMOVEIS_COM_IMAGENS_JSON, 'w', encoding='utf-8') as f:
        json.dump(imoveis_atualizados, f, ensure_ascii=False, indent=4)
    
    print("\n===== PROCESSO CONCLUÍDO =====")
    print(f"Total de imóveis processados: {len(imoveis)}")
    print(f"Dados atualizados salvos em: {IMOVEIS_COM_IMAGENS_JSON}")
    print("\nPara usar os links das imagens:")
    print("1. Use o arquivo JSON atualizado nos seus scripts da web")
    print("2. Na sua aplicação, use 'imagem_principal' para mostrar a principal")
    print("3. Use 'links_imagens' para mostrar todas as imagens do imóvel")

if __name__ == "__main__":
    main() 