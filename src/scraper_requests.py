import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from tqdm import tqdm

# Configurações
BASE_URL = "https://www.novatorres.com.br"
LISTINGS_URL = "https://www.novatorres.com.br/vendas/modo/list/ipp/96/ordem/dataatualizacaorecente"
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
DATA_FILE = os.path.join(OUTPUT_DIR, "imoveis.json")
MAX_PAGINAS = 12  # Total de páginas a serem raspadas

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

def obter_url_pagina(pagina=1):
    """Gera a URL para uma página específica."""
    return f"{LISTINGS_URL}/pagina/{pagina}"

def obter_links_imoveis():
    """Extrai os links para as páginas individuais de imóveis de todas as páginas."""
    print("\nObtendo links dos imóveis de todas as páginas...")
    
    links_totais = []
    
    for pagina in range(1, MAX_PAGINAS + 1):
        print(f"\n--- Processando página {pagina}/{MAX_PAGINAS} ---")
        url_pagina = obter_url_pagina(pagina)
        
        soup = obter_pagina(url_pagina)
        if not soup:
            print(f"Não foi possível acessar a página {pagina}. Pulando para a próxima.")
            continue
        
        # Extrair links dos imóveis - usando o padrão correto encontrado na inspeção
        links_pagina = []
        links_elementos = soup.select("a[href^='/imovel/']")
        
        print(f"Encontrados {len(links_elementos)} links de imóveis na página {pagina}.")
        
        for elemento in links_elementos:
            try:
                if elemento.has_attr('href'):
                    link = elemento['href']
                    
                    # Garantir que o link seja completo
                    if not link.startswith('http'):
                        link = urljoin(BASE_URL, link)
                    
                    # Evitar duplicatas
                    if link not in links_pagina:
                        links_pagina.append(link)
            except Exception as e:
                print(f"Erro ao extrair link de um imóvel: {e}")
        
        print(f"Extraídos {len(links_pagina)} links únicos de imóveis na página {pagina}.")
        
        # Adicionar links desta página ao total
        for link in links_pagina:
            if link not in links_totais:
                links_totais.append(link)
        
        # Esperar um pouco antes de acessar a próxima página
        if pagina < MAX_PAGINAS:
            print("Aguardando 2 segundos antes de acessar a próxima página...")
            time.sleep(2)
    
    print(f"\nTotal: Extraídos {len(links_totais)} links únicos de imóveis em {MAX_PAGINAS} páginas.")
    return links_totais

def extrair_dados_texto(soup, seletores):
    """Extrai texto de um seletor CSS, tentando vários seletores em ordem."""
    for seletor in seletores:
        elemento = soup.select_one(seletor)
        if elemento:
            return elemento.text.strip()
    return None

def extrair_detalhes_imovel(link):
    """Extrai detalhes de um imóvel específico."""
    soup = obter_pagina(link)
    if not soup:
        return None
    
    try:
        # Extrair informações básicas com múltiplos seletores para aumentar a robustez
        titulo = extrair_dados_texto(soup, [
            ".detalheTitulo h1", 
            ".tituloImovel", 
            ".titulo-imovel h1",
            ".nome-imovel",
            "h1.pageTitulo"
        ]) or "Sem título"
        
        preco = extrair_dados_texto(soup, [
            ".valorImovel", 
            ".valor", 
            ".preco-imovel",
            ".preco",
            ".valor-imovel"
        ]) or "Preço não informado"
        
        endereco = extrair_dados_texto(soup, [
            ".enderecoImovel", 
            ".enderecoDetalhado", 
            ".endereco-imovel",
            ".endereco",
            ".localizacao"
        ]) or "Endereço não informado"
        
        codigo = extrair_dados_texto(soup, [
            ".codigoImovel", 
            ".codigoDetalhado", 
            ".codigo-imovel",
            ".referencia",
            ".codigo"
        ]) or f"imovel_{int(time.time())}"
        
        # Extrair código da URL se não encontrado no HTML
        if codigo == f"imovel_{int(time.time())}":
            ref_match = re.search(r'ref-(\d+)', link)
            if ref_match:
                codigo = f"#{ref_match.group(1)}"
        
        # Extrair descrição
        descricao = extrair_dados_texto(soup, [
            ".descricaoImovel", 
            ".descricaoDetalhada", 
            ".descricao-imovel",
            ".descricao",
            "#descricao"
        ]) or "Sem descrição"
        
        # Extrair características
        caracteristicas = {}
        
        # Tentativa 1: usando classes específicas
        carac_elementos = soup.select(".caracteristicasImovel .item, .caracteristicasDetalhadas .item, .caracteristica, .item-caracteristica")
        
        for elem in carac_elementos:
            # Primeira forma: ícone com título e valor separado
            icone = elem.select_one(".icone")
            valor_elem = elem.select_one(".valor")
            
            if icone and valor_elem:
                chave = icone.get("title", "").strip()
                if not chave and icone.get("alt"):
                    chave = icone.get("alt").strip()
                
                valor_texto = valor_elem.text.strip()
                
                if chave:
                    caracteristicas[chave] = valor_texto
            
            # Segunda forma: texto completo no elemento
            elif elem.text and ":" in elem.text:
                partes = elem.text.split(":", 1)
                if len(partes) == 2:
                    caracteristicas[partes[0].strip()] = partes[1].strip()
        
        # Tentativa 2: buscando em uma tabela de informações
        if not caracteristicas:
            info_rows = soup.select(".informacoesImovel tr, .tabelaInformacoes tr, .tabela-informacoes tr, table tr")
            for row in info_rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    chave = cells[0].text.strip()
                    valor_texto = cells[1].text.strip()
                    if chave:
                        caracteristicas[chave] = valor_texto
        
        # Extrair dados básicos da URL se não encontrados no HTML
        if "Dormitórios" not in caracteristicas and "quartos" not in caracteristicas:
            quarto_match = re.search(r'(\d+)-quarto', link) or re.search(r'(\d+)-dormit', link)
            if quarto_match:
                caracteristicas["Dormitórios"] = quarto_match.group(1)
        
        if "Garagem" not in caracteristicas and "garagens" not in caracteristicas:
            garagem_match = re.search(r'(\d+)-garagem', link)
            if garagem_match:
                caracteristicas["Garagem"] = garagem_match.group(1)
        
        # Extrair tipo do imóvel da URL
        tipo_match = re.search(r'/imovel/([^-]+)', link)
        if tipo_match:
            tipo = tipo_match.group(1).replace('-', ' ').title()
            caracteristicas["Tipo"] = tipo
        
        # Extrair imagens
        imagens = []
        
        # Seletores comuns para imagens
        seletores_imagens = [
            ".imagensImovel img", 
            ".galeriaDetalhada img", 
            ".galeria-imovel img",
            ".slick-slide img", 
            ".carousel-item img",
            ".slider img",
            ".imagem-principal img",
            ".imagem-destaque",
            ".imagem-imovel",
            ".imovel-foto img",
            ".foto img",
            ".galeria img"
        ]
        
        # Tentar cada seletor
        for seletor in seletores_imagens:
            slides = soup.select(seletor)
            for img in slides:
                if img.has_attr('src'):
                    img_url = img['src']
                    if not img_url.startswith('http'):
                        img_url = urljoin(BASE_URL, img_url)
                    
                    # Evitar duplicatas
                    if img_url not in imagens:
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
    
    print(f"Baixando {len(imovel['imagens'])} imagens para o imóvel {codigo}...")
    
    for i, img_url in enumerate(imovel["imagens"]):
        try:
            # Evitar URLs malformadas
            if not img_url.startswith('http'):
                continue
                
            # Fazer o download com timeout
            response = requests.get(img_url, headers=HEADERS, stream=True, timeout=10)
            
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

def salvar_progresso(imoveis, arquivo=DATA_FILE):
    """Salva o progresso atual dos imóveis extraídos."""
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(imoveis, f, ensure_ascii=False, indent=4)
        print(f"Progresso salvo: {len(imoveis)} imóveis no arquivo {arquivo}")
        return True
    except Exception as e:
        print(f"Erro ao salvar progresso: {e}")
        return False

def carregar_progresso(arquivo=DATA_FILE):
    """Carrega imóveis já extraídos anteriormente, se existirem."""
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                imoveis = json.load(f)
            print(f"Carregados {len(imoveis)} imóveis de extração anterior.")
            return imoveis
        except Exception as e:
            print(f"Erro ao carregar progresso anterior: {e}")
    
    print("Nenhum progresso anterior encontrado. Iniciando nova extração.")
    return []

def main():
    """Função principal de execução do scraper."""
    print("\n" + "="*60)
    print("RASPAGEM DE DADOS - NOVA TORRES IMOBILIÁRIA")
    print("="*60)
    print("\nIniciando a raspagem de dados usando solicitações HTTP simples...")
    
    tempo_inicio = time.time()
    
    # Carregar progresso anterior, se existir
    imoveis_extraidos = carregar_progresso()
    links_ja_processados = [imovel["link"] for imovel in imoveis_extraidos] if imoveis_extraidos else []
    
    try:
        # Obter links dos imóveis
        todos_links = obter_links_imoveis()
        
        if not todos_links:
            print("Nenhum link de imóvel encontrado. Verificando possíveis problemas...")
            return
        
        # Filtrar links que ainda não foram processados
        links_pendentes = [link for link in todos_links if link not in links_ja_processados]
        
        print(f"\nStatus da extração:")
        print(f"- Total de links encontrados: {len(todos_links)}")
        print(f"- Links já processados anteriormente: {len(links_ja_processados)}")
        print(f"- Links pendentes para processamento: {len(links_pendentes)}")
        
        # Se não houver links pendentes, terminar
        if not links_pendentes:
            print("\nTodos os imóveis já foram extraídos anteriormente!")
            return
        
        # Extrair detalhes de cada imóvel pendente
        print(f"\nIniciando extração detalhada de {len(links_pendentes)} imóveis pendentes...")
        
        for i, link in enumerate(tqdm(links_pendentes, desc="Processando imóveis")):
            print(f"\n[Imóvel {i+1}/{len(links_pendentes)}]")
            
            # Extrair detalhes do imóvel
            imovel = extrair_detalhes_imovel(link)
            
            if imovel:
                # Baixar imagens
                imovel = baixar_imagens(imovel)
                imoveis_extraidos.append(imovel)
                
                # Salvar o progresso a cada 5 imóveis ou no último imóvel
                if (i + 1) % 5 == 0 or i == len(links_pendentes) - 1:
                    salvar_progresso(imoveis_extraidos)
                
                # Intervalo para não sobrecarregar o servidor
                if i < len(links_pendentes) - 1:
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
        
        # Calcular tempo total
        tempo_total = time.time() - tempo_inicio
        minutos = int(tempo_total // 60)
        segundos = int(tempo_total % 60)
        
        # Relatório final
        print("\n" + "="*60)
        print(f"RASPAGEM CONCLUÍDA EM {minutos} minutos e {segundos} segundos!")
        print(f"Total de imóveis extraídos: {len(imoveis_extraidos)}")
        print(f"Dados completos salvos em: {DATA_FILE}")
        print("="*60)
        
    except Exception as e:
        print(f"\nErro durante a execução do scraper: {e}")

if __name__ == "__main__":
    main() 