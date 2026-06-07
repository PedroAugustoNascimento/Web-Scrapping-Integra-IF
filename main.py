from scrapper import Scrapper
from save_csv import SaveCSV

def main():
    try:
        scrapper = Scrapper()

        scrapper.acessar_site("https://integra.ifmg.edu.br/ecossistema/pessoas")

        scrapper.selecionar_filtro_e_buscar("Ciência da Computação")

        scrapper.abrir_perfis()


    except Exception as e:
        print(f"Erro durante a execução: {e}")

    finally:
            scrapper.fechar()   


if __name__ == "__main__":
    main()