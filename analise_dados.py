import os
import json
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text

class AnaliseDadosTCC:

    INSTITUTOS = {
        "IFMG": {"estado": "MG", "regiao": "Sudeste"},
        "IFRJ": {"estado": "RJ", "regiao": "Sudeste"},
        "IFBA": {"estado": "BA", "regiao": "Nordeste"},
        "IFRN": {"estado": "RN", "regiao": "Nordeste"},
        "IF Goiano": {"estado": "GO", "regiao": "Centro-Oeste"},
        "IFB": {"estado": "DF", "regiao": "Centro-Oeste"},
        "IFAM": {"estado": "AM", "regiao": "Norte"},
        "IFRS": {"estado": "RS", "regiao": "Sul"},
        "IFPA": {"estado": "PA", "regiao": "Norte"},
        "IFSC": {"estado": "SC", "regiao": "Sul"}
    }

    CATEGORIAS_RACA = ["Branca", "Parda", "Preta", "Amarela"]
    CATEGORIAS_FORMACAO = ["Especialização", "Mestrado", "Doutorado"]

    PALAVRAS_GESTAO = [
        "coordenador", "coordenadora", "coordenação", "coordenacao",
        "chefe", "chefia", "diretor", "diretora", "direção", "direcao",
        "gerente", "gerência", "gerencia"
    ]

    def __init__(self, pasta_perfis="perfis_estruturados", pasta_resultados="resultados", pasta_fotos="fotos"):
        self.pasta_perfis = pasta_perfis
        self.pasta_resultados = pasta_resultados
        self.pasta_fotos = pasta_fotos
        os.makedirs(self.pasta_resultados, exist_ok=True)
        self.df = pd.DataFrame()

    @staticmethod
    def normalizar_texto(texto):
        if not texto: return ""
        texto = str(texto).strip().lower()
        texto = unicodedata.normalize("NFD", texto)
        return "".join(c for c in texto if unicodedata.category(c) != "Mn")

    def extrair_raca(self, dados):
        cor_raca = dados.get("Cor/Raça", {})
        raca = cor_raca.get("raca_ibge", "") if isinstance(cor_raca, dict) else ""
        if not raca: return "Não informado"
        mapa = {"branca": "Branca", "parda": "Parda", "preta": "Preta", "amarela": "Amarela"}
        return mapa.get(self.normalizar_texto(raca), "Não informado")

    def obter_instituto_estado_regiao(self, dados):
        instituto = str(dados.get("instituto", "")).strip()
        if not instituto or instituto == "-": instituto = "Não informado"
        info = self.INSTITUTOS.get(instituto, {"estado": "Não informado", "regiao": "Não informado"})
        return instituto, info["estado"], info["regiao"]

    def extrair_formacao_maxima(self, dados):
        formacoes = dados.get("dados_gerais", {}).get("formacao", [])
        if not isinstance(formacoes, list): return "Outro"
        niveis = [self.normalizar_texto(f.get("nivel", "")) for f in formacoes if isinstance(f, dict)]
        if "doutorado" in niveis: return "Doutorado"
        if "mestrado" in niveis: return "Mestrado"
        if "especializacao" in niveis: return "Especialização"
        return "Outro"

    def possui_experiencia_gestao(self, dados):
        dados_gerais = dados.get("dados_gerais", {})
        atuacoes = dados_gerais.get("atuacoes_profissionais", [])
        if isinstance(atuacoes, list):
            for atuacao in atuacoes:
                if isinstance(atuacao, dict):
                    texto_atuacao = str(atuacao.get("funcao", "")) + " " + str(atuacao.get("descricao", ""))
                    if any(self.normalizar_texto(p) in self.normalizar_texto(texto_atuacao) for p in self.PALAVRAS_GESTAO):
                        return True
        direcao = self.normalizar_texto(str(dados_gerais.get("direcao_administracao", "")))
        if any(self.normalizar_texto(p) in direcao for p in self.PALAVRAS_GESTAO):
            return True
        return False

    def extrair_anos_projetos(self, dados):
        projetos = dados.get("dados_gerais", {}).get("projetos", [])
        anos = []
        if isinstance(projetos, list):
            for p in projetos:
                if isinstance(p, dict):
                    inicio = p.get("ano_inicio")
                    fim = p.get("ano_fim")
                    if isinstance(inicio, int):
                        if isinstance(fim, int) and fim >= inicio:
                            anos.extend(list(range(inicio, fim + 1)))
                        else:
                            anos.append(inicio)
        return anos

    def carregar_dados(self):
        registros = []
        arquivos = [a for a in os.listdir(self.pasta_perfis) if a.lower().endswith(".json")]
        for arquivo in arquivos:
            caminho = os.path.join(self.pasta_perfis, arquivo)
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                raca = self.extrair_raca(dados)
                if raca not in self.CATEGORIAS_RACA:
                    continue
                instituto, estado, regiao = self.obter_instituto_estado_regiao(dados)
                anos_projetos = self.extrair_anos_projetos(dados)
                registros.append({
                    "arquivo": arquivo, "instituto": instituto, "estado": estado,
                    "regiao": regiao, "raca": raca,
                    "formacao": self.extrair_formacao_maxima(dados),
                    "gestao": 1 if self.possui_experiencia_gestao(dados) else 0,
                    "total_projetos": len(anos_projetos)
                })
            except Exception as e:
                pass
        self.df = pd.DataFrame(registros)
        return self.df

    def exibir_e_salvar_tabela(self, tabela, nome_arquivo, titulo):
        print(f"\n{'='*70}\n{titulo}\n{'='*70}")
        print(tabela)
        caminho_csv = os.path.join(self.pasta_resultados, f"{nome_arquivo}.csv")
        tabela.to_csv(caminho_csv, encoding='utf-8-sig')
        print(f" -> Salvo em: {caminho_csv}")

    def analises_gerais_com_numeros(self):
        # 1. Distribuição por IF
        tab_if = pd.crosstab(self.df["instituto"], self.df["raca"]).reindex(columns=self.CATEGORIAS_RACA, fill_value=0)
        self.exibir_e_salvar_tabela(tab_if, "tabela_raca_if", "COR/RAÇA POR INSTITUTO FEDERAL")
        
        # 2. Distribuição por Região
        tab_reg = pd.crosstab(self.df["regiao"], self.df["raca"]).reindex(columns=self.CATEGORIAS_RACA, fill_value=0)
        self.exibir_e_salvar_tabela(tab_reg, "tabela_raca_regiao", "COR/RAÇA POR REGIÃO")

        # 3. Formação
        df_form = self.df[self.df["formacao"].isin(self.CATEGORIAS_FORMACAO)]
        tab_form = pd.crosstab(df_form["formacao"], df_form["raca"]).reindex(index=self.CATEGORIAS_FORMACAO, columns=self.CATEGORIAS_RACA, fill_value=0)
        self.exibir_e_salvar_tabela(tab_form, "tabela_formacao_raca", "FORMAÇÃO ACADÊMICA POR COR/RAÇA")

        # 4. Projetos (CORRIGIDO)
        media_projetos = self.df["total_projetos"].mean()
        std_projetos = self.df["total_projetos"].std()
        print(f"\n{'='*70}\nPROJETOS POR DOCENTE\n{'='*70}")
        print(f"Média total de projetos por docente na carreira: {media_projetos:.2f}")
        print(f"Desvio Padrão: {std_projetos:.2f} (Variação normal esperada entre pesquisadores)")
        
        tab_proj_raca = self.df.groupby('raca')['total_projetos'].agg(['mean', 'std']).round(2)
        self.exibir_e_salvar_tabela(tab_proj_raca, "tabela_projetos_raca", "MÉDIA DE PROJETOS POR COR/RAÇA")

        # 5. Gestão
        self.df['gestao_str'] = self.df['gestao'].map({1: 'Com experiência', 0: 'Sem experiência'})
        tab_gestao = pd.crosstab(self.df["gestao_str"], self.df["raca"]).reindex(columns=self.CATEGORIAS_RACA, fill_value=0)
        self.exibir_e_salvar_tabela(tab_gestao, "tabela_gestao_raca", "EXPERIÊNCIA EM GESTÃO/CHEFIA POR COR/RAÇA")

    def arvore_decisao_demografica(self):
        if self.df.empty: return
        
        features = ['raca', 'regiao', 'formacao']
        df_ml = self.df[features + ['gestao']].copy()
        
        X = pd.get_dummies(df_ml[features], drop_first=True)
        # Renomeando colunas para ficarem legíveis no gráfico
        X.columns = [col.replace('raca_', 'Raca:').replace('regiao_', 'Regiao:').replace('formacao_', 'Formacao:') for col in X.columns]
        y = df_ml['gestao']

        clf = DecisionTreeClassifier(max_depth=3, random_state=42, class_weight='balanced')
        clf.fit(X, y)

        plt.figure(figsize=(16, 8))
        plot_tree(clf, feature_names=list(X.columns), class_names=['Não é Chefe', 'Virou Chefe'],
                  filled=True, rounded=True, proportion=True, fontsize=11)
        plt.title("Árvore Sociodemográfica - Barreiras e Acessos à Gestão")
        
        caminho = os.path.join(self.pasta_resultados, "arvore_decisao_demografica.png")
        plt.savefig(caminho, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"\nNova Árvore Demográfica gerada: {caminho}")

    def executar_todas(self):
        self.carregar_dados()
        if self.df.empty: return
        self.analises_gerais_com_numeros()
        self.arvore_decisao_demografica()
        print("\nAnálise Concluída.")

    def gerar_graficos_analises(self):
        if self.df.empty:
            self.carregar_dados()
            
        cores_raca = ['#F5DEB3', '#D2B48C', '#8B4513', '#F0E68C'] # Cores temáticas por categoria

        # 1. Gráfico: Distribuição por IF
        tab_if = pd.crosstab(self.df["instituto"], self.df["raca"]).reindex(columns=self.CATEGORIAS_RACA, fill_value=0)
        fig, ax = plt.subplots(figsize=(12, 6))
        tab_if.plot(kind='bar', stacked=False, ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Distribuição de Cor/Raça por Instituto Federal', fontsize=14)
        plt.xlabel('Instituto', fontsize=12)
        plt.ylabel('Número de Docentes', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Cor/Raça')
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_raca_if.png'))
        plt.show()

        # 2. Gráfico: Distribuição por Região
        tab_reg = pd.crosstab(self.df["regiao"], self.df["raca"]).reindex(columns=self.CATEGORIAS_RACA, fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 6))
        tab_reg.plot(kind='bar', stacked=True, ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Composição de Cor/Raça por Região', fontsize=14)
        plt.xlabel('Região', fontsize=12)
        plt.ylabel('Total de Docentes', fontsize=12)
        plt.xticks(rotation=0)
        plt.legend(title='Cor/Raça', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_raca_regiao.png'))
        plt.show()

        # 3. Gráfico: Formação
        df_form = self.df[self.df["formacao"].isin(self.CATEGORIAS_FORMACAO)]
        tab_form = pd.crosstab(df_form["formacao"], df_form["raca"]).reindex(index=self.CATEGORIAS_FORMACAO, columns=self.CATEGORIAS_RACA, fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 6))
        tab_form.plot(kind='bar', ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Nível de Formação Acadêmica por Cor/Raça', fontsize=14)
        plt.xlabel('Nível de Formação', fontsize=12)
        plt.ylabel('Número de Docentes', fontsize=12)
        plt.xticks(rotation=0)
        plt.legend(title='Cor/Raça')
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_formacao_raca.png'))
        plt.show()

        # 4. Gráfico: Projetos (Média por Cor/Raça)
        tab_proj_mean = self.df.groupby('raca')['total_projetos'].mean().reindex(self.CATEGORIAS_RACA).fillna(0)
        tab_proj_std = self.df.groupby('raca')['total_projetos'].std().reindex(self.CATEGORIAS_RACA).fillna(0)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        tab_proj_mean.plot(kind='bar', yerr=tab_proj_std, capsize=5, ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Média de Anos em Projetos por Cor/Raça', fontsize=14)
        plt.xlabel('Cor/Raça', fontsize=12)
        plt.ylabel('Média de Projetos (anos)', fontsize=12)
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_projetos_raca.png'))
        plt.show()

        # 5. Gráfico: Gestão (% Com vs Sem experiência)
        self.df['gestao_str'] = self.df['gestao'].map({1: 'Com experiência', 0: 'Sem experiência'})
        tab_gestao = pd.crosstab(self.df["raca"], self.df["gestao_str"]).reindex(index=self.CATEGORIAS_RACA)
        # Convertendo para porcentagem na horizontal (100% stacked bar)
        tab_gestao_pct = tab_gestao.div(tab_gestao.sum(1), axis=0) * 100
        
        fig, ax = plt.subplots(figsize=(10, 6))
        tab_gestao_pct.plot(kind='barh', stacked=True, ax=ax, color=['#1f77b4', '#ff7f0e'], edgecolor='white')
        plt.title('Proporção de Experiência em Gestão por Cor/Raça', fontsize=14)
        plt.xlabel('Porcentagem (%)', fontsize=12)
        plt.ylabel('Cor/Raça', fontsize=12)
        plt.legend(title='Gestão/Chefia', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adicionando rótulos de dados
        for c in ax.containers:
            ax.bar_label(c, fmt='%.1f%%', label_type='center', color='white', weight='bold')
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_gestao_raca.png'))
        plt.show()
    
    def analisar_cobertura_completa(self):
        # 1. Carregar IDs das fotos disponíveis (ignorando extensão .jpg/.png)
        fotos_disponiveis = set()
        if os.path.exists(self.pasta_fotos):
            fotos_disponiveis = {os.path.splitext(f)[0] for f in os.listdir(self.pasta_fotos) if os.path.isfile(os.path.join(self.pasta_fotos, f))}

        registros = []
        arquivos = [a for a in os.listdir(self.pasta_perfis) if a.lower().endswith(".json")]

        # 2. Percorrer perfis JSON
        for arquivo in arquivos:
            id_perfil = os.path.splitext(arquivo)[0] # Pega "perfil_1" do "perfil_1.json"
            possui_foto = id_perfil in fotos_disponiveis
            
            caminho = os.path.join(self.pasta_perfis, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                try:
                    dados = json.load(f)
                except:
                    continue
            
            instituto = str(dados.get("instituto", "")).strip()
            if not instituto or instituto == "-": instituto = "Não informado"
                
            raca = self.extrair_raca(dados)
            raca_valida = raca in self.CATEGORIAS_RACA
            
            sucesso = possui_foto and raca_valida
            falha = possui_foto and not raca_valida

            registros.append({
                "instituto": instituto,
                "possui_foto": 1 if possui_foto else 0,
                "sucesso_deteccao": 1 if sucesso else 0,
                "falha_deteccao": 1 if falha else 0
            })

        df = pd.DataFrame(registros)
        
        # =====================================================================
        # RELATÓRIO GERAL
        # =====================================================================
        total = len(df)
        com_foto = df["possui_foto"].sum()
        sem_foto = total - com_foto
        sucesso_geral = df["sucesso_deteccao"].sum()
        falha_geral = df["falha_deteccao"].sum()

        print(f"\n{'='*70}\nRELATÓRIO GERAL DE COBERTURA\n{'='*70}")
        print(f"Total de Perfis Coletados: {total}")
        print(f" -> Com Foto: {com_foto} ({(com_foto/total)*100:.1f}%)")
        print(f" -> Sem Foto (indisponível no site): {sem_foto} ({(sem_foto/total)*100:.1f}%)")
        if com_foto > 0:
            print(f"    - Sucesso (Raça detectada): {sucesso_geral} ({(sucesso_geral/com_foto)*100:.1f}%)")
            print(f"    - Falha (Rosto indetectado): {falha_geral} ({(falha_geral/com_foto)*100:.1f}%)")

        # =====================================================================
        # RELATÓRIO POR INSTITUTO FEDERAL
        # =====================================================================
        resumo_if = df.groupby("instituto").agg(
            Perfis_Coletados=("instituto", "count"),
            Com_Foto=("possui_foto", "sum"),
            Raca_Detectada=("sucesso_deteccao", "sum"),
            Falha_Deteccao=("falha_deteccao", "sum")
        ).reset_index()

        print(f"\n{'='*70}\nRESUMO POR INSTITUTO FEDERAL\n{'='*70}")
        print(resumo_if.to_string(index=False))
        
        caminho_csv = os.path.join(self.pasta_resultados, "tabela_cobertura_institutos.csv")
        resumo_if.to_csv(caminho_csv, index=False, encoding="utf-8-sig")

        # =====================================================================
        # GRÁFICO POR INSTITUTO
        # =====================================================================
        fig, ax = plt.subplots(figsize=(14, 7))
        
        x = np.arange(len(resumo_if["instituto"]))
        width = 0.25 # Largura das barras
        
        # Criando barras agrupadas
        ax.bar(x - width, resumo_if["Perfis_Coletados"], width, label='Perfis Coletados (Total)', color='#B0C4DE', edgecolor='black')
        ax.bar(x, resumo_if["Com_Foto"], width, label='Com Foto Disponível', color='#4682B4', edgecolor='black')
        ax.bar(x + width, resumo_if["Raca_Detectada"], width, label='Raça Detectada (Sucesso AI)', color='#2E8B57', edgecolor='black')
        
        ax.set_ylabel('Quantidade de Docentes', fontsize=12)
        ax.set_title('Análise de Coleta e Reconhecimento Facial por Instituto Federal', fontsize=14, pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(resumo_if["instituto"], rotation=45, ha='right', fontsize=11)
        ax.legend(loc='upper right')
        
        # Adicionando rótulos de falha acima da barra de "Com Foto" para maior riqueza visual
        for idx, val in enumerate(resumo_if["Falha_Deteccao"]):
            if val > 0:
                y_pos = resumo_if["Com_Foto"].iloc[idx]
                ax.text(x[idx], y_pos + (resumo_if["Perfis_Coletados"].max()*0.02), f"{val} falhas", 
                        ha='center', va='bottom', fontsize=9, color='red', rotation=90)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        caminho_grafico_if = os.path.join(self.pasta_resultados, 'grafico_cobertura_if.png')
        plt.savefig(caminho_grafico_if, dpi=300)
        plt.show()
if __name__ == "__main__":
    analise = AnaliseDadosTCC()
    #analise.executar_todas()
    #analise.gerar_graficos_analises()
    analise.analisar_cobertura_completa()