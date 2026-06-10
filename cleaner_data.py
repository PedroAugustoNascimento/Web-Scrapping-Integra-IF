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

            secoes[titulo] = texto[inicio:fim].strip()

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

    def processar_projetos(self, texto):

        projetos = []

        partes = re.split(
            r'(?=[A-Z].*?\(\d{4}(?:\s*-\s*\d{4})?\):)',
            texto
        )

        for bloco in partes:

            bloco = bloco.strip()

            if not bloco:
                continue

            projeto = {}

            cabecalho = re.search(
                r'^(.*?)\((.*?)\):',
                bloco
            )

            if cabecalho:

                projeto["nome"] = cabecalho.group(1).strip()
                projeto["periodo"] = cabecalho.group(2).strip()

            natureza = re.search(
                r'Natureza:\s*(.*)',
                bloco
            )

            if natureza:
                projeto["natureza"] = natureza.group(1).strip()

            equipe = re.search(
                r'Equipe do Projeto:\s*(.*)',
                bloco
            )

            if equipe:

                projeto["equipe"] = [
                    nome.strip()
                    for nome in equipe.group(1).split(',')
                    if nome.strip()
                ]

            financiador = re.search(
                r'Financiadores do Projeto:\s*(.*)',
                bloco
            )

            if financiador:
                projeto["financiador"] = financiador.group(1).strip()

            projetos.append(projeto)

        return projetos


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
                secoes.get("Participação em Projetos", "")
            )
        }
    
