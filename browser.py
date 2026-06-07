from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def iniciar_browser():
    chrome_options = Options() # Configurações para o Chrome
    chrome_options.add_argument("--start-maximized") # Inicia o navegador maximizado
    service = ChromeService(executable_path=ChromeDriverManager().install()) # Gerrencia o driver do chrome
    driver = webdriver.Chrome(service=service, options=chrome_options) # Inicia o navegador com as opções configuradas
    return driver 
