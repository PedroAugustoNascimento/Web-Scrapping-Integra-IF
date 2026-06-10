from scrapper import Scrapper
# implementar a chamada da classe JSON para salvar os dados extraídos em um arquivo JSON -> atualmente está sendo chamado na classe Scrapper, fazer quando já tiver todos os dados limpos e higienizados
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