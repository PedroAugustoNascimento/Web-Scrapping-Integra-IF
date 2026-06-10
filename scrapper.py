from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser import iniciar_browser
from cleaner_data import CleanerData
from save_json import JSON
import time
import base64
import os


class Scrapper:
    def __init__(self):
        self.driver = iniciar_browser()
        self.driver.implicitly_wait(10) # Espera implícita para elementos carregarem 
        self.wait = WebDriverWait(self.driver, 20)
        

    def acessar_site(self, url):
        self.driver.get(url)

    def selecionar_filtro_e_buscar(self, curso="Ciência da Computação"):
        filtro = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='integra-filter-areaAtuacao']"))
        )

        print("DEBUG - Campo de filtro encontrado, clicando")
        filtro.click() # Clicando no campo de filtro
        time.sleep(1)

        print("DEBUG - Digitando o nome do curso")
        filtro.send_keys(curso) # Digitando o nome do curso no campo de filtro
        time.sleep(2)

        print("DEBUG - Procurando pela opção do curso")
        opcao_xpath = f"//*[@title='{curso}']"
        opcao = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, opcao_xpath))
        )

        print("DEBUG - Opção encontrada, clicando")
        self.driver.execute_script("arguments[0].click();", opcao)
        
        print("DEBUG - Clicando no botão de buscar")
        buscar_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-cy='integra-filter-buscar']"))
        )
        buscar_btn.click()
        time.sleep(2) 

        print("DEBUG - Aguardando resultados aparecerem")
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "integra-item"))
        )
        time.sleep(2) 
        print("DEBUG - Resultados carregados")
    
    def abrir_perfis(self):
        perfis = self.driver.find_elements(
            By.XPATH, "//span[@data-cy='integra-item-tittle']/a"
        )

        urls = [p.get_attribute("href") for p in perfis]
        numeracao = 1
        for url in urls:
            print(f"DEBUG -Abrindo perfil: {url}")
            self.driver.get(url)

            time.sleep(2) 

            nome = self.get_nome()
            foto_perfil = self.get_foto_perfil()
            nome_arquivo = nome.replace(" ", "_").lower()
            self.baixar_foto(foto_perfil, nome_arquivo)
            print(f"DEBUG - Abrindo dados gerais")
            self.abrir_dados_gerais()
            dados_gerais = self.extrair_dados_gerais()
            cleaner = CleanerData()
            dados_limpos = cleaner.limpar_dados_gerais(dados_gerais)
            json = JSON()
            json.salvar_dados_json(dados_limpos, f"{nome_arquivo}.json")
            #print(f"DEBUG - Nome: {nome}")
            #print(f"DEBUG - Foto de perfil: {foto_perfil}")

            self.driver.back()

            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "integra-item"))
            )

    def get_nome(self):
        try:
            nome = self.driver.find_element(By.XPATH, "//h3[@class='titulo-interno__titulo text-muted']")
            return nome.text.strip().splitlines()[0]
        except Exception as e:
            print(f"Erro ao obter nome: {e}")
            return None
    
    def get_foto_perfil(self):
        try:
            foto = self.driver.find_element(By.XPATH, "//img[@class='rounded img-fluid w-100 b-img perfil__foto collapsed']")
            return foto.get_attribute("src")
        except Exception as e:
            print(f"Erro ao obter foto de perfil: {e}")
            return None

    def baixar_foto(self, src_foto, nome_arquivo, pasta="fotos"):
        if not src_foto:
            print("DEBUG - sem foto")
            return None

        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, f"{nome_arquivo}.png")

        try:
            # Remove o cabeçalho "data:image/png;base64," e decodifica
            dados_base64 = src_foto.split(",", 1)[1]
            dados_binarios = base64.b64decode(dados_base64)

            with open(caminho, "wb") as f:
                f.write(dados_binarios)

            print(f"DEBUG - Foto salva em: {caminho}")
            return caminho

        except Exception as e:
            print(f"Erro ao salvar foto: {e}")
            return None

    def abrir_dados_gerais(self):
        try:
            botao = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@data-cy='integra-tab-1']")
                )
            )

            self.driver.execute_script(
                "arguments[0].click();",
                botao
            )

            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='integra-tabs-panel-1']")
                )
            )

            print("DEBUG -Dados gerais carregados")

        except Exception as e:
            print(f"Erro ao abrir Dados Gerais: {e}") 

    def extrair_dados_gerais(self):
        try:
            dados = self.driver.find_element(By.XPATH, "//div[@id='integra-tabs-panel-1']")
            return dados.text.strip()
        except Exception as e:
            print(f"Erro ao extrair dados gerais: {e}")
            return None
        
    def fechar(self):
        self.driver.quit()