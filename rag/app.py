import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
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
async def index(request: Request):
    """Página inicial do assistente."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "Assistente Imobiliário - Nova Torres"}
    )

@app.post("/perguntar", response_model=RespostaAssistente)
async def perguntar(pergunta_request: PerguntaRequest):
    """Endpoint para fazer uma pergunta ao assistente."""
    pergunta = pergunta_request.pergunta
    
    if not pergunta or pergunta.strip() == "":
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia")
    
    try:
        resposta = assistente.responder(pergunta)
        
        # Nos certificamos que todas as imagens são URLs completas
        # Não é necessário modificá-las aqui, pois o assistente já retorna URLs completas
        
        return resposta
    except Exception as e:
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
        
        resultados = assistente.buscar_imoveis(filtros_dict)
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a busca: {str(e)}")

# Função para executar o aplicativo diretamente
def main():
    """Função para executar o aplicativo diretamente."""
    import uvicorn
    print(f"Iniciando servidor em http://{HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)

if __name__ == "__main__":
    main() 