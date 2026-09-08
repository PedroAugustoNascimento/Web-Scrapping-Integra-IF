from scrapper import Scrapper
from recognition import Recognition
import os

def main():
    scrapper = None
    try:
        scrapper = Scrapper()
        recognition = Recognition()

        caminho_arquivo = "sites.txt"
        if not os.path.exists(caminho_arquivo):
            print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
            return

        with open(caminho_arquivo, "r", encoding="utf-8") as file:
            urls_institutos = [linha.strip() for linha in file if linha.strip()]

        for url_site in urls_institutos:
            print(f"\n{'='*50}")
            print(f"INICIANDO COLETA NO SITE: {url_site}")
            print(f"{'='*50}")

            try:
                scrapper.acessar_site(url_site)
                scrapper.selecionar_filtro_e_buscar("Ciência da Computação")
                urls_perfis = scrapper.coletar_todas_urls()
                
                if urls_perfis:
                    scrapper.processar_perfis(urls_perfis)
                else:
                    print(f"Nenhuma URL encontrada para 'Ciência da Computação' no site {url_site}.")

            except Exception as e_site:
                # Se der erro em um site específico, avisa e pula para o próximo
                print(f"Erro durante a execução no site {url_site}: {e_site}")
                continue

    except Exception as e:
        print(f"Erro crítico durante a execução geral: {e}")

    finally:
        if scrapper:
            print("Fechando o navegador...")
            scrapper.fechar()   

        try:
            print("Iniciando reconhecimento facial/racial...")
            recognition.executar_reconhecimento(pasta="fotos", pasta_json="perfis")
        except Exception as e_rec:
            print(f"Erro durante o reconhecimento: {e_rec}")

if __name__ == "__main__":
    main()