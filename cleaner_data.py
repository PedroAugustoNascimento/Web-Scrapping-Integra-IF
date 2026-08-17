import re

class CleanerData:

    secoes_principais = [
        "Formação Acadêmica/Titulação",
        "Atuações Profissionais",
        "Direção e Administração",
        "Atuações em Ensino",
        "Conselho, Comissão e Consultoria",
        "Participação em Projetos"
    ]

    def separar_secoes(self, texto):

        padrao = '|'.join(map(re.escape, self.secoes_principais))

        matches = list(re.finditer(padrao, texto))

        secoes = {}

        for i, match in enumerate(matches):

            titulo = match.group()

            inicio = match.end()

            fim = (
                matches[i + 1].start()
                if i < len(matches) - 1
                else len(texto)
            )

            conteudo = texto[inicio:fim].strip()

            if titulo == "Participação em Projetos":

                if titulo not in secoes:
                    secoes[titulo] = []

                secoes[titulo].append(conteudo)

            else:
                secoes[titulo] = conteudo


        return secoes
    
    def processar_formacao(self, texto):

        formacoes = []

        padrao = (
            r'(Doutorado|Mestrado|Especialização|Graduação)'
            r'(.*?)(?=(Doutorado|Mestrado|Especialização|Graduação|$))'
        )

        for match in re.finditer(padrao, texto, re.S):

            nivel = match.group(1)

            bloco = match.group(2)

            item = {
                "nivel": nivel
            }

            curso = re.search(
                r'([A-ZÀ-Úa-zà-úÇç ]+)\s*\((.*?)\)',
                bloco
            )

            if curso:
                item["curso"] = curso.group(1).strip()
                item["periodo"] = curso.group(2).strip()

            inst = re.search(
                r'Instituição:\s*(.*?)(?:\.|\n)',
                bloco
            )

            if inst:
                item["instituicao"] = inst.group(1).strip()

            titulo = re.search(
                r'Título:\s*(.*?)(?:\.|\n)',
                bloco
            )

            if titulo:
                item["titulo"] = titulo.group(1).strip()

            orientador = re.search(
                r'Orientador\(a\):\s*(.*?)(?:\.|\n)',
                bloco
            )

            if orientador:
                item["orientador"] = orientador.group(1).strip()

            formacoes.append(item)

        return formacoes

    def processar_atuacoes_profissionais(self, texto):

            atuacoes = []

            linhas = texto.split('\n')

            for linha in linhas:

                linha = linha.strip()

                match = re.match(
                    r'(.+?):\s*\((.*?)\)\s*(.*)',
                    linha
                )

                if match:

                    atuacoes.append({
                        "empresa": match.group(1).strip(),
                        "periodo": match.group(2).strip(),
                        "cargo": match.group(3).strip()
                    })

            return atuacoes

    def processar_projetos(self, secoes_projetos):

        projetos = []

        for bloco_instituicao in secoes_projetos:

            bloco_instituicao = bloco_instituicao.strip()

            if not bloco_instituicao:
                continue

            # Remove ":" que aparece depois de "Participação em Projetos:"
            bloco_instituicao = bloco_instituicao.lstrip(":").strip()

            linhas = bloco_instituicao.split('\n')

            if not linhas:
                continue

            # Primeira linha = instituição
            instituicao = linhas[0].strip()

            conteudo = '\n'.join(linhas[1:]).strip()

            # Localiza o início de cada projeto
            padrao_projeto = re.compile(
                r'(.+?)\s*-\s*\((\d{4}(?:\s*-\s*\d{4})?)\):'
            )

            matches = list(padrao_projeto.finditer(conteudo))

            for i, match in enumerate(matches):

                inicio = match.start()

                fim = (
                    matches[i + 1].start()
                    if i + 1 < len(matches)
                    else len(conteudo)
                )

                bloco_projeto = conteudo[inicio:fim].strip()

                projeto = {
                    "instituicao": instituicao,
                    "nome": match.group(1).strip(),
                    "periodo": match.group(2).strip()
                }

                # Natureza
                natureza = re.search(
                    r'Natureza:\s*(.*?)(?=\n|Equipe do Projeto:|Financiadores do Projeto:|$)',
                    bloco_projeto,
                    re.S
                )

                if natureza:
                    projeto["natureza"] = natureza.group(1).strip()

                # Equipe
                equipe = re.search(
                    r'Equipe do Projeto:\s*(.*?)(?=\n|Financiadores do Projeto:|$)',
                    bloco_projeto,
                    re.S
                )

                if equipe:

                    projeto["equipe"] = [
                        pessoa.strip()
                        for pessoa in equipe.group(1).split(',')
                        if pessoa.strip()
                    ]

                # Financiador
                financiador = re.search(
                    r'Financiadores do Projeto:\s*(.*?)(?=\n|$)',
                    bloco_projeto,
                    re.S
                )

                if financiador:
                    projeto["financiador"] = financiador.group(1).strip()

                projetos.append(projeto)

        return projetos

    def separar_subsecoes(self, texto, subsecoes):

        padrao = '|'.join(
            re.escape(secao)
            for secao in subsecoes
        )

        matches = list(
            re.finditer(
                padrao,
                texto,
                re.IGNORECASE
            )
        )

        secoes = {}

        for i, match in enumerate(matches):

            titulo = match.group().strip()

            inicio = match.end()

            fim = (
                matches[i + 1].start()
                if i < len(matches) - 1
                else len(texto)
            )

            conteudo = texto[inicio:fim].strip()

            secoes[titulo] = conteudo

        return secoes


    def limpar_dados_gerais(self, dados_gerais):
        secoes = self.separar_secoes(dados_gerais)

        return {
            "formacao": self.processar_formacao(
                secoes.get("Formação Acadêmica/Titulação", "")
            ),

            "atuacoes_profissionais": self.processar_atuacoes_profissionais(
                secoes.get("Atuações Profissionais", "")
            ),

            "direcao_administracao":
                secoes.get("Direção e Administração", ""),

            "ensino":
                secoes.get("Atuações em Ensino", ""),

            "comissoes":
                secoes.get("Conselho, Comissão e Consultoria", ""),

            "projetos": self.processar_projetos(
                secoes.get("Participação em Projetos", [])
            )
        }
    
    def limpar_producao_tecnica(self, dados_gerais):

        subsecoes = [
            "Software",
            "Apresentação de Trabalho",
            "Curso De Curta Duração Ministrado",
            "Organização De Evento"
        ]
            
        secoes = self.separar_subsecoes(
            dados_gerais,
            subsecoes
        )
    
        return {
            "producao_tecnica": self.processar_producao_tecnica(secoes)
        }
    
    def limpar_producao_bibliografica(self, texto):

        subsecoes = [
            "Livros Publicados ou Organizados",
            "Artigos Aceitos para Publicação",
            "Trabalhos em Eventos"
        ]

        secoes = self.separar_subsecoes(texto, subsecoes)

        return self.processar_producao_bibliografica(secoes)
    
    def limpar_producao_outra(self, texto):

        subsecoes = [
            "Outras Orientações Concluídas"
        ]

        secoes = self.separar_subsecoes(texto, subsecoes)

        return self.processar_producao_outra(secoes)

    def processar_producao_tecnica(self, secoes):

        return {

            "softwares": self.processar_softwares(
                secoes.get("Software", "")
            ),

            "apresentacoes_trabalho": self.processar_apresentacoes(
                secoes.get("Apresentação de Trabalho", "")
            ),

            "cursos_curta_duracao": self.processar_cursos(
                secoes.get("Curso De Curta Duração Ministrado", "")
            ),

            "organizacao_eventos": self.processar_eventos(
                secoes.get("Organização De Evento", "")
            )
        }
    
    def processar_softwares(self, texto):

        softwares = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?),\s*(.*?),\s*(\d{4})\.?\s*Finalidade:\s*(.*)',
                linha
            )

            if match:

                softwares.append({
                    "autor": match.group(1).strip(),
                    "software": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "finalidade": match.group(4).strip()
                })

        return softwares
    
    def processar_apresentacoes(self, texto):

        apresentacoes = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?),\s*(.+?),\s*(\d{4})\.\s*Instituição Promotora:\s*(.*)',
                linha
            )

            if match:

                apresentacoes.append({
                    "autores": match.group(1).strip(),
                    "titulo": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "instituicao_promotora": match.group(4).strip()
                })

        return apresentacoes
    
    def processar_cursos(self, texto):

        cursos = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?),\s*(.+?),\s*(\d{4})\.?$',
                linha
            )

            if match:

                cursos.append({
                    "autor": match.group(1).strip(),
                    "curso": match.group(2).strip(),
                    "ano": match.group(3).strip()
                })

        return cursos
    
    def processar_eventos(self, texto):

        eventos = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?),\s*(.+?),\s*(\d{4})\s*,\s*duração\s*\(semanas\)\s*(\d+)\.\s*Instituição Promotora:\s*(.*)',
                linha
            )

            if match:

                eventos.append({
                    "autores": match.group(1).strip(),
                    "evento": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "duracao_semanas": match.group(4).strip(),
                    "instituicao_promotora": match.group(5).strip()
                })

        return eventos
    
    def processar_eventos(self, texto):

        eventos = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?),\s*(.+?),\s*(\d{4})\s*,\s*duração\s*\(semanas\)\s*(\d+)\.\s*Instituição Promotora:\s*(.*)',
                linha,
                re.IGNORECASE
            )

            if match:

                eventos.append({
                    "autores": match.group(1).strip(),
                    "evento": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "duracao_semanas": match.group(4).strip(),
                    "instituicao_promotora": match.group(5).strip()
                })

        return eventos
    
    def processar_producao_bibliografica(self, secoes):

        return {
            "livros": self.processar_livros(
                secoes.get("Livros Publicados ou Organizados", "")
            ),

            "artigos": self.processar_artigos(
                secoes.get("Artigos Aceitos para Publicação", "")
            ),

            "trabalhos_eventos": self.processar_trabalhos_eventos(
                secoes.get("Trabalhos em Eventos", "")
            )
        }
    
    def processar_livros(self, texto):

        livros = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?);\s*(.+?),\s*(\d{4})\.\s*(.*)',
                linha
            )

            if match:

                livro = {
                    "autores": match.group(1).strip(),
                    "titulo": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "informacoes_adicionais": match.group(4).strip()
                }

                livros.append(livro)

        return livros
    
    def processar_artigos(self, texto):

        artigos = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?);\s*(.+?),\s*(\d{4})\.\s*Título do periódico ou revista:\s*(.*)',
                linha
            )

            if match:

                artigos.append({
                    "autores": match.group(1).strip(),
                    "titulo": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "periodico": match.group(4).strip()
                })

        return artigos
    
    def processar_trabalhos_eventos(self, texto):

        trabalhos = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?);\s*(.+?)\.\s*(.+?),\s*(.*?),\s*(\d{4})\.$',
                linha
            )

            if match:

                trabalhos.append({
                    "autores": match.group(1).strip(),
                    "titulo": match.group(2).strip(),
                    "evento": match.group(3).strip(),
                    "local": match.group(4).strip(),
                    "ano": match.group(5).strip()
                })

        return trabalhos
    
    def processar_orientacoes(self, texto):

        orientacoes = []

        linhas = texto.split('\n')

        for linha in linhas:

            linha = linha.strip()

            if not linha:
                continue

            match = re.match(
                r'(.+?)\.\s*(.+?)\s*\((\d{4})\)\.\s*'
                r'Nome do Curso:\s*(.*?)\.\s*'
                r'Nome da Instituição:\s*(.*?)(?:\.|$)',
                linha
            )

            if match:

                orientacoes.append({
                    "orientando": match.group(1).strip(),
                    "titulo": match.group(2).strip(),
                    "ano": match.group(3).strip(),
                    "curso": match.group(4).strip(),
                    "instituicao": match.group(5).strip()
                })

        return orientacoes
    
    def processar_producao_outra(self, secoes):

        return {
            "outras_orientacoes": self.processar_orientacoes(
                secoes.get("Outras Orientações Concluídas", "")
            )
        }