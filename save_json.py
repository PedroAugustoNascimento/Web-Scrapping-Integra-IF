import json
import os

class JSON:
    def __init__(self):
        pass

    def salvar_dados_json(self, dados, nome_arquivo, pasta="perfis"):
        try:
            os.makedirs(pasta, exist_ok=True)

            caminho_arquivo = os.path.join(pasta, nome_arquivo)

            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)

            print(f"DEBUG - Dados salvos em {caminho_arquivo}")

        except Exception as e:
            print(f"DEBUG - Erro ao salvar dados em JSON: {e}")