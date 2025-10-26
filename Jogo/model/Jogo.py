import yaml

class Jogo:
    def __init__(self, arq_historia="historia.yaml"):
        self.jogadores = {}   # jogador -> conectado
        self.votos = {}       # jogador -> opção
        self.chat = []
        self.indice_atual = 0

        # Carrega o YAML
        try:
            with open(arq_historia, "r", encoding="utf-8") as f:
                dados = yaml.safe_load(f)
                self.trechos = dados.get("trechos", [])
        except Exception as e:
            print(f"Erro ao carregar YAML: {e}")
            self.trechos = []

        if not self.trechos:
            self.trechos = [{"texto": "História vazia", "opcoes": []}]
        print(f"[DEBUG] Trechos carregados: {len(self.trechos)}")

    # --- História ---
    def obter_trecho(self):
        if self.indice_atual < len(self.trechos):
            trecho = self.trechos[self.indice_atual]
            return trecho.get("texto", "Trecho sem texto")
        return "Fim da história!"

    # --- Opções do trecho atual ---
    def obter_opcoes(self):
        if self.indice_atual < len(self.trechos):
            opcoes = self.trechos[self.indice_atual].get("opcoes", [])

            # Se for dicionário numerado
            if isinstance(opcoes, dict):
                return {str(k): str(v) for k, v in opcoes.items()}

            # Se for lista de dicionários
            elif isinstance(opcoes, list):
                resultado = {}
                for i, o in enumerate(opcoes):
                    if isinstance(o, dict) and "texto" in o:
                        resultado[str(i+1)] = o["texto"]
                return resultado
        return {}

    # --- jogadores ---
    def entrar_no_jogo(self, jogador):
        if jogador not in self.jogadores:
            self.jogadores[jogador] = True
        return f"{jogador} entrou no jogo!"

    def obter_jogadores(self):
        return list(self.jogadores.keys())

    # --- Votação / Avançar trecho ---
    def registrar_voto(self, jogador, opcao):
        if jogador not in self.jogadores:
            return "Jogador não registrado!"
        if jogador in self.votos:
            return f"{jogador} já votou nesta rodada."

        self.votos[jogador] = opcao

        if len(self.votos) < len(self.jogadores):
            return f"{jogador} votou na opção {opcao}. Aguardando os demais jogadores..."
        else:
            return self.calcular_resultado()

    def calcular_resultado(self):
        contagem = {}
        for voto in self.votos.values():
            if voto in contagem:
                contagem[voto] += 1
            else:
                contagem[voto] = 1

        # Determina vencedor
        max_votos = 0
        for c in contagem.values():
            if c > max_votos:
                max_votos = c

        vencedores = [chave for chave, c in contagem.items() if c == max_votos]

        if len(vencedores) == 1:
            escolhido = vencedores[0]
            self.indice_atual += 1
            resultado = f"Opção {escolhido} venceu! Avançando para o próximo trecho..."
        else:
            resultado = "Empate! Votação será repetida."

        self.votos = {}
        return resultado

    # --- Chat ---
    def enviar_mensagem(self, jogador, msg):
        if jogador not in self.jogadores:
            return "Jogador não registrado!"
        self.chat.append(f"{jogador}: {msg}")
        return "Mensagem enviada."

    def obter_chat(self):
        return "\n".join(self.chat)
