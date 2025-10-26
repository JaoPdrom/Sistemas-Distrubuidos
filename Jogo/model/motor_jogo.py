import yaml
import os
import threading
import logging
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger("ServidorRPyC")  # usa o mesmo logger do servidor


# from controller.servidor_controller import log

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class MotorJogo:

    def __init__(self, arquivo_historia: str): #construtor da classe
        self.historia = self.carregar_historia(arquivo_historia) #armazena o arquivo yaml da historia
        self.trecho_atual = None #armazena o trecho atual da historia
        self.votos = {} #dicionario para armazenar os votos dos jogadores
        self.chat = [] #lista para armazenar as mensagens do chat
        self.jogadores_conectados = {}  #dicionario para armazenar os jogadores únicos
        self.jogo_iniciado = False #flag para verificar se o jogo foi iniciado
        self.jogadores_prontos = set()  #quem clicou em "Continuar"
        self.proximo_trecho_pendente = None  #trecho aguardando todos confirmarem
        self.lock = threading.RLock()
        self.avancando = False  #flag para impedir confirmações simultâneas
        self.resultado_calculado = False  #evita calcular mais de uma vez por rodada
        self.ultimo_resultado = None  #salva o texto do último resultado da votação

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

        #detecta se o trecho inicial não tem opções
        trecho = self.historia[self.trecho_atual]
        if not trecho.get("opcoes"):
            self.proximo_trecho_pendente = trecho.get("proximo")  # se houver “proximo” direto
            return {
                "mensagem": f"O jogo começou! Trecho inicial: {self.trecho_atual}",
                "sem_opcoes": True
            }

        return {
            "mensagem": f"O jogo começou! Trecho inicial: {self.trecho_atual}",
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

        # Cabeçalho do trecho
        texto = f"\nTrecho atual: {self.trecho_atual}\n\n"

        # 📖 Formata o texto principal mantendo quebras de linha
        texto_bruto = trecho.get("texto", "")
        if isinstance(texto_bruto, str):
            # Garante que \n do YAML sejam mantidos e remove espaços extras
            texto += texto_bruto.strip() + "\n"
        elif isinstance(texto_bruto, list):
            # Caso o texto venha em lista de parágrafos (formato alternativo)
            texto += "\n\n".join(p.strip() for p in texto_bruto if p.strip()) + "\n"

        # Caso não existam opções, considera fim da história
        if not opcoes_exibir:
            texto += "\nFim da história\n"
            return texto

        # Caso de empate
        if modo_empate:
            texto += "\nEmpate detectado! Vote novamente entre as opções abaixo:\n"
        else:
            texto += "\nOpções disponíveis:\n"

        # Lista as opções numeradas
        for i, opcao in enumerate(opcoes_exibir, start=1):
            texto += f"  {i}. {opcao['texto']}\n"

        return texto

    def registrar_voto(self, jogador, opcao: int):
        with self.lock:
            if not self.jogo_iniciado:
                return "O jogo ainda não começou!"

            trecho = self.obter_trecho_atual(formatado=False)
            opcoes = trecho.get("opcoes", []) if isinstance(trecho, dict) else []
            total_opcoes = len(opcoes)

            if total_opcoes == 0:
                return "Não há opções para votar neste trecho."

            if not (1 <= opcao <= total_opcoes):
                return f"Opção inválida. Escolha entre 1 e {total_opcoes}."

            # registra voto
            self.votos[jogador] = opcao
            if jogador in self.jogadores_conectados:
                self.jogadores_conectados[jogador]["votou"] = True

            total_jogadores = len(self.jogadores_conectados)
            total_votos = len(self.votos)

            log.debug(f"[VOTO] '{jogador}' -> opção {opcao} | "
                      f"{total_votos}/{total_jogadores} votos: {dict(self.votos)}")

            # todos votaram?
            if total_votos == total_jogadores:
                if not self.resultado_calculado:
                    self.resultado_calculado = True
                    resultado = self.calcular_resultados()
                    if not resultado:
                        resultado = "⚠️ Erro interno ao calcular resultado."
                    return resultado
                else:
                    # se já calculado, devolve o último resultado
                    return self.ultimo_resultado or "Resultado já calculado. Aguarde todos clicarem em 'Continuar'."
            else:
                faltam = total_jogadores - total_votos
                return f"{jogador} registrou seu voto. Aguardando {faltam} voto(s)..."


    def calcular_resultados(self):
        """Conta os votos, resolve empate e prepara próximo trecho sem limpar estado prematuramente.
        Armazena o último resultado para garantir que todos os clientes recebam a mesma mensagem.
        """
        with self.lock:
            if not self.jogo_iniciado:
                return "O jogo ainda não começou!"

            total_jogadores = len(self.jogadores_conectados)
            total_votos = len(self.votos)
            if total_votos < total_jogadores:
                faltam = total_jogadores - total_votos
                return f"Aguardando {faltam} voto(s) restante(s) antes de calcular o resultado."

            # descobre quantas opções existem neste trecho
            trecho = self.obter_trecho_atual(formatado=False)
            opcoes = trecho.get("opcoes", []) if isinstance(trecho, dict) else []
            total_opcoes = len(opcoes)
            if total_opcoes == 0:
                return "Erro: trecho atual não possui opções para votação."

            # contagem dinâmica (1..N)
            contagem = Counter(self.votos.values())

            # maior número de votos
            maior = max(contagem.values())
            vencedoras = [idx for idx, c in contagem.items() if c == maior]

            # empate (duas ou mais opções com a mesma contagem)
            if len(vencedoras) != 1:
                log.debug(f"Empate detectado: {dict(contagem)} — reiniciando votação.")
                self.votos.clear()
                for nome in self.jogadores_conectados:
                    self.jogadores_conectados[nome]["votou"] = False
                self.resultado_calculado = False  # libera novo cálculo
                self.ultimo_resultado = "Empate! Votem novamente nas mesmas opções."
                return self.ultimo_resultado

            # opção vencedora
            vencedor = vencedoras[0]  # índice da opção (1..N)

            try:
                proximo_trecho = opcoes[vencedor - 1]["proximo"]
            except (KeyError, IndexError):
                return "Erro ao determinar o próximo trecho. Estrutura da história incorreta."

            # define o próximo trecho e armazena o resultado
            self.proximo_trecho_pendente = proximo_trecho
            self.ultimo_resultado = (
                f"Opção {vencedor} venceu com {maior} voto(s)!\n"
                "Aguardando todos clicarem em 'Continuar' para avançar..."
            )

            log.debug(
                f"[RESULTADO] {self.ultimo_resultado} | pendente: {self.proximo_trecho_pendente}"
            )

            return self.ultimo_resultado

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
            return "Todos os jogadores já votaram! Calculando resultado..."

    def avancar_historia(self, proximo_trecho: str):
        """Thread-safe: avança a história para o próximo trecho e reinicia o ciclo de votação."""
        with self.lock:
            # 1) valida o trecho
            if proximo_trecho not in self.historia:
                return "Trecho inválido."

            # 2) atualiza estado do jogo
            self.trecho_atual = proximo_trecho
            self.votos.clear()
            self.jogadores_prontos.clear()

            for nome in self.jogadores_conectados:
                self.jogadores_conectados[nome]["votou"] = False

            # 3) verifica se o novo trecho tem opções
            trecho = self.historia[self.trecho_atual]
            opcoes = trecho.get("opcoes", [])

            if not opcoes:
                # fim da história
                return f"Fim da história! Último trecho: {self.trecho_atual}"

            # 4) mensagem de sucesso
            return f"➡Avançando para o trecho: {self.trecho_atual}"

    def registrar_pronto(self, jogador):
        """Thread-safe e à prova de duplicação de avanço."""
        with self.lock:
            # Se o jogo estiver em transição, ignora novos cliques
            if self.avancando:
                log.debug(f"[IGNORADO] '{jogador}' tentou confirmar enquanto o jogo avançava.")
                return {"avancar": False, "mensagem": "⏳ O jogo está avançando, aguarde..."}

            # Marca o jogador como pronto
            self.jogadores_prontos.add(jogador)

            total_jogadores = len(self.jogadores_conectados)
            prontos = len(self.jogadores_prontos)

            log.debug(
                f"[CONTINUAR] Jogador '{jogador}' confirmou. "
                f"({prontos}/{total_jogadores}) prontos atualmente: {list(self.jogadores_prontos)}"
            )

            # Revalidação: quem ainda não confirmou
            faltantes = [
                nome for nome in self.jogadores_conectados
                if nome not in self.jogadores_prontos
            ]

            # --- todos confirmaram ---
            if not faltantes and not self.avancando:
                self.avancando = True  #bloqueia novas confirmações
                log.debug("✅ Todos confirmaram. Avançando trecho...")

                self.jogadores_prontos.clear()

                if self.proximo_trecho_pendente:
                    proximo = self.proximo_trecho_pendente
                    self.proximo_trecho_pendente = None

                    # Avança a história (já limpa votos e jogadores_prontos)
                    resultado = self.avancar_historia(proximo)

                    #Reseta as flags da rodada de votação
                    self.resultado_calculado = False
                    self.ultimo_resultado = None

                    self.avancando = False  #libera novas confirmações
                    log.debug(f"🧭 História avançada para: {self.trecho_atual}")
                    return {"avancar": True, "mensagem": resultado}

                self.avancando = False
                log.debug("🔚 Nenhum trecho pendente — rodada encerrada.")
                return {"avancar": True, "mensagem": "Avançando para o próximo trecho..."}

            # --- ainda faltam jogadores ---
            log.debug(f"⏳ Aguardando jogadores restantes: {faltantes}")
            faltam = len(faltantes)
            return {
                "avancar": False,
                "mensagem": f"✅ {jogador} está pronto. Aguardando {faltam} jogador(es)..."
            }

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
