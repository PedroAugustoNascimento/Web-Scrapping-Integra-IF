import unicodedata
from pathlib import Path

class Corretor:
    def __init__(self, pasta_fotos="foto_teste", pasta_json="perfis"):
        self.pasta_fotos = Path(pasta_fotos)
        self.pasta_json = Path(pasta_json)

    def remover_acentos(self, texto):
        return "".join(
            c for c in unicodedata.normalize('NFD', str(texto))
            if unicodedata.category(c) != 'Mn'
        )

    def corrigir_nomes(self):
        extensoes_imagem = [".jpg", ".jpeg", ".png"]
        caminhos_imagens = []

        for extensao in extensoes_imagem:
            caminhos_imagens.extend(self.pasta_fotos.glob(f"*{extensao}"))

        if not caminhos_imagens:
            print(f"Nenhuma imagem encontrada na pasta '{self.pasta_fotos}'.")
            return

        for imagem_path in caminhos_imagens:
            nome_original = imagem_path.stem
            nome_sem_acento = self.remover_acentos(nome_original)

            if nome_original == nome_sem_acento:
                continue

            # renomeia foto
            novo_caminho_imagem = imagem_path.with_name(f"{nome_sem_acento}{imagem_path.suffix}")

            if novo_caminho_imagem.exists():
                print(f"-> AVISO: já existe um arquivo com o nome '{novo_caminho_imagem.name}', pulando renomeação da foto.")
            else:
                imagem_path.rename(novo_caminho_imagem)
                print(f"Foto renomeada: '{imagem_path.name}' -> '{novo_caminho_imagem.name}'")

            # renomeia json
            caminho_json_original = self.pasta_json / f"{nome_original}.json"
            caminho_json_novo = self.pasta_json / f"{nome_sem_acento}.json"

            if caminho_json_original.exists():
                if caminho_json_novo.exists():
                    print(f"-> AVISO: já existe um JSON com o nome '{caminho_json_novo.name}', pulando renomeação do JSON.")
                else:
                    caminho_json_original.rename(caminho_json_novo)
                    print(f"JSON renomeado: '{caminho_json_original.name}' -> '{caminho_json_novo.name}'")
            else:
                print(f"-> AVISO: nenhum JSON encontrado para '{nome_original}' ({caminho_json_original})")

        print("\nCorreção de nomes concluída.\n")