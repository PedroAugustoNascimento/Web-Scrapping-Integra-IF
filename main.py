from scrapper import Scrapper
from recognition import Recognition
from correcao_fotos import Corretor

def main():
    try:
        scrapper = Scrapper()
        recognition = Recognition()
        corretor = Corretor(pasta_fotos="fotos", pasta_json="perfis") #classe para retirar acentos dos nomes das fotos e dos arquivos JSON correspondentes

        #scrapper.acessar_site("https://integra.ifmg.edu.br/ecossistema/pessoas")
        #scrapper.selecionar_filtro_e_buscar("Ciência da Computação")
        #urls = scrapper.coletar_todas_urls()
        #scrapper.processar_perfis(urls)
        corretor.corrigir_nomes()  

    except Exception as e:
        print(f"Erro durante a execução: {e}")

    finally:
            if scrapper:
                scrapper.fechar()   

            #chama o reconhecimento racial das imagens salvas na pasta "fotos_teste ou fotos"
            recognition.executar_reconhecimento(pasta="fotos", pasta_json="perfis")


if __name__ == "__main__":
    main()