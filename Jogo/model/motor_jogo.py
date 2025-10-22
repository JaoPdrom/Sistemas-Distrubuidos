import yaml
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class MotorJogo:

    def __init__(self, arquivo_historia: str): #construtor da classe
        self.historia = self.carregar_historia(arquivo_historia) #armazena o arquivo yaml da historia
        self.trecho_atual = None #armazena o trecho atual da historia
        self.votos = {} #dicionario para armazenar os votos dos jogadores
        self.chat = [] #lista para armazenar as mensagens do chat
        self.jogadores_conectados = {}  #dicionario para armazenar os jogadores únicos
        self.jogo_iniciado = False #flag para verificar se o jogo foi iniciado
        self.jogadores_prontos = set()  # quem clicou em "Continuar"
        self.proximo_trecho_pendente = None  # trecho aguardando todos confirmarem


    def carregar_historia(self, arquivo: str) -> dict:
        """Carrega o arquivo YAML de história a partir de model/dao/."""
        try:
            caminho_absoluto = os.path.join(BASE_DIR, "dao", arquivo)
            print(f"[DEBUG] Tentando carregar história de: {caminho_absoluto}")

            if not os.path.exists(caminho_absoluto):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_absoluto}")

            with open(caminho_absoluto, "r", encoding="utf-8") as arq_historia:
                dados = yaml.safe_load(arq_historia)

            if not isinstance(dados, dict):
                raise ValueError("O arquivo YAML deve conter um dicionário como estrutura principal.")

            print("[DEBUG] História carregada com sucesso.")
            return dados

        except FileNotFoundError as e:
            print(f"Erro: {e}")
            return {}
        except yaml.YAMLError as e:
            print(f"Erro ao carregar o arquivo YAML: {e}")
            return {}
        
    def adicionar_jogador(self, nome: str):        
        # Se o jogador ainda não existe, cria seu registro
        if nome not in self.jogadores_conectados:
            self.jogadores_conectados[nome] = {"conectado": True, "votou": False}
        else:
            # Se ele já existia, apenas marca como reconectado
            self.jogadores_conectados[nome]["conectado"] = True

        total = len(self.jogadores_conectados)

        # Se ainda não atingiu 4 jogadores
        if total < 4:
            faltam = 4 - total
            return f"👋 {nome} entrou no jogo. Aguardando mais {faltam} jogador(es)..."
        
        # Se atingiu 4 jogadores e o jogo ainda não começou
        elif total == 4 and not self.jogo_iniciado:
            self.iniciar_jogo()
            self.jogo_iniciado = True
            return "🎮 Quatro jogadores conectados! O jogo começou!"
        
        # Caso já esteja iniciado, apenas informa entrada
        else:
            return f"{nome} entrou no jogo. O jogo já está em andamento!"

    def iniciar_jogo(self):
        if not self.historia: #verifica se a historia foi carregada corretamente
            raise RuntimeError("História não carregada corretamente.")
        
        try:
            self.trecho_atual = next(iter(self.historia)) #pega o primeiro trecho da historia
        except StopIteration:
            raise RuntimeError("A história está vazia.")
        
        self.votos.clear() #limpa os votos
        self.chat.clear() #limpa o chat

        for nome in self.jogadores_conectados:
            self.jogadores_conectados[nome]["votou"] = False #marca todos os jogadores como não votaram ainda

            self.jogo_iniciado = True #marca o jogo como iniciado

        # 🆕 Detecta se o trecho inicial não tem opções
        trecho = self.historia[self.trecho_atual]
        if not trecho.get("opcoes"):
            self.proximo_trecho_pendente = trecho.get("proximo")  # se houver “proximo” direto
            return {
                "mensagem": f"🧭 O jogo começou! Trecho inicial: {self.trecho_atual}",
                "sem_opcoes": True
            }

        return {
            "mensagem": f"🧭 O jogo começou! Trecho inicial: {self.trecho_atual}",
            "sem_opcoes": False
        }


    def obter_trecho_atual(self, formatado=True):
        """Retorna o texto formatado do trecho atual da história."""
        if self.trecho_atual is None:  # verifica se o jogo foi iniciado
            return "O jogo não foi iniciado."
        
        trecho = self.historia[self.trecho_atual]  # pega o trecho atual da história

        # Define quais opções mostrar (todas ou só as empatadas)
        if hasattr(self, "opcoes_empate") and self.opcoes_empate:  # verifica se tem empate
            opcoes_exibir = []
            for indice in self.opcoes_empate:  # reinicia a votação mostrando apenas as opções empatadas
                opcoes_exibir.append(trecho["opcoes"][indice - 1])
            modo_empate = True
        else:
            opcoes_exibir = trecho.get("opcoes", [])  # mostra todas as opções normais sem empate
            modo_empate = False

            # Se o chamador pediu formato puro (para envio via rede, por exemplo)
            if not formatado:
                return {
                    "texto": trecho["texto"],
                    "opcoes": opcoes_exibir
                }

        # 🧭 Cabeçalho do trecho
        texto = f"\n🧭 Trecho atual: {self.trecho_atual}\n\n"

        # 📖 Formata o texto principal mantendo quebras de linha
        texto_bruto = trecho.get("texto", "")
        if isinstance(texto_bruto, str):
            # Garante que \n do YAML sejam mantidos e remove espaços extras
            texto += texto_bruto.strip() + "\n"
        elif isinstance(texto_bruto, list):
            # Caso o texto venha em lista de parágrafos (formato alternativo)
            texto += "\n\n".join(p.strip() for p in texto_bruto if p.strip()) + "\n"

        # 🏁 Caso não existam opções, considera fim da história
        if not opcoes_exibir:
            texto += "\nFim da história\n"
            return texto

        # ⚖️ Caso de empate
        if modo_empate:
            texto += "\nEmpate detectado! Vote novamente entre as opções abaixo:\n"
        else:
            texto += "\nOpções disponíveis:\n"

        # 🗳️ Lista as opções numeradas
        for i, opcao in enumerate(opcoes_exibir, start=1):
            texto += f"  {i}. {opcao['texto']}\n"

        return texto

    
    def registrar_voto(self, jogador: str, opcao: int):
        """Registra o voto do jogador e verifica se todos já votaram."""
        
        if not self.jogo_iniciado:
            return "O jogo ainda não começou."

        if jogador not in self.jogadores_conectados:
            return "Jogador não está registrado no jogo."

        if self.jogadores_conectados[jogador]["votou"]:
            return "Você já votou nesta rodada."

        trecho = self.historia[self.trecho_atual]
        opcoes_disponiveis = trecho.get("opcoes", [])

        # Verifica se há opções e se a escolhida é válida
        if not opcoes_disponiveis:
            return "Não há opções disponíveis neste trecho."
        if opcao < 1 or opcao > len(opcoes_disponiveis):
            return "Opção inválida."

        # Registra o voto e marca o jogador como já tendo votado
        self.votos[jogador] = opcao
        self.jogadores_conectados[jogador]["votou"] = True

        total_jogadores = len(self.jogadores_conectados)
        total_votos = len(self.votos)

        # Se todos já votaram, calcula o resultado
        if total_votos == total_jogadores:
            resultado = self.calcular_resultados()
            return f"{jogador} registrou seu voto.\n{resultado}"
        else:
            faltam = total_jogadores - total_votos
            return f"✅ {jogador} registrou seu voto. Aguardando {faltam} voto(s)..."
 
    
    def calcular_resultados(self):
        """Conta os votos, resolve empates e avança a história."""
        
        if not self.jogo_iniciado:
            return "O jogo ainda não começou!"

        total_jogadores = len(self.jogadores_conectados)
        total_votos = len(self.votos)

        if total_votos < total_jogadores:
            faltam = total_jogadores - total_votos
            return f"Aguardando {faltam} voto(s) restante(s) antes de calcular o resultado."

        # --- Contagem de votos (2 opções fixas) ---
        contagem = {1: 0, 2: 0}
        for v in self.votos.values():
            if v in contagem:
                contagem[v] += 1

        votos1, votos2 = contagem[1], contagem[2]

        # --- Regra de empate (2x2) ---
        if votos1 == 2 and votos2 == 2:
            # Limpa votos e reseta estado de votação
            self.votos.clear()
            for nome in self.jogadores_conectados:
                self.jogadores_conectados[nome]["votou"] = False

            return (
                "Empate detectado (2x2)! Todos devem votar novamente.\n"
                "Escolham entre as mesmas opções."
            )

        # --- Determina o vencedor ---
        if votos1 > votos2:
            proximo_trecho = self.historia[self.trecho_atual]["opcoes"][0]["proximo"]
            vencedor = 1
        else:
            proximo_trecho = self.historia[self.trecho_atual]["opcoes"][1]["proximo"]
            vencedor = 2

        # --- Prepara o próximo trecho (não avança ainda) ---
        self.proximo_trecho_pendente = proximo_trecho
        resultado = f"Opção {vencedor} venceu com {max(votos1, votos2)} voto(s)!\n"
        resultado += "⏳ Aguardando todos clicarem em 'Continuar' para avançar..."

        # Limpa votos e reseta status dos jogadores
        self.votos.clear()
        for nome in self.jogadores_conectados:
            self.jogadores_conectados[nome]["votou"] = False

        return resultado


    
    def obter_status_votacao(self):
        """Retorna o status atual da votação (quantos já votaram)."""
        
        total_jogadores = len(self.jogadores_conectados)
        total_votos = len(self.votos)

        # Caso o jogo ainda não tenha iniciado
        if not self.jogo_iniciado:
            if total_jogadores < 4:
                faltam = 4 - total_jogadores
                return f"Aguardando {faltam} jogador(es) para iniciar o jogo..."
            else:
                return "O jogo ainda não começou oficialmente."

        # Caso ainda não tenha nenhum voto
        if total_votos == 0:
            return "Nenhum voto registrado ainda."

        # Enquanto ainda há votos faltando
        if total_votos < total_jogadores:
            return f"🗳️ {total_votos} de {total_jogadores} jogadores já votaram."

        # Todos já votaram
        if total_votos == total_jogadores:
            return "✅ Todos os jogadores já votaram! Calculando resultado..."


    def avancar_historia(self, proximo_trecho: str):
        if proximo_trecho not in self.historia:
            return "Trecho inválido."

        self.trecho_atual = proximo_trecho
        self.votos.clear() #limpa os votos para o próximo trecho
        return f"Próximo trecho: {self.trecho_atual}"

    def registrar_pronto(self, jogador):
        self.jogadores_prontos.add(jogador)

        # Quando todos clicarem em continuar
        if len(self.jogadores_prontos) == len(self.jogadores_conectados):
            self.jogadores_prontos.clear()

            # Só avança se houver um trecho pendente
            if self.proximo_trecho_pendente:
                resultado = self.avancar_historia(self.proximo_trecho_pendente)
                self.proximo_trecho_pendente = None
                return {"avancar": True, "mensagem": resultado}

            return {"avancar": True, "mensagem": "Avançando para o próximo trecho..."}

        return {"avancar": False, "mensagem": "Aguardando outros jogadores..."}


    
    def enviar_mensagem_chat(self, jogador: str, mensagem: str):
        if not mensagem.strip():
            return "Mensagem vazia não pode ser enviada."

        mensagem = f"{jogador}: {mensagem.strip()}"
        self.chat.append((jogador, mensagem))
        return f"{jogador} disse: {mensagem}"
    
    def obter_chat(self, formatado=True):
        """Retorna o chat formatado para exibição."""
        if not self.chat:
            return "Nenhuma mensagem no chat."

        if formatado:
            texto = "\nChat atual:\n"
            for jogador, mensagem in self.chat:
                texto += f"  {mensagem}\n"
            return texto.strip()

        return self.chat
