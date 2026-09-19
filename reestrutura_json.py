import os
import json
import re

class RestruturadorJSON:
    def __init__(self, pasta_origem="perfis", pasta_destino="perfis_estruturados"):
        self.pasta_origem = pasta_origem
        self.pasta_destino = pasta_destino
        
        if not os.path.exists(self.pasta_destino):
            os.makedirs(self.pasta_destino)

    def extrair_anos(self, periodo_str):
        if not periodo_str:
            return None, None
            
        # Extrai todos os anos (começando com 19 ou 20 e tendo 4 dígitos)
        anos = re.findall(r'\b(?:19|20)\d{2}\b', str(periodo_str))
        
        if len(anos) >= 2:
            return int(anos[0]), int(anos[1])
        elif len(anos) == 1:
            return int(anos[0]), None
        
        return None, None

    def categorizar_cargo(self, cargo_str):
        cargo_str = str(cargo_str).strip(' .')
        if not cargo_str:
            return {"funcao": "Não informada", "vinculo": "Não informado", "descricao": ""}
        
        partes = [p.strip() for p in cargo_str.split(',')]
        
        funcao = partes[0] if len(partes) > 0 else "Não informada"
        vinculo = partes[1] if len(partes) > 1 else "Não informado"
        
        # Junta o resto como descrição
        descricao = ", ".join(partes[2:]) if len(partes) > 2 else ""
        
        # Correção de anomalia: se só tiver 2 partes, mas a segunda for muito longa,
        # provavelmente não é o vínculo, mas sim a descrição.
        if len(partes) == 2 and len(vinculo.split()) > 3:
            descricao = vinculo
            vinculo = "Não informado"

        return {"funcao": funcao, "vinculo": vinculo, "descricao": descricao}

    def padronizar_natureza(self, natureza_str):
        nat = str(natureza_str).lower().strip()
        if not nat: return 'Não informada'
        
        if 'pesquisa' in nat: return 'Pesquisa'
        if 'extens' in nat: return 'Extensão'
        if 'ensin' in nat: return 'Ensino'
        if 'desenvolv' in nat: return 'Desenvolvimento'
        if 'inova' in nat: return 'Inovação'
        
        return natureza_str.capitalize()

    def processar_perfil(self, dados):
        dados_gerais = dados.get("dados_gerais", {})
        if not dados_gerais:
            return dados
            
        # 1. Estruturar Formação
        for f in dados_gerais.get("formacao", []):
            ano_inicio, ano_fim = self.extrair_anos(f.get("periodo", ""))
            f["ano_inicio"] = ano_inicio
            f["ano_fim"] = ano_fim
            f.pop("periodo", None) # Remove o campo antigo (opcional)

        # 2. Estruturar Atuações Profissionais
        for a in dados_gerais.get("atuacoes_profissionais", []):
            ano_inicio, ano_fim = self.extrair_anos(a.get("periodo", ""))
            a["ano_inicio"] = ano_inicio
            a["ano_fim"] = ano_fim
            a.pop("periodo", None)
            
            cargo_detalhado = self.categorizar_cargo(a.get("cargo", ""))
            a["funcao"] = cargo_detalhado["funcao"]
            a["vinculo"] = cargo_detalhado["vinculo"]
            a["descricao"] = cargo_detalhado["descricao"]
            a.pop("cargo", None)

        # 3. Estruturar Projetos
        for p in dados_gerais.get("projetos", []):
            ano_inicio, ano_fim = self.extrair_anos(p.get("periodo", ""))
            p["ano_inicio"] = ano_inicio
            p["ano_fim"] = ano_fim
            p.pop("periodo", None)
            
            p["natureza"] = self.padronizar_natureza(p.get("natureza", ""))
            
            # Garante que a equipe seja sempre uma lista limpa
            if "equipe" in p and isinstance(p["equipe"], list):
                p["equipe"] = [membro.strip().title() for membro in p["equipe"] if membro.strip()]

        dados["dados_gerais"] = dados_gerais
        return dados

    def executar(self):
        arquivos = [f for f in os.listdir(self.pasta_origem) if f.endswith('.json')]
        print(f"Encontrados {len(arquivos)} perfis para estruturação.")

        sucesso = 0
        for arquivo in arquivos:
            caminho_origem = os.path.join(self.pasta_origem, arquivo)
            caminho_destino = os.path.join(self.pasta_destino, arquivo)

            try:
                # Carrega o JSON original
                with open(caminho_origem, 'r', encoding='utf-8') as f:
                    dados = json.load(f)

                # Aplica as transformações
                dados_estruturados = self.processar_perfil(dados)

                # Salva o novo JSON
                with open(caminho_destino, 'w', encoding='utf-8') as f:
                    json.dump(dados_estruturados, f, ensure_ascii=False, indent=4)
                
                sucesso += 1
            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}")

        print(f"Migração concluída! {sucesso}/{len(arquivos)} arquivos estruturados com sucesso na pasta '{self.pasta_destino}'.")

if __name__ == "__main__":
    # Certifique-se de que o nome da pasta de origem está correto (onde seus jsons estão hoje)
    restruturador = RestruturadorJSON(pasta_origem="perfis", pasta_destino="perfis_estruturados")
    restruturador.executar()