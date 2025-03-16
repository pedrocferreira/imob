import os
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import time
from tqdm import tqdm

# Configurações
DATA_DIR = Path("data")
IMOVEIS_JSON = DATA_DIR / "imoveis.json"
IMOVEIS_COM_IMAGENS_JSON = DATA_DIR / "imoveis_com_imagens.json"
IMAGES_DIR = DATA_DIR / "imagens_simples"

# Criar diretórios se não existirem
IMAGES_DIR.mkdir(exist_ok=True, parents=True)

# Headers para simular um navegador real
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

def obter_primeira_imagem(url):
    """Acessa a página do imóvel e extrai apenas a primeira imagem do carrossel."""
    try:
        print(f"Acessando: {url}")
        
        # Fazer requisição com retry
        for tentativa in range(3):
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
                break
            except Exception as e:
                print(f"  Tentativa {tentativa+1} falhou: {e}")
                if tentativa < 2:
                    print("  Tentando novamente em 3 segundos...")
                    time.sleep(3)
                else:
                    raise
        
        # Analisar o HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tentar encontrar especificamente a primeira imagem do carrossel royalSlider
        imagem_url = None
        
        # Método 1: Direto na primeira rsSlide (mais preciso)
        primeiro_slide = soup.select_one("#gal-imov .rsSlide:first-child img.rsImg, .royalSlider .rsSlide:first-child img.rsImg")
        if primeiro_slide and primeiro_slide.has_attr('src'):
            # Obter URL da imagem grande, não thumbnail
            imagem_url = primeiro_slide['src']
            # Converter de média (im) para grande (il)
            imagem_url = imagem_url.replace('/im/', '/il/')
            print(f"  ✓ Encontrada primeira imagem do carrossel")
        
        # Método 2: Verificar atributo data-rsbigimg (contém a URL da imagem grande)
        if not imagem_url:
            primeira_img_big = soup.select_one(".royalSlider img.rsImg[data-rsbigimg]")
            if primeira_img_big and primeira_img_big.has_attr('data-rsbigimg'):
                imagem_url = primeira_img_big['data-rsbigimg']
                print(f"  ✓ Encontrada imagem grande via data-rsbigimg")
        
        # Método 3: Primeira imagem selecionada na galeria
        if not imagem_url:
            thumb_selecionada = soup.select_one(".rsNavSelected img.rsTmb")
            if thumb_selecionada and thumb_selecionada.has_attr('src'):
                # Converter de thumbnail (it) para grande (il)
                imagem_url = thumb_selecionada['src'].replace('/it/', '/il/')
                print(f"  ✓ Usando imagem grande da thumbnail selecionada")
        
        # Método 4: Qualquer imagem principal do carrossel
        if not imagem_url:
            qualquer_img = soup.select_one(".royalSlider img.rsMainSlideImage")
            if qualquer_img and qualquer_img.has_attr('src'):
                imagem_url = qualquer_img['src'].replace('/im/', '/il/')
                print(f"  ✓ Usando imagem do slide principal")
        
        # Método 5: Elemento span com background-image (alternativa comum)
        if not imagem_url:
            bg_span = soup.select_one(".royalSlider .rsSlide:first-child .bg")
            if bg_span and bg_span.has_attr('style'):
                import re
                bg_match = re.search(r'background-image: url\((.*?)\)', bg_span['style'])
                if bg_match:
                    # Extrair URL do background e converter para versão grande
                    imagem_url = bg_match.group(1).replace('/it/', '/il/')
                    print(f"  ✓ Extraído URL do background-image")
        
        # Ajustar URL relativa
        if imagem_url:
            if imagem_url.startswith('//'):
                imagem_url = 'https:' + imagem_url
            elif not imagem_url.startswith('http'):
                # Construir URL absoluta
                base_url = '/'.join(url.split('/')[:3])  # http://exemplo.com
                imagem_url = base_url + imagem_url if imagem_url.startswith('/') else base_url + '/' + imagem_url
        
        if imagem_url:
            print(f"  ✓ Imagem grande encontrada: {imagem_url}")
        else:
            print(f"  ✗ Nenhuma imagem do carrossel encontrada")
        
        return imagem_url
    
    except Exception as e:
        print(f"  ✗ Erro ao acessar a página: {e}")
        return None

def baixar_imagem(url, codigo):
    """Baixa a imagem e salva com o código do imóvel como nome."""
    if not url:
        print(f"  ✗ URL vazia para o imóvel {codigo}")
        return None
    
    # Nome do arquivo: código do imóvel + .jpg
    nome_arquivo = f"{codigo}.jpg"
    caminho_imagem = IMAGES_DIR / nome_arquivo
    
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=15)
        
        if response.status_code == 200:
            with open(caminho_imagem, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            # Caminho relativo para salvar no JSON
            caminho_relativo = f"imagens_simples/{nome_arquivo}"
            print(f"  ✓ Imagem salva em {caminho_relativo}")
            return caminho_relativo
        else:
            print(f"  ✗ Erro ao baixar imagem: Status {response.status_code}")
            return None
    
    except Exception as e:
        print(f"  ✗ Erro ao baixar imagem: {e}")
        return None

def baixar_imagem_placeholder(codigo):
    """Baixa uma imagem de placeholder se não foi possível obter a imagem real."""
    print(f"  → Criando placeholder para imóvel {codigo}")
    
    nome_arquivo = f"{codigo}.jpg"
    caminho_imagem = IMAGES_DIR / nome_arquivo
    
    placeholder_url = f"https://placehold.co/800x600/0d6efd/white?text=Im%C3%B3vel%20{codigo}"
    
    try:
        response = requests.get(placeholder_url, stream=True, timeout=10)
        
        if response.status_code == 200:
            with open(caminho_imagem, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            caminho_relativo = f"imagens_simples/{nome_arquivo}"
            print(f"  ✓ Placeholder salvo em {caminho_relativo}")
            return caminho_relativo
        else:
            return None
    except Exception as e:
        print(f"  ✗ Erro ao criar placeholder: {e}")
        return None

def main():
    """Função principal."""
    print("\n===== BAIXADOR SIMPLES DE IMAGENS DE IMÓVEIS =====\n")
    
    # Carregar os imóveis
    imoveis = carregar_imoveis()
    if not imoveis:
        print("Nenhum imóvel encontrado. Abortando.")
        return
    
    # Lista para armazenar os imóveis com imagens
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
        
        # Verificar se a imagem já existe
        nome_arquivo = f"{codigo}.jpg"
        caminho_imagem = IMAGES_DIR / nome_arquivo
        
        if caminho_imagem.exists():
            print(f"  ✓ Imagem já existe: imagens_simples/{nome_arquivo}")
            # Adicionar o caminho da imagem ao imóvel
            imovel["imagem_principal"] = f"imagens_simples/{nome_arquivo}"
            imoveis_atualizados.append(imovel)
            continue
        
        # Obter a primeira imagem
        imagem_url = obter_primeira_imagem(link)
        
        # Baixar a imagem
        caminho_salvo = None
        if imagem_url:
            caminho_salvo = baixar_imagem(imagem_url, codigo)
        
        # Se não conseguiu baixar, criar um placeholder
        if not caminho_salvo:
            caminho_salvo = baixar_imagem_placeholder(codigo)
        
        # Atualizar o objeto do imóvel
        if caminho_salvo:
            imovel["imagem_principal"] = caminho_salvo
        
        # Adicionar o imóvel atualizado à lista
        imoveis_atualizados.append(imovel)
        
        # Salvar o progresso a cada 10 imóveis
        if (i + 1) % 10 == 0:
            with open(IMOVEIS_COM_IMAGENS_JSON, 'w', encoding='utf-8') as f:
                json.dump(imoveis_atualizados, f, ensure_ascii=False, indent=4)
            print(f"Progresso salvo em {IMOVEIS_COM_IMAGENS_JSON} ({i+1}/{len(imoveis)} imóveis)")
        
        # Pequena pausa entre requisições
        if i < len(imoveis) - 1:
            time.sleep(1)
    
    # Salvar o resultado final
    with open(IMOVEIS_COM_IMAGENS_JSON, 'w', encoding='utf-8') as f:
        json.dump(imoveis_atualizados, f, ensure_ascii=False, indent=4)
    
    print("\n===== PROCESSO CONCLUÍDO =====")
    print(f"Total de imóveis processados: {len(imoveis)}")
    print(f"Imagens salvas em: {IMAGES_DIR}")
    print(f"Dados atualizados salvos em: {IMOVEIS_COM_IMAGENS_JSON}")
    print("\nPara usar estas imagens no RAG:")
    print("1. Modifique o arquivo app.py para incluir:")
    print('   app.mount("/imagens_simples", StaticFiles(directory=str(DATA_DIR / "imagens_simples")), name="imagens_simples")')
    print("2. Atualize o arquivo assistente.py para usar o novo caminho de imagens")

if __name__ == "__main__":
    main() 