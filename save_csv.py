import csv
import os

class SaveCSV:
    #teste
    def __init__(self, caminho_saida: str = "resultados.csv"):
        self.caminho_saida = caminho_saida
        self.cabecalho_escrito = os.path.exists(caminho_saida)