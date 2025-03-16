import os
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import pandas as pd
from urllib.parse import urljoin
import re

# Configurações
BASE_URL = "https://www.novatorres.com.br"
LISTINGS_URL = "https://www.novatorres.com.br/vendas/modo/grid/ipp/96/ordem/dataatualizacaorecente"
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
DATA_FILE = os.path.join(OUTPUT_DIR, "imoveis.json")

# Garantir que os diretórios existam
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def configurar_selenium():
    """Configura e retorna uma instância do Selenium WebDriver com Firefox."""
    try:
        print("Configurando o Selenium WebDriver com Firefox...")
        
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        
        # Tentar usar o GeckoDriverManager para instalar o driver
        try:
            service = Service(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=firefox_options)
        except Exception as e:
            print(f"Erro ao usar GeckoDriverManager: {e}")
            print("Tentando abordagem alternativa...")
            
            # Abordagem alternativa se o GeckoDriverManager falhar
            driver = webdriver.Firefox(options=firefox_options)
        
        print("Firefox configurado com sucesso!")
        return driver
    
    except Exception as e:
        print(f"Erro ao configurar o Firefox: {e}")
        print("Não foi possível iniciar o navegador.")
        return None

def esperar_carregamento(driver, seletor, tempo=10):
    """Aguarda o carregamento de um elemento na página."""
    try:
        elemento = WebDriverWait(driver, tempo).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, seletor))
        )
        return True
    except Exception as e:
        print(f"Erro ao aguardar elemento '{seletor}': {e}")
        return False

def obter_links_imoveis(driver):
    """Extrai os links para as páginas individuais de imóveis."""
    print("Acessando a página de listagem de imóveis...")
    driver.get(LISTINGS_URL)
    
    # Aguardar o carregamento da página
    if not esperar_carregamento(driver, ".resultadoBusca"):
        return []
    
    # Obter o conteúdo da página
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Encontrar os elementos de imóveis
    links = []
    imoveis_elementos = soup.select(".resultadoBusca .itemImovel")
    print(f"Encontrados {len(imoveis_elementos)} elementos de imóveis na página.")
    
    # Extrair os links
    for elemento in imoveis_elementos:
        try:
            link_elemento = elemento.select_one("a.linkResultado")
            if link_elemento and link_elemento.has_attr('href'):
                link = urljoin(BASE_URL, link_elemento['href'])
                links.append(link)
        except Exception as e:
            print(f"Erro ao extrair link de um imóvel: {e}")
    
    print(f"Extraídos com sucesso {len(links)} links de imóveis.")
    return links

def extrair_detalhes_imovel(driver, link):
    """Extrai detalhes de um imóvel específico."""
    print(f"Acessando imóvel: {link}")
    driver.get(link)
    
    # Aguardar o carregamento dos detalhes
    if not esperar_carregamento(driver, ".imovelDetalhado", 15):
        print(f"Não foi possível carregar os detalhes do imóvel: {link}")
        return None
    
    # Dar tempo para os elementos carregarem completamente
    time.sleep(2)
    
    # Extrair os detalhes
    try:
        # Obter o HTML da página
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extrair dados básicos
        titulo_elem = soup.select_one(".detalheTitulo h1, .tituloImovel")
        titulo = titulo_elem.text.strip() if titulo_elem else "Sem título"
        
        preco_elem = soup.select_one(".valorImovel, .valor")
        preco = preco_elem.text.strip() if preco_elem else "Preço não informado"
        
        endereco_elem = soup.select_one(".enderecoImovel, .enderecoDetalhado")
        endereco = endereco_elem.text.strip() if endereco_elem else "Endereço não informado"
        
        codigo_elem = soup.select_one(".codigoImovel, .codigoDetalhado")
        codigo = codigo_elem.text.strip() if codigo_elem else f"imovel_{int(time.time())}"
        
        # Extrair descrição
        descricao_elem = soup.select_one(".descricaoImovel, .descricaoDetalhada")
        descricao = descricao_elem.text.strip() if descricao_elem else "Sem descrição"
        
        # Extrair características
        caracteristicas = {}
        
        # Tentativa 1: usando classes específicas
        carac_elementos = soup.select(".caracteristicasImovel .item, .caracteristicasDetalhadas .item")
        
        for elem in carac_elementos:
            icone = elem.select_one(".icone")
            valor = elem.select_one(".valor")
            
            if icone and valor:
                chave = icone.get("title", "").strip()
                if not chave and icone.get("alt"):
                    chave = icone.get("alt").strip()
                
                valor_texto = valor.text.strip()
                
                if chave:
                    caracteristicas[chave] = valor_texto
        
        # Tentativa 2: buscando em uma tabela de informações
        if not caracteristicas:
            info_rows = soup.select(".informacoesImovel tr, .tabelaInformacoes tr")
            for row in info_rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    chave = cells[0].text.strip()
                    valor_texto = cells[1].text.strip()
                    if chave:
                        caracteristicas[chave] = valor_texto
        
        # Extrair imagens
        imagens = []
        
        # Tentativa 1: galeria de imagens padrão
        slides = soup.select(".imagensImovel img, .galeriaDetalhada img, .galeria-imovel img")
        for img in slides:
            if img.has_attr('src'):
                img_url = img['src']
                if not img_url.startswith('http'):
                    img_url = urljoin(BASE_URL, img_url)
                imagens.append(img_url)
        
        # Tentativa 2: imagens em sliders específicos
        if not imagens:
            slides = soup.select(".slick-slide img, .carousel-item img")
            for img in slides:
                if img.has_attr('src'):
                    img_url = img['src']
                    if not img_url.startswith('http'):
                        img_url = urljoin(BASE_URL, img_url)
                    if img_url not in imagens:  # Evita duplicatas
                        imagens.append(img_url)
        
        # Remover imagens de placeholder ou logos
        imagens = [img for img in imagens if not any(termo in img.lower() for termo in ["placeholder", "logo", "icon"])]
        
        # Construir o objeto de dados do imóvel
        imovel = {
            "codigo": re.sub(r'[^a-zA-Z0-9]', '-', codigo),
            "titulo": titulo,
            "preco": preco,
            "endereco": endereco,
            "caracteristicas": caracteristicas,
            "descricao": descricao,
            "link": link,
            "imagens": imagens
        }
        
        print(f"Extraídos detalhes do imóvel: {titulo}")
        print(f"  - Preço: {preco}")
        print(f"  - Endereço: {endereco}")
        print(f"  - Características: {len(caracteristicas)} itens")
        print(f"  - Imagens: {len(imagens)}")
        
        return imovel
        
    except Exception as e:
        print(f"Erro ao extrair detalhes do imóvel {link}: {e}")
        return None

def baixar_imagens(imovel):
    """Baixa as imagens do imóvel e atualiza os caminhos no objeto."""
    codigo = imovel["codigo"]
    diretorio_imovel = os.path.join(IMAGES_DIR, codigo)
    os.makedirs(diretorio_imovel, exist_ok=True)
    
    caminhos_locais = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Baixando {len(imovel['imagens'])} imagens para o imóvel {codigo}...")
    
    for i, img_url in enumerate(imovel["imagens"]):
        try:
            # Evitar URLs malformadas
            if not img_url.startswith('http'):
                continue
                
            # Fazer o download com timeout
            response = requests.get(img_url, headers=headers, stream=True, timeout=10)
            
            if response.status_code == 200:
                # Determinar o tipo de arquivo da imagem
                content_type = response.headers.get('Content-Type', '')
                ext = '.jpg'  # Extensão padrão
                
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
    
    # Atualizar o objeto com os caminhos locais
    imovel["imagens_locais"] = caminhos_locais
    return imovel

def main():
    """Função principal de execução do scraper."""
    print("Iniciando a raspagem de dados da Nova Torres Imobiliária...")
    
    driver = configurar_selenium()
    
    if driver is None:
        print("Não foi possível iniciar o navegador. Abortando.")
        return
    
    imoveis_extraidos = []
    
    try:
        # Obter links dos imóveis
        links_imoveis = obter_links_imoveis(driver)
        
        if not links_imoveis:
            print("Nenhum link de imóvel encontrado. Verificando possíveis problemas...")
            try:
                driver.save_screenshot("debug_pagina.png")
                print(f"Screenshot salvo em debug_pagina.png para diagnóstico.")
            except:
                print("Não foi possível salvar o screenshot.")
            return
        
        # Extrair detalhes de cada imóvel
        print(f"\nIniciando extração detalhada de {len(links_imoveis)} imóveis...")
        
        for i, link in enumerate(links_imoveis):
            print(f"\n[Imóvel {i+1}/{len(links_imoveis)}]")
            
            # Extrair detalhes do imóvel
            imovel = extrair_detalhes_imovel(driver, link)
            
            if imovel:
                # Baixar imagens
                imovel = baixar_imagens(imovel)
                imoveis_extraidos.append(imovel)
                
                # Salvar os dados parciais após cada imóvel
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(imoveis_extraidos, f, ensure_ascii=False, indent=4)
                
                # Intervalo para não sobrecarregar o servidor
                if i < len(links_imoveis) - 1:
                    tempo_espera = 2
                    print(f"Aguardando {tempo_espera} segundos antes do próximo imóvel...")
                    time.sleep(tempo_espera)
        
        # Criar DataFrame para análise
        if imoveis_extraidos:
            df = pd.DataFrame([
                {
                    "Código": item["codigo"],
                    "Título": item["titulo"],
                    "Preço": item["preco"],
                    "Endereço": item["endereco"],
                    "Quartos": item["caracteristicas"].get("Dormitórios", "N/A"),
                    "Banheiros": item["caracteristicas"].get("Banheiros", "N/A"),
                    "Área": item["caracteristicas"].get("Área total", "N/A"),
                    "Link": item["link"],
                    "Quantidade de Imagens": len(item.get("imagens_locais", []))
                } 
                for item in imoveis_extraidos
            ])
            
            # Salvar como CSV
            csv_path = os.path.join(OUTPUT_DIR, "imoveis.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"\nResumo dos dados salvos em: {csv_path}")
        
        # Relatório final
        print("\n" + "="*50)
        print(f"Raspagem concluída com sucesso!")
        print(f"Total de imóveis extraídos: {len(imoveis_extraidos)}")
        print(f"Dados completos salvos em: {DATA_FILE}")
        print("="*50)
        
    except Exception as e:
        print(f"\nErro durante a execução do scraper: {e}")
        
    finally:
        if driver:
            print("\nFinalizando o WebDriver...")
            driver.quit()

if __name__ == "__main__":
    main() 