from scrapper import Scrapper
from recognition import Recognition
from reestrutura_json import RestruturadorJSON  
from analise_dados import AnaliseDadosTCC    
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

            try:
                scrapper.acessar_site(url_site)
                scrapper.selecionar_filtro_e_buscar("Ciência da Computação")
                urls_perfis = scrapper.coletar_todas_urls()
                
                if urls_perfis:
                    scrapper.processar_perfis(urls_perfis)
                else:
                    print(f"Nenhuma URL encontrada para 'Ciência da Computação' no site {url_site}.")

            except Exception as e_site:
                # Se der erro em um site, continua para o próximo em vez de parar tudo (usando continue)
                print(f"Erro durante a execução no site {url_site}: {e_site}")
                with open("sites_com_erro.txt", "a", encoding="utf-8") as f_erro:
                    f_erro.write(f"Site: {url_site} | Erro: {e_site}\n")
                continue

        # Fecha o navegador assim que a coleta termina para liberar memória
        print("\nFechando o navegador da coleta...")
        scrapper.fechar()
        scrapper = None 

        try:
            recognition.executar_reconhecimento(pasta="fotos", pasta_json="perfis")
        except Exception as e_rec:
            print(f"Erro crítico durante o reconhecimento: {e_rec}")
            return # Se falhar aqui, não adianta analisar, então interrompe

        try:
            restruturador = RestruturadorJSON(pasta_origem="perfis", pasta_destino="perfis_estruturados")
            restruturador.executar()
        except Exception as e_res:
            print(f"Erro na reestruturação dos dados: {e_res}")
            return

        try:
            analise = AnaliseDadosTCC(
                pasta_perfis="perfis_estruturados",
                pasta_resultados="resultados"
            )
            analise.executar_todas()
        except Exception as e_ana:
            print(f"Erro na geração da análise de dados: {e_ana}")

    except Exception as e:
        print(f"Erro crítico não tratado no pipeline geral: {e}")

    finally:
        # Fallback de segurança para garantir que o navegador não fique fantasma na memória
        if scrapper:
            print("Fechando o navegador (fallback de erro)...")
            scrapper.fechar()

if __name__ == "__main__":
    main()