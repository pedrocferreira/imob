import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException, Cookie, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from assistente import AssistenteImobiliaria

# Carregar variáveis de ambiente
load_dotenv(Path(__file__).parent / '.env')

# Configurações
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"
DATA_DIR = Path(__file__).parent.parent / "data"

# Criar o diretório de arquivos estáticos se não existir
STATIC_DIR.mkdir(exist_ok=True)

# Certificar-se de que o caminho da imagem de placeholder existe
PLACEHOLDER_IMG = STATIC_DIR / "placeholder.jpg"
if not PLACEHOLDER_IMG.exists():
    # Se não existir, tentar criar um placeholder vazio
    try:
        import requests
        print("Baixando imagem de placeholder...")
        response = requests.get("https://placehold.co/600x400/e9ecef/495057?text=Im%C3%B3vel", stream=True)
        if response.status_code == 200:
            with open(PLACEHOLDER_IMG, 'wb') as f:
                f.write(response.content)
            print(f"Placeholder criado em {PLACEHOLDER_IMG}")
    except Exception as e:
        print(f"Erro ao criar imagem de placeholder: {e}")

# Definir modelos de dados para a API
class PerguntaRequest(BaseModel):
    pergunta: str = Field(..., description="Pergunta do usuário sobre imóveis")
    sessao_id: Optional[str] = Field(None, description="ID da sessão do usuário")

class ImovelRelacionado(BaseModel):
    codigo: str = Field(..., description="Código do imóvel")
    titulo: str = Field(..., description="Título do imóvel")
    preco: str = Field(..., description="Preço do imóvel")
    link: str = Field(..., description="Link para a página do imóvel")
    dormitorios: Optional[str] = Field(None, description="Quantidade de dormitórios")
    banheiros: Optional[str] = Field(None, description="Quantidade de banheiros")
    garagem: Optional[str] = Field(None, description="Quantidade de vagas de garagem")
    tipo: Optional[str] = Field(None, description="Tipo do imóvel")
    area: Optional[str] = Field(None, description="Área do imóvel")
    features: Optional[List[str]] = Field(None, description="Lista de características do imóvel")

class RespostaAssistente(BaseModel):
    resposta: str = Field(..., description="Resposta do assistente")
    imoveis_relacionados: List[ImovelRelacionado] = Field(default_factory=list, description="Imóveis relacionados à pergunta")
    imagens_relacionadas: List[str] = Field(default_factory=list, description="Imagens relacionadas à pergunta")
    sessao_id: str = Field(..., description="ID da sessão do usuário")

class FiltrosImoveis(BaseModel):
    dormitorios: Optional[int] = Field(None, description="Número de dormitórios")
    bairro: Optional[str] = Field(None, description="Bairro ou área")
    preco_max: Optional[float] = Field(None, description="Preço máximo")
    caracteristicas: Optional[List[str]] = Field(None, description="Lista de características desejadas")

# Inicializar o aplicativo FastAPI
app = FastAPI(
    title="Assistente Imobiliário - Nova Torres",
    description="API para o assistente de IA da imobiliária Nova Torres",
    version="1.0.0"
)

# Configurar templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Configurar arquivos estáticos
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Manter estes mounts para compatibilidade com versões antigas
# Agora eles serão usados apenas como fallback
app.mount("/images", StaticFiles(directory=str(DATA_DIR / "images_new")), name="images")
app.mount("/data/images", StaticFiles(directory=str(DATA_DIR / "images")), name="data_images")
app.mount("/imagens_simples", StaticFiles(directory=str(DATA_DIR / "imagens_simples")), name="imagens_simples")

# Inicializar o assistente
assistente = AssistenteImobiliaria()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, sessao_id: Optional[str] = Cookie(None)):
    """Página inicial do assistente."""
    # Se não houver sessão, criar uma nova
    if not sessao_id:
        sessao_id = assistente.gerenciador_conversas.iniciar_conversa()
    
    # Passar o ID da sessão para o template
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "Assistente Imobiliário - Nova Torres", "sessao_id": sessao_id}
    )

@app.post("/perguntar", response_model=RespostaAssistente)
async def perguntar(pergunta_request: PerguntaRequest, response: Response, sessao_id: Optional[str] = Cookie(None)):
    """Endpoint para fazer uma pergunta ao assistente."""
    pergunta = pergunta_request.pergunta
    
    # Usar o ID de sessão do cookie ou do request, ou criar um novo
    id_sessao = pergunta_request.sessao_id or sessao_id
    if not id_sessao:
        id_sessao = assistente.gerenciador_conversas.iniciar_conversa()
    
    # Definir o cookie de sessão
    response.set_cookie(key="sessao_id", value=id_sessao, max_age=3600*24*30)  # 30 dias
    
    if not pergunta or pergunta.strip() == "":
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia")
    
    try:
        with open("debug_log.txt", "a") as log_file:
            log_file.write(f"\n\n--- Nova requisição: {datetime.now()} ---\n")
            log_file.write(f"Pergunta: '{pergunta}' com sessão ID: {id_sessao}\n")
        
        # Chamar o assistente com o ID da sessão
        resultado = assistente.responder(pergunta, id_sessao)
        
        with open("debug_log.txt", "a") as log_file:
            log_file.write(f"Resultado obtido: {type(resultado)}\n")
            log_file.write(f"Conteúdo: {resultado}\n")
        
        # Extrair os valores do dicionário retornado
        resposta = resultado["resposta"]
        imoveis_relacionados = resultado.get("imoveis_relacionados", [])
        imagens_relacionadas = resultado.get("imagens_relacionadas", [])
        
        with open("debug_log.txt", "a") as log_file:
            log_file.write(f"Resposta extraída: {type(resposta)}\n")
            if isinstance(resposta, str):
                log_file.write(f"Resposta (primeiros 50 chars): {resposta[:50]}...\n")
            else:
                log_file.write(f"Resposta não é uma string: {resposta}\n")
            log_file.write(f"Imóveis relacionados: {len(imoveis_relacionados)}\n")
            log_file.write(f"Imagens relacionadas: {len(imagens_relacionadas)}\n")
        
        # Garantir que o ID da sessão está na resposta
        if "sessao_id" not in resultado:
            resultado["sessao_id"] = id_sessao
            
        # Formatar os imóveis relacionados para a resposta
        imoveis_formatados = []
        for imovel in imoveis_relacionados:
            # Extrair características do imóvel para a lista de features
            features = []
            if "features" in imovel and isinstance(imovel["features"], list):
                features = imovel["features"]
                
            imovel_formatado = ImovelRelacionado(
                codigo=imovel.get("codigo", ""),
                titulo=imovel.get("titulo", ""),
                preco=imovel.get("preco", ""),
                dormitorios=imovel.get("dormitorios", ""),
                banheiros=imovel.get("banheiros", ""),
                garagem=imovel.get("garagem", ""),
                area=imovel.get("area", ""),
                tipo=imovel.get("tipo", ""),
                link=imovel.get("link", ""),
                features=features
            )
            imoveis_formatados.append(imovel_formatado)
        
        # Construir resposta
        resposta_assistente = RespostaAssistente(
            resposta=resposta,
            imoveis_relacionados=imoveis_formatados,
            imagens_relacionadas=imagens_relacionadas,
            sessao_id=id_sessao
        )
        
        return resposta_assistente
    except Exception as e:
        import traceback
        erro_detalhado = traceback.format_exc()
        with open("debug_log.txt", "a") as log_file:
            log_file.write(f"ERRO DETALHADO:\n{erro_detalhado}\n")
            log_file.write(f"Tipo de erro: {type(e)}\n")
            log_file.write(f"Erro: {str(e)}\n")
        
        raise HTTPException(status_code=500, detail=f"Erro ao processar a pergunta: {str(e)}")

@app.get("/imagem/{path:path}")
async def redirecionar_imagem(path: str):
    """Redirecionar para links externos, caso necessário."""
    # Verificar se o caminho é uma URL completa
    if path.startswith(('http://', 'https://')):
        return RedirectResponse(url=path)
    
    # Caso contrário, construir URL completa (assumindo que é um caminho relativo ao site da imobiliária)
    url_completa = f"https://www.novatorres.com.br/{path.lstrip('/')}"
    return RedirectResponse(url=url_completa)

@app.post("/buscar", response_model=List[Dict[str, Any]])
async def buscar(filtros: FiltrosImoveis):
    """Endpoint para buscar imóveis com filtros específicos."""
    try:
        # Converter para dicionário e remover valores None
        filtros_dict = filtros.dict()
        filtros_dict = {k: v for k, v in filtros_dict.items() if v is not None}
        
        criterios = {}
        if "dormitorios" in filtros_dict:
            criterios["dormitorios"] = filtros_dict["dormitorios"]
        if "bairro" in filtros_dict:
            criterios["bairro"] = filtros_dict["bairro"]
        if "preco_max" in filtros_dict:
            criterios["preco_maximo"] = filtros_dict["preco_max"]
        if "caracteristicas" in filtros_dict:
            criterios["features"] = filtros_dict["caracteristicas"]
            
        # Usar o novo método de busca com critérios
        resultados = assistente.buscar_imoveis(criterios)
        
        # Formatar os resultados
        return [{
            "codigo": imovel["codigo"],
            "titulo": imovel["titulo"],
            "preco": imovel["preco"],
            "link": imovel["link"],
            "dormitorios": imovel.get("caracteristicas", {}).get("Dormitórios", ""),
            "banheiros": imovel.get("caracteristicas", {}).get("Banheiros", ""),
            "area": imovel.get("caracteristicas", {}).get("Área total", ""),
            "tipo": imovel.get("caracteristicas", {}).get("Tipo", ""),
            "endereco": imovel.get("endereco", "")
        } for imovel in resultados]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a busca: {str(e)}")

@app.get("/limpar-sessao")
async def limpar_sessao(response: Response):
    """Limpa a sessão atual e inicia uma nova."""
    # Criar nova sessão
    nova_sessao = assistente.gerenciador_conversas.iniciar_conversa()
    
    # Atualizar o cookie
    response.set_cookie(key="sessao_id", value=nova_sessao, max_age=3600*24*30)
    
    return {"message": "Sessão limpa com sucesso", "nova_sessao": nova_sessao}

# Função para executar o aplicativo diretamente
def main():
    """Função para executar o aplicativo diretamente."""
    import uvicorn
    print(f"Iniciando servidor em http://{HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)

if __name__ == "__main__":
    main() 