import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Carregar variáveis de ambiente
load_dotenv(Path(__file__).parent / '.env')

# Configuração do armazenamento de documentos
DOCUMENTOS_JSON = os.path.join(os.path.dirname(os.getenv("CHROMA_PERSIST_DIRECTORY", "./db")), "documentos.json")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class AssistenteImobiliaria:
    """Assistente de IA para responder perguntas sobre imóveis."""
    
    def __init__(self):
        """Inicializa o assistente."""
        self.dados_imoveis = None
        self.llm = None  # Modelo de linguagem para respostas mais inteligentes
        self.inicializar()
    
    def inicializar(self):
        """Carrega os dados e configura o assistente."""
        import os
        import json
        from pathlib import Path
        from dotenv import load_dotenv
        import sys
        
        # Garantir que estamos no diretório raiz
        if os.path.basename(os.getcwd()) == "rag":
            os.chdir('..')
        
        # Adicionar diretório raiz ao path para importações
        sys.path.append(os.getcwd())
        
        # Configurações
        self.data_dir = Path("data")
        
        # Tentar carregar dados com links de imagens primeiro
        imoveis_com_links = self.data_dir / "imoveis_com_links.json"
        imoveis_com_imagens = self.data_dir / "imoveis_com_imagens.json"
        imoveis_json = self.data_dir / "imoveis.json"
        
        # Carregar o arquivo de imóveis (tentar primeiro os com links)
        if imoveis_com_links.exists():
            print("Usando arquivo com links de imagens...")
            with open(imoveis_com_links, 'r', encoding='utf-8') as f:
                self.dados_imoveis = json.load(f)
        elif imoveis_com_imagens.exists():
            print("Usando arquivo com caminhos locais de imagens...")
            with open(imoveis_com_imagens, 'r', encoding='utf-8') as f:
                self.dados_imoveis = json.load(f)
        else:
            print("Usando arquivo básico de imóveis...")
            with open(imoveis_json, 'r', encoding='utf-8') as f:
                self.dados_imoveis = json.load(f)
        
        print(f"Carregados dados de {len(self.dados_imoveis)} imóveis.")
        
        # Carregar configuração OpenAI
        load_dotenv(Path("rag") / ".env")
        
        # Configurar o modelo de linguagem se possível
        try:
            from langchain_openai import ChatOpenAI
            import os
            
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key and openai_api_key != "sua_chave_aqui":
                self.llm = ChatOpenAI(
                    model=os.getenv("LLM_MODEL", "gpt-3.5-turbo-0125"),
                    temperature=0.2
                )
                print(f"Usando modelo OpenAI: {os.getenv('LLM_MODEL', 'gpt-3.5-turbo-0125')}")
            else:
                print("AVISO: API Key da OpenAI não configurada. Usando respostas pré-definidas.")
        except Exception as e:
            print(f"Erro ao inicializar modelo de linguagem: {e}")
            print("Usando respostas pré-definidas como fallback.")
        
        print("Assistente inicializado com sucesso!")
    
    def _buscar_documentos_relevantes(self, pergunta: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca os documentos mais relevantes para a pergunta."""
        if not self.dados_imoveis:
            print("Aviso: Nenhum documento carregado na base de conhecimento.")
            return []
        
        print(f"Buscando documentos relevantes para: '{pergunta}'")
        
        # Normalizar a pergunta (remover acentos, converter para minúsculas)
        pergunta_norm = pergunta.lower().strip()
        
        # Extrair palavras-chave mais relevantes da pergunta
        palavras_chave = re.findall(r'\b\w{3,}\b', pergunta_norm)
        
        # Verificar palavras específicas relacionadas a imóveis
        palavras_especificas = ['quarto', 'quartos', 'dormitório', 'dormitórios', 'apartamento', 'casa', 
                               'praia', 'garagem', 'suite', 'banheiro', 'preço', 'centro', 'área']
                               
        # Adicionar palavras específicas se estiverem na pergunta
        for palavra in palavras_especificas:
            if palavra in pergunta_norm and palavra not in palavras_chave:
                palavras_chave.append(palavra)
        
        # Remover alguns stop words e palavras muito comuns
        stop_words = ['com', 'que', 'para', 'por', 'dos', 'das', 'tem', 'mais', 'são', 'não', 'sim']
        palavras_chave = [p for p in palavras_chave if p not in stop_words]
        
        print(f"Palavras-chave identificadas: {palavras_chave}")
        
        # Se não há palavras-chave suficientes, retornar documentos de imóveis aleatórios
        if len(palavras_chave) < 2:
            print("Poucas palavras-chave identificadas, retornando imóveis representativos")
            
            # Coletar documentos de imóvel
            imoveis_docs = [doc for doc in self.dados_imoveis if doc.get("metadata", {}).get("tipo") == "imovel"]
            
            # Se não há documentos suficientes, retornar todos
            if len(imoveis_docs) <= k:
                return imoveis_docs
            
            # Caso contrário, pegar alguns aleatórios, limitado ao número k
            import random
            random_docs = random.sample(imoveis_docs, min(k, len(imoveis_docs)))
            
            # Complementar com documentos de características e imagens relacionados
            resultado = []
            codigos_processados = set()
            
            for doc in random_docs:
                codigo = doc.get("metadata", {}).get("codigo", "")
                if codigo and codigo not in codigos_processados:
                    resultado.append(doc)
                    
                    # Adicionar características e imagens
                    for comp_doc in self.dados_imoveis:
                        comp_tipo = comp_doc.get("metadata", {}).get("tipo")
                        comp_codigo = comp_doc.get("metadata", {}).get("codigo")
                        
                        if comp_codigo == codigo and comp_tipo in ["caracteristicas", "imagens"]:
                            resultado.append(comp_doc)
                    
                    codigos_processados.add(codigo)
                    
                    # Limitar ao número máximo de documentos
                    if len(resultado) >= k * 3:  # multiplicador para incluir docs relacionados
                        break
            
            print(f"Retornando {len(resultado)} documentos aleatórios")
            return resultado[:k*3]  # Limitar ao número máximo de documentos
        
        # Busca normal por palavras-chave
        documentos_pontuados = []
        
        for doc in self.dados_imoveis:
            texto = doc["text"].lower()
            metadata = doc.get("metadata", {})
            
            # Calcular pontuação base por correspondência de palavras-chave
            pontuacao = 0
            for palavra in palavras_chave:
                if palavra in texto:
                    # Palavras-chave no texto
                    matches = len(re.findall(r'\b' + palavra + r'\b', texto))
                    pontuacao += matches * 1.0
                    
                    # Bônus para palavras-chave no título
                    if palavra in metadata.get("titulo", "").lower():
                        pontuacao += 2.0
                    
                    # Bônus para palavras-chave no código/identificador
                    if palavra in metadata.get("codigo", "").lower():
                        pontuacao += 3.0
            
            # Aplicar modificadores com base no tipo de documento
            tipo_doc = metadata.get("tipo", "")
            
            # Priorizar documentos de imóveis e características
            if tipo_doc == "imovel":
                pontuacao *= 1.5
            elif tipo_doc == "caracteristicas":
                pontuacao *= 1.2
            
            # Adicionar o documento à lista se tiver alguma relevância
            if pontuacao > 0:
                documentos_pontuados.append((doc, pontuacao))
        
        # Ordenar por pontuação e pegar os k*3 mais relevantes para incluir documentos relacionados
        documentos_ordenados = sorted(documentos_pontuados, key=lambda x: x[1], reverse=True)
        docs_relevantes = [doc for doc, _ in documentos_ordenados[:k*3]]
        
        # Se não encontrou nenhum documento relevante, retornar alguns imóveis aleatórios
        if not docs_relevantes:
            print("Nenhum documento relevante encontrado. Retornando imóveis aleatórios.")
            imoveis_docs = [doc for doc in self.dados_imoveis if doc.get("metadata", {}).get("tipo") == "imovel"]
            if imoveis_docs:
                import random
                return random.sample(imoveis_docs, min(k, len(imoveis_docs)))
            return []
        
        # Incluir documentos de características e imagens para os imóveis encontrados
        codigos_encontrados = set()
        documentos_complementares = []
        
        for doc in docs_relevantes:
            metadata = doc.get("metadata", {})
            if metadata.get("tipo") == "imovel":
                codigo = metadata.get("codigo")
                if codigo:
                    codigos_encontrados.add(codigo)
        
        # Adicionar documentos complementares (características e imagens)
        for doc in self.dados_imoveis:
            metadata = doc.get("metadata", {})
            tipo = metadata.get("tipo")
            codigo = metadata.get("codigo")
            
            if tipo in ["caracteristicas", "imagens"] and codigo in codigos_encontrados:
                if doc not in docs_relevantes:
                    documentos_complementares.append(doc)
        
        # Combinar os documentos relevantes com os complementares
        resultado_final = docs_relevantes + documentos_complementares
        
        print(f"Retornando {len(resultado_final)} documentos relevantes e complementares")
        return resultado_final[:k*3]  # Limitar ao número máximo de documentos
    
    def _extrair_caracteristicas_imovel(self, codigo: str) -> Dict[str, Any]:
        """Extrai características detalhadas de um imóvel específico."""
        caracteristicas = {
            "dormitorios": "N/A",
            "banheiros": "N/A",
            "garagem": "N/A",
            "tipo": "N/A",
            "area": "N/A",
            "mobiliado": False,
            "features": []
        }
        
        # Buscar documento de características
        for doc in self.dados_imoveis:
            metadata = doc.get("metadata", {})
            if metadata.get("tipo") == "caracteristicas" and metadata.get("codigo") == codigo:
                texto = doc["text"].lower()
                
                # Extrair dormitórios
                if "dormitórios:" in texto or "dormitorios:" in texto:
                    for linha in texto.split("\n"):
                        if "dormitórios:" in linha or "dormitorios:" in linha:
                            partes = linha.split(":", 1)
                            if len(partes) > 1:
                                caracteristicas["dormitorios"] = partes[1].strip()
                
                # Extrair garagem
                if "garagem:" in texto:
                    for linha in texto.split("\n"):
                        if "garagem:" in linha:
                            partes = linha.split(":", 1)
                            if len(partes) > 1:
                                caracteristicas["garagem"] = partes[1].strip()
                
                # Extrair tipo
                if "tipo:" in texto:
                    for linha in texto.split("\n"):
                        if "tipo:" in linha:
                            partes = linha.split(":", 1)
                            if len(partes) > 1:
                                caracteristicas["tipo"] = partes[1].strip()
                
                break
        
        # Buscar documento principal para extrair mais características
        for doc in self.dados_imoveis:
            metadata = doc.get("metadata", {})
            if metadata.get("tipo") == "imovel" and metadata.get("codigo") == codigo:
                texto = doc["text"].lower()
                
                # Verificar se é mobiliado
                if "mobiliado" in texto or "mobiliada" in texto:
                    caracteristicas["mobiliado"] = True
                
                # Extrair recursos adicionais
                features = []
                if "sacada" in texto:
                    features.append("Sacada")
                if "churrasqueira" in texto:
                    features.append("Churrasqueira")
                if "piscina" in texto:
                    features.append("Piscina")
                if "elevador" in texto:
                    features.append("Elevador")
                if "gourmet" in texto:
                    features.append("Espaço Gourmet")
                if "área de serviço" in texto or "area de servico" in texto:
                    features.append("Área de Serviço")
                
                caracteristicas["features"] = features
                
                # Extrair área se mencionada
                if "m²" in texto or "m2" in texto:
                    palavras = texto.split()
                    for i, palavra in enumerate(palavras):
                        if "m²" in palavra or "m2" in palavra:
                            if i > 0 and palavras[i-1].isdigit():
                                caracteristicas["area"] = palavras[i-1] + " m²"
                break
        
        return caracteristicas
    
    def responder(self, pergunta: str) -> Dict[str, Any]:
        """Responde a uma pergunta sobre imóveis."""
        import re
        
        # Verificar se temos os dados carregados
        if not self.dados_imoveis:
            return {
                "resposta": "Desculpe, ainda não tenho dados sobre imóveis para responder.",
                "imoveis_relacionados": [],
                "imagens_relacionadas": []
            }
        
        # Verificar se é uma pergunta sobre um imóvel específico
        codigo_imovel = None
        match_codigo = re.search(r'(?:código|codigo|cód|cod)[\s:]*([a-zA-Z0-9-]+)', pergunta, re.IGNORECASE)
        if match_codigo:
            codigo_imovel = match_codigo.group(1)
            
        resposta = ""
        imoveis_relacionados = []
        imagens_relacionadas = []
        
        try:
            # Se perguntou sobre um imóvel específico
            if codigo_imovel:
                # Buscar o imóvel pelo código
                imovel = next((item for item in self.dados_imoveis if item["codigo"] == codigo_imovel), None)
                
                if imovel:
                    # Construir resposta detalhada para este imóvel
                    caracteristicas = imovel.get("caracteristicas", {})
                    dormitorios = caracteristicas.get("Dormitórios", "não informado")
                    banheiros = caracteristicas.get("Banheiros", "não informado")
                    area = caracteristicas.get("Área total", "não informado")
                    
                    if self.llm:
                        # Construir o prompt para o modelo de linguagem
                        prompt = f"""
                        Você é Torres Virtual, um assistente especializado em imóveis da Nova Torres Imobiliária, com personalidade calorosa e entusiasmada.
                        
                        Seu objetivo é conversar como um corretor de imóveis muito amigável e experiente, que adora os imóveis que vende.
                        Responda de forma EXTREMAMENTE HUMANA E CONVERSACIONAL.
                        
                        Forneça informações sobre o seguinte imóvel:
                        
                        Código: {imovel["codigo"]}
                        Título: {imovel["titulo"]}
                        Preço: {imovel["preco"]}
                        Endereço: {imovel["endereco"]}
                        Dormitórios: {dormitorios}
                        Banheiros: {banheiros}
                        Área total: {area}
                        Link do imóvel: {imovel["link"]}
                        
                        Características adicionais:
                        {', '.join([f"{k}: {v}" for k, v in caracteristicas.items()])}
                        
                        Descrição:
                        {imovel['descricao']}
                        
                        DIRETRIZES IMPORTANTES PARA SUA RESPOSTA:
                        1. Use expressões brasileiras regionais como "olha só", "que legal", "sensacional", "maravilhoso" 
                        2. Seja MUITO entusiasmado e mostre paixão pelo imóvel
                        3. Descreva vividamente pelo menos 3 vantagens do imóvel (localização, espaço, estrutura, etc)
                        4. Fale como se estivesse tendo uma conversa casual com um cliente, não como um robô
                        5. Use vocabulário rico para descrever o imóvel (ex: aconchegante, espaçoso, iluminado, sofisticado)
                        6. Mencione explicitamente que há fotos disponíveis ao lado que o cliente deve ver
                        7. Termine com uma pergunta ou convite para agendar uma visita
                        8. Mencione o link para mais detalhes
                        9. Use frases curtas, expressões de empolgação, e tom animado!
                        
                        FORMATAÇÃO DA RESPOSTA:
                        1. TÍTULO: Comece com um título em caixa alta e negrito para o imóvel em uma linha separada
                        2. INTRODUÇÃO: Adicione um parágrafo curto de resumo sobre o imóvel em linhas separadas
                        3. ESPAÇAMENTO: Use DUAS quebras de linha entre parágrafos e seções para criar espaço em branco
                        4. SEÇÕES: Cada seção deve começar com um título em negrito em uma linha separada
                        5. MARCADORES: Coloque cada característica em uma linha separada começando com um marcador (•)
                        6. DESTAQUE: Use elementos em negrito para destacar pontos importantes como preço e localização
                        7. EMOJIS: Use emojis relevantes no início de cada seção para tornar o texto mais atrativo
                        
                        Exemplo de estrutura (OBSERVE AS QUEBRAS DE LINHA - cada elemento fica em uma linha separada):
                        
                        **EXCELENTE IMÓVEL EM ZONA NOBRE** 🏠
                        
                        Olha só que oportunidade incrível! Este imóvel sensacional está localizado em uma das melhores regiões da cidade.
                        
                        **CARACTERÍSTICAS PRINCIPAIS:** ✨
                        
                        • 3 dormitórios espaçosos com armários planejados
                        • Cozinha completa com bancada em granito
                        • Área de lazer com piscina e churrasqueira
                        
                        **LOCALIZAÇÃO PRIVILEGIADA:** 📍
                        
                        A apenas 5 minutos do centro comercial, com fácil acesso a escolas e supermercados!
                        
                        **INVESTIMENTO:** 💰
                        
                        Um valor incrível de apenas R$ 850.000,00 para toda esta qualidade e conforto.
                        
                        **AGENDE UMA VISITA:** 📱
                        
                        Não perca tempo! Vamos marcar uma visita para você conhecer este imóvel maravilhoso?
                        
                        NÃO mencione que você é uma IA ou modelo de linguagem. Responda como se fosse um corretor real.
                        """
                        
                        # Gerar resposta com o modelo de linguagem
                        try:
                            resposta = self.llm.predict(prompt)
                        except Exception as e:
                            print(f"Erro ao gerar resposta com o modelo: {e}")
                            # Fallback para resposta estruturada simples
                            resposta = f"O imóvel {codigo_imovel} é {imovel['titulo']} e custa {imovel['preco']}. "
                            resposta += f"Está localizado em {imovel['endereco']}. "
                            resposta += f"Possui {dormitorios} dormitório(s), {banheiros} banheiro(s) e área total de {area}. "
                            resposta += f"\n\n{imovel['descricao']}"
                    else:
                        # Resposta estruturada simples
                        resposta = f"O imóvel {codigo_imovel} é {imovel['titulo']} e custa {imovel['preco']}. "
                        resposta += f"Está localizado em {imovel['endereco']}. "
                        resposta += f"Possui {dormitorios} dormitório(s), {banheiros} banheiro(s) e área total de {area}. "
                        resposta += f"\n\n{imovel['descricao']}"
                    
                    # Adicionar imovel relacionado
                    imovel_info = {
                        "codigo": imovel["codigo"],
                        "titulo": imovel["titulo"],
                        "preco": imovel["preco"],
                        "link": imovel["link"],
                        "dormitorios": caracteristicas.get("Dormitórios", ""),
                        "banheiros": caracteristicas.get("Banheiros", ""),
                        "garagem": caracteristicas.get("Vagas na garagem", ""),
                        "area": caracteristicas.get("Área total", ""),
                        "tipo": caracteristicas.get("Tipo", ""),
                        "features": [f"{k}: {v}" for k, v in caracteristicas.items()]
                    }
                    imoveis_relacionados.append(imovel_info)
                    
                    # PRIORIZAR LINKS DIRETOS DAS IMAGENS - esta é a parte que precisamos corrigir
                    # Verificar se o imóvel tem links_imagens (novo formato com URLs diretas)
                    if "links_imagens" in imovel and imovel["links_imagens"]:
                        # Filtrar links inválidos
                        imagens_relacionadas = [link for link in imovel["links_imagens"] 
                                              if link and not link.endswith('/') 
                                              and not link == "https://www.novatorres.com.br/"]
                    # Se não tiver links_imagens, verificar se tem imagem_principal
                    elif "imagem_principal" in imovel and imovel["imagem_principal"]:
                        imagens_relacionadas = [imovel["imagem_principal"]]
                    # Como último recurso, usar caminhos locais (formato antigo)
                    elif "imagens_locais" in imovel and imovel["imagens_locais"]:
                        # Usar URLs completas em vez de caminhos relativos
                        base_url = "https://www.novatorres.com.br/images/"
                        imagens_relacionadas = [base_url + img.replace('\\', '/') for img in imovel["imagens_locais"]]
                else:
                    resposta = f"Desculpe, não encontrei nenhum imóvel com o código {codigo_imovel}."
            
            # Caso contrário, buscar documentos relevantes e responder
            else:
                # Buscar imóveis que possam ser relevantes
                imoveis_filtrados = self.buscar_imoveis_por_texto(pergunta)
                
                if imoveis_filtrados and self.llm:
                    # Construir informações sobre os imóveis para o modelo
                    contexto_imoveis = ""
                    for i, imovel in enumerate(imoveis_filtrados[:3]):
                        caract = imovel.get("caracteristicas", {})
                        contexto_imoveis += f"\nImóvel {i+1}:\n"
                        contexto_imoveis += f"Código: {imovel['codigo']}\n"
                        contexto_imoveis += f"Título: {imovel['titulo']}\n"
                        contexto_imoveis += f"Preço: {imovel['preco']}\n"
                        contexto_imoveis += f"Endereço: {imovel['endereco']}\n"
                        contexto_imoveis += f"Dormitórios: {caract.get('Dormitórios', 'Não informado')}\n"
                        contexto_imoveis += f"Banheiros: {caract.get('Banheiros', 'Não informado')}\n"
                        contexto_imoveis += f"Área: {caract.get('Área total', 'Não informada')}\n"
                    
                    # Construir o prompt para o modelo de linguagem
                    prompt = f"""
                    Você é Torres Virtual, um assistente especializado em imóveis da Nova Torres Imobiliária, com personalidade calorosa e entusiasmada.
                    
                    O usuário perguntou: "{pergunta}"
                    
                    Com base nesta pergunta, encontrei os seguintes imóveis que podem ser relevantes:
                    {contexto_imoveis}
                    
                    DIRETRIZES IMPORTANTES PARA SUA RESPOSTA:
                    1. Fale com MUITO entusiasmo e empolgação sobre os imóveis
                    2. Use linguagem brasileira informal com expressões como "olha só", "super legal", "incrível", "sensacional"
                    3. Descreva detalhadamente pelo menos 3 características positivas de cada imóvel mencionado
                    4. Não se limite apenas aos dados - imagine e descreva como seria viver no imóvel, detalhes da vizinhança, etc
                    5. Mencione EXPLICITAMENTE que há fotos disponíveis para o cliente ver (diga "confira as fotos ao lado")
                    6. Sugira fortemente visitar o imóvel ou entrar em contato com a imobiliária
                    7. Mencione que o cliente pode clicar no link para ver mais detalhes
                    8. Crie um texto FLUIDO e NATURAL, não apenas listando características
                    9. Use gírias comuns do mercado imobiliário como "ótima planta", "acabamento de primeira", "localização privilegiada"
                    10. Termine com uma pergunta ou convite para o cliente
                    
                    FORMATAÇÃO DA RESPOSTA:
                    1. TÍTULO: Comece com um título em caixa alta e negrito para a seleção de imóveis, em uma linha separada
                    2. INTRODUÇÃO: Adicione um parágrafo curto que resuma a seleção encontrada
                    3. ESPAÇAMENTO: Use DUAS quebras de linha entre parágrafos e seções para criar espaço em branco
                    4. SEPARADORES: Use uma linha completa de separação como "---------------" em linha separada antes e depois de cada imóvel
                    5. NUMERAÇÃO: Coloque cada imóvel em uma seção claramente numerada (Ex: **IMÓVEL 1**, **IMÓVEL 2**) em linha separada
                    6. MARCADORES: Use marcadores (•) para listar as características principais, um por linha
                    7. DESTAQUE: Use elementos em negrito para destacar pontos importantes como preço e localização
                    8. EMOJIS: Use emojis relevantes para tornar o texto mais atrativo
                    
                    Exemplo de estrutura (OBSERVE AS QUEBRAS DE LINHA - cada elemento está em uma linha separada):
                    
                    **IMÓVEIS ENCONTRADOS PARA VOCÊ** 🏠
                    
                    Olha só que seleção especial encontrei para você! São opções sensacionais que atendem exatamente o que você procura.
                    
                    ---------------
                    
                    **IMÓVEL 1: APARTAMENTO NO CENTRO** 🌇
                    
                    • Preço: **R$ 850.000,00**
                    • 3 dormitórios espaçosos
                    • Localização privilegiada
                    
                    Este imóvel fica em uma região super valorizada, perto de todos os serviços que você precisa!
                    
                    ---------------
                    
                    **IMÓVEL 2: CASA EM CONDOMÍNIO** 🏡
                    
                    • Preço: **R$ 980.000,00**
                    • 4 dormitórios com suíte
                    • Área de lazer completa
                    
                    Uma propriedade incrível com excelente acabamento e espaço para toda a família.
                    
                    ---------------
                    
                    **ENTRE EM CONTATO:** 📱
                    
                    Estou à disposição para agendar uma visita. Não perca esta oportunidade!
                    
                    Para cada imóvel listado acima, o usuário poderá ver imagens e clicar no link para mais detalhes.
                    
                    NÃO mencione que você é uma IA ou modelo de linguagem. Responda como se fosse um corretor real.
                    """
                    
                    # Gerar resposta com o modelo de linguagem
                    try:
                        resposta = self.llm.predict(prompt)
                    except Exception as e:
                        print(f"Erro ao gerar resposta com o modelo: {e}")
                        # Fallback para resposta estruturada simples
                        resposta = self._gerar_resposta_generica(pergunta)
                else:
                    # Usar resposta genérica como fallback
                    resposta = self._gerar_resposta_generica(pergunta)
                
                # Adicionar até 3 imóveis aos resultados
                for imovel in imoveis_filtrados[:3]:
                    codigo = imovel["codigo"]
                    caracteristicas = imovel.get("caracteristicas", {})
                    
                    imovel_info = {
                        "codigo": codigo,
                        "titulo": imovel["titulo"],
                        "preco": imovel["preco"],
                        "link": imovel["link"],
                        "dormitorios": caracteristicas.get("Dormitórios", ""),
                        "banheiros": caracteristicas.get("Banheiros", ""),
                        "garagem": caracteristicas.get("Vagas na garagem", ""),
                        "area": caracteristicas.get("Área total", ""),
                        "tipo": caracteristicas.get("Tipo", ""),
                        "features": [f"{k}: {v}" for k, v in caracteristicas.items()]
                    }
                    imoveis_relacionados.append(imovel_info)
                    
                    # Se ainda não temos imagens, adicionar as do primeiro imóvel
                    if not imagens_relacionadas and len(imoveis_relacionados) == 1:
                        # PRIORIZAÇÃO DE LINKS DIRETOS
                        # Primeiro tentar usar os links diretos (novo formato)
                        if "links_imagens" in imovel and imovel["links_imagens"]:
                            # Filtrar links inválidos
                            imagens_relacionadas = [link for link in imovel["links_imagens"][:5] 
                                                  if link and not link.endswith('/') 
                                                  and not link == "https://www.novatorres.com.br/"]
                        # Se não tiver links diretos, usar a imagem principal
                        elif "imagem_principal" in imovel and imovel["imagem_principal"]:
                            imagens_relacionadas = [imovel["imagem_principal"]]
                        # Como último recurso, usar caminhos locais (formato antigo)
                        elif "imagens_locais" in imovel and imovel["imagens_locais"]:
                            # Usar URLs completas em vez de caminhos relativos
                            base_url = "https://www.novatorres.com.br/images/"
                            imagens_relacionadas = [base_url + img.replace('\\', '/') for img in imovel["imagens_locais"]]
        except Exception as e:
            import traceback
            print(f"Erro ao processar pergunta: {e}")
            print(traceback.format_exc())
            resposta = "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente mais tarde."
        
        # Limitar o número de imagens retornadas
        imagens_relacionadas = imagens_relacionadas[:5] if imagens_relacionadas else []
        
        # Garantir que todas as imagens sejam URLs diretas
        imagens_relacionadas = [img if img.startswith("http") else f"https://www.novatorres.com.br/{img.lstrip('/')}" 
                             for img in imagens_relacionadas if img]
        
        return {
            "resposta": resposta,
            "imoveis_relacionados": imoveis_relacionados,
            "imagens_relacionadas": imagens_relacionadas
        }
        
    def _gerar_resposta_generica(self, pergunta: str) -> str:
        """Gera uma resposta genérica com base na pergunta do usuário."""
        # Verificar se é uma busca por preço
        import re
        
        match_preco = re.search(r'(\d+)[\s]*(mil|milh[õo]es)', pergunta.lower())
        
        if "preço" in pergunta.lower() or "valor" in pergunta.lower() or match_preco:
            valor = None
            if match_preco:
                valor = match_preco.group(1)
                unidade = match_preco.group(2)
                
                if unidade.startswith("milh"):
                    valor = int(valor) * 1000000
                else:
                    valor = int(valor) * 1000
            
            if valor:
                return f"""**IMÓVEIS NA SUA FAIXA DE PREÇO** 💰

Olha só que legal! Temos diversos imóveis na faixa de preço de **R$ {valor:,}**.

Aqui estão algumas opções incríveis que selecionei especialmente para você:

---------------"""
            else:
                return """**IMÓVEIS COM DIFERENTES PREÇOS** 💰

Temos imóveis em diversas faixas de preço para atender ao seu orçamento!

Confira estas opções sensacionais que separei especialmente para você:

---------------"""
                
        # Verificar se é uma busca por localização
        locais = ["centro", "praia", "cal", "grande", "torres", "jardim", "predial"]
        for local in locais:
            if local.lower() in pergunta.lower():
                return f"""**IMÓVEIS EM {local.upper()}** 📍

Que maravilha! Temos diversas opções na região de **{local.capitalize()}**.

Confira estas propriedades especiais que selecionei para você:

---------------"""
        
        # Verificar se é uma busca por número de quartos
        match_quartos = re.search(r'(\d+)[\s]*(quartos|dormitórios|dormitorio)', pergunta.lower())
        if match_quartos or "quarto" in pergunta.lower() or "dormitório" in pergunta.lower():
            num_quartos = match_quartos.group(1) if match_quartos else ""
            if num_quartos:
                return f"""**IMÓVEIS COM {num_quartos} DORMITÓRIOS** 🛏️

Super legal! Encontrei imóveis com **{num_quartos} dormitórios** disponíveis.

Dê uma olhada nestas opções incríveis:

---------------"""
            else:
                return """**IMÓVEIS COM DIFERENTES CONFIGURAÇÕES** 🛏️

Temos imóveis com diferentes configurações de dormitórios para atender à sua necessidade!

Confira estas opções que separei especialmente para você:

---------------"""
        
        # Resposta padrão
        return """**IMÓVEIS SELECIONADOS PARA VOCÊ** 🏠

Olha só que bacana! Encontrei alguns imóveis que podem te interessar com base na sua pergunta.

Confira estas opções especiais:

---------------"""
        
    def buscar_imoveis_por_texto(self, texto: str) -> List[Dict[str, Any]]:
        """Busca imóveis com base em um texto livre."""
        import re
        
        # Extrair critérios da pergunta
        criterios = {}
        
        # Buscar por preço
        match_preco = re.search(r'(\d+)[\s]*(mil|milh[õo]es)', texto.lower())
        if match_preco:
            valor = int(match_preco.group(1))
            unidade = match_preco.group(2)
            
            if unidade.startswith("milh"):
                valor = valor * 1000000
            else:
                valor = valor * 1000
            
            criterios["preco_max"] = valor * 1.2  # 20% acima para dar margem
            criterios["preco_min"] = valor * 0.8  # 20% abaixo para dar margem
        
        # Buscar por quantidade de quartos
        match_quartos = re.search(r'(\d+)[\s]*(quartos|dormitórios|dormitorio)', texto.lower())
        if match_quartos:
            criterios["dormitorios"] = int(match_quartos.group(1))
        
        # Buscar por localização
        locais = ["centro", "praia", "cal", "grande", "torres", "jardim", "predial"]
        for local in locais:
            if local.lower() in texto.lower():
                criterios["localizacao"] = local
                break
        
        # Realizar a busca
        return self.buscar_imoveis(criterios)
        
    def buscar_imoveis(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca imóveis com base em filtros específicos."""
        if not self.dados_imoveis:
            return []
        
        resultados = []
        
        for imovel in self.dados_imoveis:
            # Flag para controlar se o imóvel atende a todos os critérios
            atende_criterios = True
            
            # Verificar preço mínimo
            if "preco_min" in filtros:
                try:
                    # Extrair apenas números do preço
                    import re
                    preco_numerico = float(re.sub(r'[^\d.]', '', imovel.get("preco", "0").replace(".", "").replace(",", ".")))
                    if preco_numerico < filtros["preco_min"]:
                        atende_criterios = False
                        continue
                except:
                    # Se não conseguir converter o preço, ignorar este critério
                    pass
            
            # Verificar preço máximo
            if "preco_max" in filtros:
                try:
                    # Extrair apenas números do preço
                    import re
                    preco_numerico = float(re.sub(r'[^\d.]', '', imovel.get("preco", "0").replace(".", "").replace(",", ".")))
                    if preco_numerico > filtros["preco_max"]:
                        atende_criterios = False
                        continue
                except:
                    # Se não conseguir converter o preço, ignorar este critério
                    pass
            
            # Verificar número de dormitórios
            if "dormitorios" in filtros:
                try:
                    dormitorios = imovel.get("caracteristicas", {}).get("Dormitórios", "0")
                    dormitorios_num = int(re.sub(r'[^\d]', '', dormitorios))
                    if dormitorios_num != filtros["dormitorios"]:
                        atende_criterios = False
                        continue
                except:
                    # Se não conseguir converter, ignorar este critério
                    pass
            
            # Verificar localização
            if "localizacao" in filtros:
                loc = filtros["localizacao"].lower()
                endereco = imovel.get("endereco", "").lower()
                titulo = imovel.get("titulo", "").lower()
                
                if loc not in endereco and loc not in titulo:
                    atende_criterios = False
                    continue
            
            # Se passou por todos os filtros, adicionar aos resultados
            if atende_criterios:
                resultados.append(imovel)
        
        # Limitar a 10 resultados
        return resultados[:10]


# Para teste direto
if __name__ == "__main__":
    assistente = AssistenteImobiliaria()
    perguntas_teste = [
        "Quais imóveis têm 2 quartos?",
        "Qual o imóvel mais caro disponível?",
        "Tem algum apartamento na praia?"
    ]
    
    for pergunta in perguntas_teste:
        print(f"\n\nPergunta: {pergunta}")
        resposta = assistente.responder(pergunta)
        print(f"Resposta: {resposta['resposta']}")
        
        if resposta["imoveis_relacionados"]:
            print("\nImóveis relacionados:")
            for imovel in resposta["imoveis_relacionados"]:
                print(f"- {imovel['codigo']}: {imovel['titulo']} - {imovel['preco']}")
                print(f"  Características: {imovel['dormitorios']} dormitórios, {imovel['garagem']} garagem(ns)")
                if imovel['features']:
                    print(f"  Recursos: {', '.join(imovel['features'])}")
        
        if resposta["imagens_relacionadas"]:
            print("\nImagens disponíveis:")
            for img in resposta["imagens_relacionadas"][:3]:  # Mostrar apenas 3 imagens
                print(f"- {img}") 