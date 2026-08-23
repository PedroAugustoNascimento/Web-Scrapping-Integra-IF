from scrapper import Scrapper
from recognition import Recognition
from deepface import DeepFace
# implementar a chamada da classe JSON para salvar os dados extraídos em um arquivo JSON -> atualmente está sendo chamado na classe Scrapper, fazer quando já tiver todos os dados limpos e higienizados
def main():
    try:
        scrapper = Scrapper()
        recognition = Recognition()

        #scrapper.acessar_site("https://integra.ifmg.edu.br/ecossistema/pessoas")
        #scrapper.selecionar_filtro_e_buscar("Ciência da Computação")
        #urls = scrapper.coletar_todas_urls()
        #scrapper.processar_perfis(urls)
        

    except Exception as e:
        print(f"Erro durante a execução: {e}")

    finally:
            if scrapper:
                scrapper.fechar()   

            #chama o reconhecimento racial das imagens salvas na pasta "fotos_teste"
            recognition.executar_reconhecimento(pasta="fotos", pasta_json="perfis")


if __name__ == "__main__":
    main()