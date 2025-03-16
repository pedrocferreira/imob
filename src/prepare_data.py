import os
import json
import pandas as pd
from tqdm import tqdm

def carregar_dados(json_file='data/imoveis.json'):
    """Carrega os dados dos imóveis do arquivo JSON."""
    print(f"Carregando dados de {json_file}...")
    
    if not os.path.exists(json_file):
        print(f"Arquivo {json_file} não encontrado!")
        return []
    
    with open(json_file, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    print(f"Carregados {len(dados)} imóveis.")
    return dados

def gerar_perguntas_respostas(imovel):
    """Gera pares de perguntas e respostas para um imóvel específico."""
    qa_pairs = []
    
    # Informações básicas
    qa_pairs.append({
        "pergunta": f"Qual é o preço do imóvel {imovel['codigo']}?",
        "resposta": f"O preço deste imóvel é {imovel['preco']}."
    })
    
    qa_pairs.append({
        "pergunta": f"Onde fica localizado o imóvel {imovel['codigo']}?",
        "resposta": f"Este imóvel está localizado em {imovel['endereco']}."
    })
    
    # Título e descrição
    qa_pairs.append({
        "pergunta": f"Qual é o título deste imóvel?",
        "resposta": imovel['titulo']
    })
    
    qa_pairs.append({
        "pergunta": f"Descreva este imóvel.",
        "resposta": imovel['descricao']
    })
    
    # Características específicas
    for caracteristica, valor in imovel['caracteristicas'].items():
        qa_pairs.append({
            "pergunta": f"Qual é o/a {caracteristica.lower()} deste imóvel?",
            "resposta": f"O/A {caracteristica.lower()} deste imóvel é {valor}."
        })
    
    # Quantidades
    quartos = imovel['caracteristicas'].get('Dormitórios', 'não informado')
    banheiros = imovel['caracteristicas'].get('Banheiros', 'não informado')
    area = imovel['caracteristicas'].get('Área total', 'não informado')
    
    qa_pairs.append({
        "pergunta": f"Quantos quartos tem o imóvel {imovel['codigo']}?",
        "resposta": f"Este imóvel possui {quartos} quarto(s)."
    })
    
    qa_pairs.append({
        "pergunta": f"Quantos banheiros tem este imóvel?",
        "resposta": f"Este imóvel possui {banheiros} banheiro(s)."
    })
    
    qa_pairs.append({
        "pergunta": f"Qual é a área total deste imóvel?",
        "resposta": f"A área total deste imóvel é {area}."
    })
    
    # Perguntas mais abrangentes
    qa_pairs.append({
        "pergunta": f"Me fale sobre o imóvel {imovel['codigo']}.",
        "resposta": f"Este imóvel ({imovel['titulo']}) está localizado em {imovel['endereco']} e custa {imovel['preco']}. {imovel['descricao']}"
    })
    
    qa_pairs.append({
        "pergunta": f"Quais são as características do imóvel {imovel['codigo']}?",
        "resposta": ", ".join([f"{k}: {v}" for k, v in imovel['caracteristicas'].items()])
    })
    
    # Perguntas sobre imagens
    qa_pairs.append({
        "pergunta": f"Quantas imagens estão disponíveis para o imóvel {imovel['codigo']}?",
        "resposta": f"Este imóvel possui {len(imovel.get('imagens_locais', []))} imagens disponíveis."
    })
    
    # Adiciona a URL para acessar o imóvel
    qa_pairs.append({
        "pergunta": f"Onde posso ver mais detalhes sobre o imóvel {imovel['codigo']}?",
        "resposta": f"Você pode ver mais detalhes sobre este imóvel no link: {imovel['link']}"
    })
    
    return qa_pairs

def gerar_dataset_treinamento(imoveis, output_file='data/dataset_treinamento.json'):
    """Gera um dataset de treinamento com pares de perguntas e respostas para todos os imóveis."""
    print("Gerando dataset de treinamento...")
    
    todos_qa_pairs = []
    
    for imovel in tqdm(imoveis, desc="Processando imóveis"):
        qa_pairs = gerar_perguntas_respostas(imovel)
        todos_qa_pairs.extend(qa_pairs)
    
    print(f"Gerados {len(todos_qa_pairs)} pares de perguntas e respostas.")
    
    # Salvar como JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(todos_qa_pairs, f, ensure_ascii=False, indent=4)
    
    print(f"Dataset de treinamento salvo em {output_file}")
    
    # Salvar também como CSV
    csv_file = output_file.replace('.json', '.csv')
    pd.DataFrame(todos_qa_pairs).to_csv(csv_file, index=False, encoding='utf-8')
    print(f"Dataset de treinamento também salvo como CSV em {csv_file}")
    
    return todos_qa_pairs

def gerar_contexto_geral(imoveis, output_file='data/contexto_geral.md'):
    """Gera um arquivo de contexto geral sobre todos os imóveis, útil para fine-tuning."""
    print("Gerando contexto geral...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Informações sobre Imóveis da Nova Torres Imobiliária\n\n")
        f.write(f"Total de imóveis disponíveis: {len(imoveis)}\n\n")
        
        for idx, imovel in enumerate(imoveis):
            f.write(f"## Imóvel {idx+1}: {imovel['titulo']}\n\n")
            f.write(f"**Código:** {imovel['codigo']}\n")
            f.write(f"**Preço:** {imovel['preco']}\n")
            f.write(f"**Localização:** {imovel['endereco']}\n\n")
            
            f.write("**Características:**\n")
            for carac, valor in imovel['caracteristicas'].items():
                f.write(f"- {carac}: {valor}\n")
            
            f.write("\n**Descrição:**\n")
            f.write(f"{imovel['descricao']}\n\n")
            
            f.write(f"**Link para mais informações:** {imovel['link']}\n\n")
            
            if imovel.get('imagens_locais'):
                f.write(f"**Imagens disponíveis:** {len(imovel['imagens_locais'])}\n\n")
            
            f.write("---\n\n")
    
    print(f"Contexto geral salvo em {output_file}")

def main():
    """Função principal."""
    print("Iniciando preparação dos dados para IA...")
    
    # Carregar dados dos imóveis
    imoveis = carregar_dados()
    
    if not imoveis:
        print("Nenhum dado encontrado. Execute primeiro o scraper.")
        return
    
    # Gerar dataset de treinamento
    gerar_dataset_treinamento(imoveis)
    
    # Gerar contexto geral
    gerar_contexto_geral(imoveis)
    
    print("\nPreparação de dados concluída!")

if __name__ == "__main__":
    main() 