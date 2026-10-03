import os
import json
import unicodedata
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
                ano_ingresso_if = self.extrair_ano_ingresso_if(dados)
                registros.append({
                    "arquivo": arquivo, 
                    "instituto": instituto, 
                    "estado": estado,
                    "regiao": regiao, "raca": raca,
                    "formacao": self.extrair_formacao_maxima(dados),
                    "gestao": 1 if self.possui_experiencia_gestao(dados) else 0,
                    "total_projetos": len(anos_projetos),
                    "ano_ingresso": ano_ingresso_if
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
            
        cores_raca = ['#003f5c', '#78529b', '#ef537d', '#ffa600'] # Cores temáticas por categoria

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

    def analises_gerais_com_porcentagem(self):
        if self.df.empty:
            self.carregar_dados()
            
        print(f"\n{'='*70}\nANÁLISES EM PORCENTAGEM\n{'='*70}")

        # 1. Distribuição por IF (%)
        tab_if_pct = pd.crosstab(self.df["instituto"], self.df["raca"], normalize='index').reindex(columns=self.CATEGORIAS_RACA, fill_value=0) * 100
        self.exibir_e_salvar_tabela(tab_if_pct.round(2), "tabela_raca_if_pct", "PORCENTAGEM DE COR/RAÇA POR INSTITUTO FEDERAL (%)")
        
        # 2. Distribuição por Região (%)
        tab_reg_pct = pd.crosstab(self.df["regiao"], self.df["raca"], normalize='index').reindex(columns=self.CATEGORIAS_RACA, fill_value=0) * 100
        self.exibir_e_salvar_tabela(tab_reg_pct.round(2), "tabela_raca_regiao_pct", "PORCENTAGEM DE COR/RAÇA POR REGIÃO (%)")

        # 3. Formação (%)
        df_form = self.df[self.df["formacao"].isin(self.CATEGORIAS_FORMACAO)]
        tab_form_pct = pd.crosstab(df_form["formacao"], df_form["raca"], normalize='index').reindex(index=self.CATEGORIAS_FORMACAO, columns=self.CATEGORIAS_RACA, fill_value=0) * 100
        self.exibir_e_salvar_tabela(tab_form_pct.round(2), "tabela_formacao_raca_pct", "PORCENTAGEM DE COR/RAÇA POR FORMAÇÃO ACADÊMICA (%)")

    def gerar_graficos_porcentagem(self):
        if self.df.empty:
            self.carregar_dados()
            
        cores_raca = ['#003f5c', '#78529b', '#ef537d', '#ffa600']

        # Função auxiliar para adicionar os rótulos de % nos gráficos empilhados
        def adicionar_rotulos_pct(ax):
            for c in ax.containers:
                # Filtra valores muito pequenos (ex: < 2%) para não poluir o gráfico
                labels = [f'{v.get_height():.1f}%' if v.get_height() > 2 else '' for v in c]
                ax.bar_label(c, labels=labels, label_type='center', color='white', weight='bold', fontsize=9)

        # 1. Gráfico: Distribuição por IF (%)
        tab_if_pct = pd.crosstab(self.df["instituto"], self.df["raca"], normalize='index').reindex(columns=self.CATEGORIAS_RACA, fill_value=0) * 100
        fig, ax = plt.subplots(figsize=(12, 6))
        tab_if_pct.plot(kind='bar', stacked=True, ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Distribuição Proporcional de Cor/Raça por Instituto Federal', fontsize=14)
        plt.xlabel('Instituto', fontsize=12)
        plt.ylabel('Porcentagem (%)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Cor/Raça', bbox_to_anchor=(1.05, 1), loc='upper left')
        adicionar_rotulos_pct(ax)
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_raca_if_pct.png'))
        plt.show()

        # 2. Gráfico: Distribuição por Região (%)
        tab_reg_pct = pd.crosstab(self.df["regiao"], self.df["raca"], normalize='index').reindex(columns=self.CATEGORIAS_RACA, fill_value=0) * 100
        fig, ax = plt.subplots(figsize=(10, 6))
        tab_reg_pct.plot(kind='bar', stacked=True, ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Composição Proporcional de Cor/Raça por Região', fontsize=14)
        plt.xlabel('Região', fontsize=12)
        plt.ylabel('Porcentagem (%)', fontsize=12)
        plt.xticks(rotation=0)
        plt.legend(title='Cor/Raça', bbox_to_anchor=(1.05, 1), loc='upper left')
        adicionar_rotulos_pct(ax)
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_raca_regiao_pct.png'))
        plt.show()

        # 3. Gráfico: Formação (%)
        df_form = self.df[self.df["formacao"].isin(self.CATEGORIAS_FORMACAO)]
        tab_form_pct = pd.crosstab(df_form["formacao"], df_form["raca"], normalize='index').reindex(index=self.CATEGORIAS_FORMACAO, columns=self.CATEGORIAS_RACA, fill_value=0) * 100
        fig, ax = plt.subplots(figsize=(10, 6))
        tab_form_pct.plot(kind='bar', stacked=True, ax=ax, color=cores_raca, edgecolor='black')
        plt.title('Proporção de Cor/Raça por Nível de Formação', fontsize=14)
        plt.xlabel('Nível de Formação', fontsize=12)
        plt.ylabel('Porcentagem (%)', fontsize=12)
        plt.xticks(rotation=0)
        plt.legend(title='Cor/Raça', bbox_to_anchor=(1.05, 1), loc='upper left')
        adicionar_rotulos_pct(ax)
        plt.tight_layout()
        plt.savefig(os.path.join(self.pasta_resultados, 'grafico_formacao_raca_pct.png'))
        plt.show()
        
    def gerar_mapa_composicao_regioes(self):
            
            print("\nGerando mapa do Brasil (baixando malha espacial)...")
            
            if self.df.empty:
                self.carregar_dados()
                
            tab_reg_pct = pd.crosstab(self.df["regiao"], self.df["raca"], normalize='index') * 100

            # URL com o GeoJSON público dos Estados do Brasil
            url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
            
            try:
                gdf = gpd.read_file(url_geojson)
            except Exception as e:
                print(f"Erro ao obter dados espaciais: {e}")
                return

            # Mapeamento de Estados para Regiões
            mapa_regioes = {
                'Acre': 'Norte', 'Amapá': 'Norte', 'Amazonas': 'Norte', 'Pará': 'Norte', 'Rondônia': 'Norte', 'Roraima': 'Norte', 'Tocantins': 'Norte',
                'Alagoas': 'Nordeste', 'Bahia': 'Nordeste', 'Ceará': 'Nordeste', 'Maranhão': 'Nordeste', 'Paraíba': 'Nordeste', 'Pernambuco': 'Nordeste', 'Piauí': 'Nordeste', 'Rio Grande do Norte': 'Nordeste', 'Sergipe': 'Nordeste',
                'Goiás': 'Centro-Oeste', 'Mato Grosso': 'Centro-Oeste', 'Mato Grosso do Sul': 'Centro-Oeste', 'Distrito Federal': 'Centro-Oeste',
                'Espírito Santo': 'Sudeste', 'Minas Gerais': 'Sudeste', 'Rio de Janeiro': 'Sudeste', 'São Paulo': 'Sudeste',
                'Paraná': 'Sul', 'Rio Grande do Sul': 'Sul', 'Santa Catarina': 'Sul'
            }
            
            # Criar a coluna 'regiao' e mesclar os polígonos dos estados para formar a Região
            gdf['regiao'] = gdf['name'].map(mapa_regioes)
            gdf_regioes = gdf.dissolve(by='regiao').reset_index()

            # Cores definidas conforme sua solicitação
            cores = {
                'Norte': '#4c956c',      
                'Nordeste': '#ffa600',    
                'Centro-Oeste': '#ef537d', 
                'Sudeste': '#78529b',      
                'Sul': '#003f5c'          
            }
            gdf_regioes['cor'] = gdf_regioes['regiao'].map(cores)

            # Plotagem da Imagem
            fig, ax = plt.subplots(1, 1, figsize=(14, 12))
            ax.axis('off') # Remove a moldura quadrada padrão e os eixos X/Y
            
            ax.set_title("Composição de Cor/Raça do Corpo Docente por Região", 
                        fontsize=18, fontweight='bold', pad=15)

            # Plota os polígonos usando a paleta de cores criada
            gdf_regioes.plot(ax=ax, color=gdf_regioes['cor'], edgecolor='white', linewidth=1.5)

            # Adicionar os textos sobrepostos às regiões
            for idx, row in gdf_regioes.iterrows():
                regiao = row['regiao']
                
                # Pega o centróide (meio geográfico) da região
                centro_x = row['geometry'].centroid.x
                centro_y = row['geometry'].centroid.y
                
                # Ajustes finos de coordenada para o texto não sobrepor fronteiras ou outras regiões
                if regiao == 'Norte': 
                    # Movendo mais para a esquerda e para cima para fugir do Centro-Oeste
                    centro_x -= 1.0; centro_y += 1.5
                elif regiao == 'Nordeste': 
                    centro_x += 1.5; centro_y -= 1.0
                elif regiao == 'Sul': 
                    centro_x += 1.5; centro_y -= 0.5
                
                if regiao in tab_reg_pct.index:
                    pct = tab_reg_pct.loc[regiao]
                    
                    # Formata a caixinha de texto (sem a palavra da região, já que teremos legenda)
                    texto = (
                        f"{pct['Branca']:.1f}% Brancos\n"
                        f"{pct['Parda']:.1f}% Pardos\n"
                        f"{pct['Preta']:.1f}% Pretos\n"
                        f"{pct['Amarela']:.1f}% Amarelos"
                    )
                    
                    # Renderização do texto:
                    # Fonte menor (9) e caixa mais fina (pad=0.3) com fundo preto bem suave (alpha=0.25)
                    ax.text(
                        centro_x, centro_y, texto,
                        fontsize=9, fontweight='bold', color='white',
                        ha='center', va='center',
                        bbox=dict(facecolor='black', alpha=0.25, edgecolor='none', boxstyle='round,pad=0.3')
                    )

            # --- CRIANDO A LEGENDA ---
            # Cria as "amostras" de cor baseadas no seu dicionário original
            legend_patches = [mpatches.Patch(color=cor, label=reg) for reg, cor in cores.items()]
            
            # Adiciona a legenda no canto inferior esquerdo
            ax.legend(handles=legend_patches, title="Regiões do Brasil", 
                    loc='lower left', bbox_to_anchor=(0.05, 0.05),
                    fontsize=11, title_fontsize=13, frameon=True, shadow=True)

            plt.tight_layout()
            caminho_mapa = os.path.join(self.pasta_resultados, "mapa_raca_regioes_pct.png")
            plt.savefig(caminho_mapa, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f" -> Mapa salvo com sucesso em: {caminho_mapa}")

    def extrair_ano_ingresso_if(self, dados):

        anos_if = []
        atuacoes = dados.get("dados_gerais", {}).get("atuacoes_profissionais", [])
        
        if isinstance(atuacoes, list):
            for atuacao in atuacoes:
                if isinstance(atuacao, dict):
                    empresa = self.normalizar_texto(atuacao.get("empresa", ""))
                    
                    if "instituto federal" in empresa or "escola tecnica federal" in empresa or "if" in empresa.split():
                        inicio = atuacao.get("ano_inicio")
                        if isinstance(inicio, int) and 1950 <= inicio <= 2026:
                            anos_if.append(inicio)
                            
        if anos_if:
            return min(anos_if)
        return None

    def analisar_evolucao_historica_raca(self):
            print("\n" + "="*70)
            print("EVOLUÇÃO HISTÓRICA DE INGRESSO (DE 5 EM 5 ANOS) POR COR/RAÇA")
            print("="*70)
            
            if self.df.empty:
                self.carregar_dados()

            df_tempo = self.df.dropna(subset=['ano_ingresso']).copy()
            df_tempo['ano_ingresso'] = df_tempo['ano_ingresso'].astype(int)

            bins = [0, 2000, 2005, 2010, 2015, 2020, 2026]
            labels = ['Até 2000', '2001-2005', '2006-2010', '2011-2015', '2016-2020', '2021-2026']
            
            df_tempo['quinquenio'] = pd.cut(df_tempo['ano_ingresso'], bins=bins, labels=labels, right=True)

            tab_abs = pd.crosstab(df_tempo['quinquenio'], df_tempo['raca']).reindex(columns=self.CATEGORIAS_RACA, fill_value=0)
            tab_pct = pd.crosstab(df_tempo['quinquenio'], df_tempo['raca'], normalize='index').reindex(columns=self.CATEGORIAS_RACA, fill_value=0) * 100

            # =====================================================================
            # 1. SALVAR AS TABELAS (PORCENTAGEM E ABSOLUTA)
            # =====================================================================
            self.exibir_e_salvar_tabela(tab_pct.round(2), "tabela_evolucao_raca_pct", "PORCENTAGEM DE INGRESSO POR PERÍODO (%)")
            
            # Cria uma cópia para adicionar a coluna "Total" sem atrapalhar o gráfico
            tab_abs_com_total = tab_abs.copy()
            tab_abs_com_total['Total do Período'] = tab_abs_com_total.sum(axis=1)
            self.exibir_e_salvar_tabela(tab_abs_com_total, "tabela_evolucao_raca_absoluta", "NÚMERO ABSOLUTO DE INGRESSANTES POR PERÍODO")

            # Configuração de Cores
            cores_raca_dict = {'Branca': '#003f5c', 'Parda': '#78529b', 'Preta': '#ef537d', 'Amarela': '#ffa600'}
            cores_raca_lista = [cores_raca_dict.get(r, 'gray') for r in self.CATEGORIAS_RACA]

            # =====================================================================
            # 2. GRÁFICO DE PORCENTAGEM (LINHAS)
            # =====================================================================
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            
            for raca in self.CATEGORIAS_RACA:
                if raca in tab_pct.columns:
                    ax1.plot(tab_pct.index, tab_pct[raca], marker='o', linewidth=2.5, 
                            label=raca, color=cores_raca_dict.get(raca, 'gray'))
                    
                    for i, valor in enumerate(tab_pct[raca]):
                        ax1.annotate(f'{valor:.1f}%', 
                                    (i, valor), 
                                    textcoords="offset points", 
                                    xytext=(0,10), 
                                    ha='center', fontsize=9)

            ax1.set_title('Evolução do Perfil Racial (Ano de Ingresso nos IFs) - %', fontsize=15, fontweight='bold', pad=15)
            ax1.set_xlabel('Período de Ingresso', fontsize=12)
            ax1.set_ylabel('Porcentagem das Vagas no Período (%)', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.6)
            
            ax1.set_ylim(0, tab_pct.max().max() + 15) 
            ax1.legend(title='Cor/Raça', bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            caminho_grafico_pct = os.path.join(self.pasta_resultados, 'grafico_evolucao_historica_pct.png')
            plt.savefig(caminho_grafico_pct, dpi=300, bbox_inches='tight')
            plt.close(fig1)
            
            print(f" -> Gráfico de evolução (%) salvo em: {caminho_grafico_pct}")

            # =====================================================================
            # 3. GRÁFICO ABSOLUTO (BARRAS EMPILHADAS)
            # =====================================================================
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            
            tab_abs.plot(kind='bar', stacked=True, ax=ax2, color=cores_raca_lista, edgecolor='black')
            
            ax2.set_title('Volume Absoluto de Ingressos por Cor/Raça ao Longo do Tempo', fontsize=15, fontweight='bold', pad=15)
            ax2.set_xlabel('Período de Ingresso', fontsize=12)
            ax2.set_ylabel('Número Total de Docentes Contratados', fontsize=12)
            ax2.tick_params(axis='x', labelrotation=0)
            ax2.legend(title='Cor/Raça', bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Adicionando os rótulos de dados absolutos dentro das barras
            for c in ax2.containers:
                labels_bar = [f'{int(v.get_height())}' if v.get_height() > 0 else '' for v in c]
                ax2.bar_label(c, labels=labels_bar, label_type='center', color='white', weight='bold', fontsize=10)

            plt.tight_layout()
            caminho_grafico_abs = os.path.join(self.pasta_resultados, 'grafico_evolucao_absoluta.png')
            plt.savefig(caminho_grafico_abs, dpi=300, bbox_inches='tight')
            plt.close(fig2)
            
            print(f" -> Gráfico de evolução absoluta salvo em: {caminho_grafico_abs}")
    
if __name__ == "__main__":
    analise = AnaliseDadosTCC()
    #analise.executar_todas()
    #analise.gerar_graficos_analises()
    #analise.analisar_cobertura_completa()
    #analise.analises_gerais_com_porcentagem()
    #analise.gerar_graficos_porcentagem()
    #analise.gerar_mapa_composicao_regioes()
    analise.analisar_evolucao_historica_raca()