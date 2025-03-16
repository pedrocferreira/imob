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

# Configurações
BASE_URL = "https://www.novatorres.com.br"
LISTINGS_URL = "https://www.novatorres.com.br/vendas/modo/grid/ipp/96/ordem/dataatualizacaorecente"
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
DATA_FILE = os.path.join(OUTPUT_DIR, "imoveis.json")

# Garantir que os diretórios existam
os.makedirs(IMAGES_DIR, exist_ok=True)

def configurar_selenium():
    """Configura e retorna uma instância do Selenium WebDriver usando Firefox."""
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
            
        return driver
    except Exception as e:
        print(f"Erro ao configurar o Firefox: {e}")
        print("Usando uma implementação mais básica do scraper sem navegador...")
        
        # Retornar None para indicar que o selenium não está disponível
        return None

def obter_links_imoveis(driver):
    """Extrai os links para as páginas individuais de imóveis."""
    print("Acessando a página de listagem de imóveis...")
    driver.get(LISTINGS_URL)
    
    # Aguardar o carregamento dos elementos
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".resultadoBusca"))
        )
    except Exception as e:
        print(f"Erro ao aguardar carregamento da página: {e}")
        return []
    
    # Obter o HTML da página
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extrair links dos imóveis
    links = []
    imoveis_elementos = soup.select(".resultadoBusca .itemImovel")
    
    for elemento in imoveis_elementos:
        link_elemento = elemento.select_one("a.linkResultado")
        if link_elemento and link_elemento.has_attr('href'):
            link = urljoin(BASE_URL, link_elemento['href'])
            links.append(link)
    
    print(f"Encontrados {len(links)} imóveis para extrair.")
    return links

def extrair_detalhes_imovel(driver, link):
    """Extrai detalhes de um imóvel específico."""
    print(f"Acessando: {link}")
    driver.get(link)
    
    # Aguardar o carregamento dos elementos
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".imovelDetalhado"))
        )
    except Exception as e:
        print(f"Erro ao aguardar carregamento da página do imóvel: {e}")
        return None
    
    # Obter o HTML da página
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extrair informações básicas
    try:
        titulo = soup.select_one(".detalheTitulo h1").text.strip() if soup.select_one(".detalheTitulo h1") else "Sem título"
        preco = soup.select_one(".valorImovel").text.strip() if soup.select_one(".valorImovel") else "Preço não informado"
        endereco = soup.select_one(".enderecoImovel").text.strip() if soup.select_one(".enderecoImovel") else "Endereço não informado"
        
        # Extrair características
        caracteristicas = {}
        carac_elementos = soup.select(".caracteristicasImovel .item")
        for elem in carac_elementos:
            icone = elem.select_one(".icone")
            valor = elem.select_one(".valor")
            if icone and valor:
                chave = icone.get("title", "").strip()
                valor_texto = valor.text.strip()
                if chave:
                    caracteristicas[chave] = valor_texto
        
        # Extrair descrição
        descricao = soup.select_one(".descricaoImovel").text.strip() if soup.select_one(".descricaoImovel") else "Sem descrição"
        
        # Extrair código do imóvel
        codigo = soup.select_one(".codigoImovel").text.strip() if soup.select_one(".codigoImovel") else "Sem código"
        
        # Extrair links das imagens
        imagens = []
        slides = soup.select(".imagensImovel img")
        for img in slides:
            if img.has_attr('src'):
                img_url = urljoin(BASE_URL, img['src'])
                imagens.append(img_url)
        
        # Construir objeto de dados do imóvel
        imovel = {
            "codigo": codigo,
            "titulo": titulo,
            "preco": preco,
            "endereco": endereco,
            "caracteristicas": caracteristicas,
            "descricao": descricao,
            "link": link,
            "imagens": imagens
        }
        
        return imovel
    
    except Exception as e:
        print(f"Erro ao extrair detalhes do imóvel {link}: {e}")
        return None

def baixar_imagens(imovel):
    """Baixa as imagens do imóvel e atualiza os caminhos no objeto."""
    codigo = imovel["codigo"].replace("/", "-").replace(".", "-")
    diretorio_imovel = os.path.join(IMAGES_DIR, codigo)
    os.makedirs(diretorio_imovel, exist_ok=True)
    
    caminhos_locais = []
    
    for i, img_url in enumerate(imovel["imagens"]):
        try:
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                nome_arquivo = f"{i+1}.jpg"
                caminho_arquivo = os.path.join(diretorio_imovel, nome_arquivo)
                
                with open(caminho_arquivo, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                caminhos_locais.append(os.path.relpath(caminho_arquivo, OUTPUT_DIR))
            else:
                print(f"Erro ao baixar imagem {img_url}: Status code {response.status_code}")
        except Exception as e:
            print(f"Erro ao baixar imagem {img_url}: {e}")
    
    # Atualizar o objeto com os caminhos locais
    imovel["imagens_locais"] = caminhos_locais
    return imovel

def main():
    """Função principal de execução do scraper."""
    print("Iniciando o scraper da Nova Torres Imobiliária...")
    
    # Tentar configurar o Selenium
    driver = configurar_selenium()
    
    if driver is None:
        print("Não foi possível iniciar o navegador. Abortando.")
        return
    
    try:
        # Obter links dos imóveis
        links_imoveis = obter_links_imoveis(driver)
        
        # Lista para armazenar os dados dos imóveis
        imoveis = []
        
        # Extrair detalhes de cada imóvel
        for link in tqdm(links_imoveis, desc="Extraindo imóveis"):
            imovel = extrair_detalhes_imovel(driver, link)
            if imovel:
                # Baixar imagens
                imovel = baixar_imagens(imovel)
                imoveis.append(imovel)
                
                # Aguardar um pouco para não sobrecarregar o servidor
                time.sleep(1)
        
        # Salvar os dados em JSON
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(imoveis, f, ensure_ascii=False, indent=4)
        
        # Criar um DataFrame com os dados para análise
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
                "Quantidade de Imagens": len(item["imagens"])
            } 
            for item in imoveis
        ])
        
        # Salvar como CSV
        df.to_csv(os.path.join(OUTPUT_DIR, "imoveis.csv"), index=False, encoding='utf-8')
        
        print(f"Raspagem concluída! {len(imoveis)} imóveis extraídos.")
        print(f"Dados salvos em: {DATA_FILE}")
        print(f"Resumo salvo em: {os.path.join(OUTPUT_DIR, 'imoveis.csv')}")
        
    except Exception as e:
        print(f"Erro durante a execução: {e}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main() 