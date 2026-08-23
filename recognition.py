import os
import sys
import json

# Suprime avisos do TensorFlow antes de importá-lo
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.stderr = open(os.devnull, 'w')

import cv2
import numpy as np
import warnings
from deepface import DeepFace
import tensorflow as tf
from pathlib import Path
import imghdr
import unicodedata

class Recognition:
    def __init__(self):
        # Configurações para silenciar os logs do TensorFlow
        tf.get_logger().setLevel('ERROR')
        #tf.compat.v1.disable_eager_execution() Teste para desativar a depreciação do TensorFlow
        warnings.filterwarnings("ignore", category=Warning, module="tensorflow")

    def remover_acentos(self, caminho):
        return "".join((c for c in unicodedata.normalize('NFD', str(caminho)) if unicodedata.category(c) != 'Mn'))

    #metodo para conversão de valores numpy para tipos nativos do Python, para evitar erros de serialização ao salvar em JSON. O padrão retornado pelo dp é float32
    def converter_numpy(self,obj):
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(f"Tipo não serializável: {type(obj)}")

    # conversão da raça detectada pelo DeepFace para a classificação do IBGE
    def mapear_raca_ibge(self, deepface_race):
        mapeamento = {
            'white': 'Branca',
            'black': 'Preta',
            'asian': 'Amarela',
            'latino hispanic': 'Parda',
            'middle eastern': 'Parda',
            'indian': 'Parda' 
        }
        return mapeamento.get(deepface_race, 'Não Identificado')

    def executar_reconhecimento(self, pasta="fotos", pasta_json="perfis"):
        print("\n" + "="*50)
        print("INICIANDO RECONHECIMENTO RACIAL (DEEPFACE)")
        print("="*50 + "\n")
        
        pasta_imagens = Path(pasta)
        extensoes_imagem = [".jpg", ".jpeg", ".png"]
        caminhos_imagens = []

        # Coleta todas as imagens na pasta
        for extensao in extensoes_imagem:
            caminhos_imagens.extend(pasta_imagens.glob(f"*{extensao}"))

        if not caminhos_imagens:
            print(f"Nenhuma imagem encontrada na pasta '{pasta}'.")
            return

        for imagem_path in caminhos_imagens:
            try:
                if imghdr.what(imagem_path) is None:
                    raise Exception(f"O arquivo não é uma imagem válida: {imagem_path}")
                
                imagem = cv2.imread(str(imagem_path))
                if imagem is None:
                    raise Exception(f"Não foi possivel carregar a imagem: {imagem_path}")

                #tratamento do nome da pessoa para exibição, removendo acentos e formatando para título
                nome_pessoa = self.remover_acentos(imagem_path.stem)
                nome_pessoa = nome_pessoa.replace('_', ' ').title()
                
                print(f"Analisando: {nome_pessoa}...")
                # reconhecimento racial usando DeepFace com backend MTCNN para detecção de rosto
                resultado = DeepFace.analyze(imagem, actions=["race"], detector_backend="mtcnn", enforce_detection=False) # enforce_detection=False evita quebrar se o rosto estiver parcial
                
                if isinstance(resultado, list) and resultado:
                    raca_original = resultado[0]["dominant_race"]
                    raca_ibge = self.mapear_raca_ibge(raca_original)
                    
                    #print(f"Nome: {nome_pessoa}")
                    #print(f"Raça Original (Deepface): {raca_original}")
                    #print(f"Raça Mapeada (IBGE): -> {raca_ibge} <-")
                    #print(f"Índice de Confiança para a detecção: {resultado[0]['face_confidence']}")

                    dados = {
                        "raca_original": raca_original,
                        "raca_ibge": raca_ibge,
                        "confiança": resultado[0]['face_confidence'],
                        "probabilidades_originais": resultado[0]['race']
                    }
                    
                    nome_arquivo_base = imagem_path.stem 
                    
                    # Monta o caminho exato onde o JSON deveria estar
                    caminho_json_alvo = Path(pasta_json) / f"{nome_arquivo_base}.json"

                    if caminho_json_alvo.exists(): # Verifica se o JSON realmente existe
                        try:
                            # 1. Abre e lê o JSON existente
                            with open(caminho_json_alvo, 'r', encoding='utf-8') as f:
                                json_existente = json.load(f)
                            
                            # 2. Adiciona a chave "Cor/Raça" com os dados detectados
                            json_existente["Cor/Raça"] = dados
                            
                            # 3. Sobrescreve o JSON com os dados atualizados
                            with open(caminho_json_alvo, 'w', encoding='utf-8') as f:
                                json.dump(json_existente, f, ensure_ascii=False, indent=4, default=self.converter_numpy)
                                
                            print(f"-> Dados salvos com sucesso no arquivo {caminho_json_alvo.name}")
                        except Exception as e:
                            print(f"-> Erro ao atualizar o arquivo JSON {caminho_json_alvo.name}: {e}")
                    else:
                        print(f"-> AVISO: Arquivo JSON não encontrado para {nome_pessoa} ({caminho_json_alvo})")
                    
                    #print("Probabilidades do Modelo Original:")
                    #for race, percentage in resultado[0]['race'].items():
                    #    print(f"\t{race}: {percentage:.2f}%")
                    #print("-" * 40)
                else:
                    print(f"Erro: Resultado inválido para a imagem {imagem_path.name}")
                    
            except Exception as e:
                print(f"Erro ao processar a imagem {imagem_path.name}: {e}\n")