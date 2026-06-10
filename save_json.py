import json

class JSON:
    def __init__(self):
        pass

    def salvar_dados_json(self, dados, nome_arquivo):
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            print(f"DEBUG - Dados salvos em {nome_arquivo}")
        except Exception as e:
            print(f"DEBUG - Erro ao salvar dados em JSON: {e}")