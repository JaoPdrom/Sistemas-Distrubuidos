# service/servidor_controller.py
import logging
import os
import rpyc
from model.motor_jogo import MotorJogo

# === Configuração de Logs ===
os.makedirs("logs", exist_ok=True)  # garante que a pasta exista

log_path = os.path.join("logs", "log_servidor.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger("ServidorRPyC")

#instancia global do motor do jogo
motor_global = MotorJogo("historia.yaml")


class JogoService(rpyc.Service):
    #conexao
    def on_connect(self, conn):
        #chamado quando um cliente se conecta ao servidor
        self.conn = conn  #guarda a conexão
        log.info(f"Novo cliente conectado: {conn}")

    def on_disconnect(self, conn):
        #chamado quando o cliente se desconecta.
        jogador = getattr(conn, "jogador", None)
        if jogador:
            log.info(f"Jogador '{jogador}' se desconectou.")
        else:
            log.info("Cliente desconectado (não identificado).")

    # --- Jogadores ---
    def exposed_entrar_no_jogo(self, jogador):
        #registra a entrada de um novo jogador
        conn = self.conn
        conn.jogador = jogador
        log.info(f"Jogador '{jogador}' entrou no jogo.")
        resposta = motor_global.adicionar_jogador(jogador)

        #se o jogo acabou de começar, verifica se o primeiro trecho não tem opções
        if isinstance(resposta, dict):
            return resposta
        return resposta

        return motor_global.adicionar_jogador(jogador)

    def exposed_obter_jogadores(self):
        jogadores = list(motor_global.jogadores_conectados.keys())
        log.info(f"Lista de jogadores conectados: {jogadores}")
        return jogadores

    #história
    def exposed_obter_trecho(self):
        trecho = motor_global.obter_trecho_atual()
        log.info("Trecho atual solicitado pelo cliente.")
        return trecho

    def exposed_obter_opcoes(self):
        trecho = motor_global.obter_trecho_atual(formatado=False)
        if isinstance(trecho, dict):
            opcoes = trecho.get("opcoes", [])
            log.info(f"Opções enviadas: {[o['texto'] for o in opcoes]}")
            return {str(i + 1): o["texto"] for i, o in enumerate(opcoes)}
        log.info("Nenhuma opção disponível para este trecho.")
        return {}

    #votacao
    def exposed_registrar_voto(self, jogador, opcao):
        try:
            log.info(f"Jogador '{jogador}' votou na opção {opcao}.")
            resultado = motor_global.registrar_voto(jogador, int(opcao))
            log.info(f"Resultado parcial da votação: {motor_global.votos}")
            return resultado
        except Exception as e:
            log.error(f"Falha ao registrar voto de {jogador}: {e}")
            return f"Erro ao registrar voto: {e}"

    def exposed_confirmar_continuar(self, nome_jogador):
        #recebe o clique de 'Continuar' do cliente e coordena o avanço do jogo
        try:
            log.info(f"🕹️ Jogador '{nome_jogador}' clicou em 'Continuar'.")
            resposta = motor_global.registrar_pronto(nome_jogador)

            if resposta["avancar"]:
                log.info(f"Todos confirmaram — avançando trecho. ({nome_jogador} foi o último a confirmar)")
                trecho_atual = motor_global.obter_trecho_atual()
                log.debug(f"➡️ Trecho atual após avanço: {trecho_atual}")
                return {
                    "acao": "avancar",
                    "mensagem": resposta["mensagem"],
                    "trecho": trecho_atual
                }
            else:
                log.debug(
                    f"⏳ Jogador '{nome_jogador}' confirmou. "
                    f"Aguardando outros — mensagem: {resposta['mensagem']}"
                )
                return {
                    "acao": "aguardando",
                    "mensagem": resposta["mensagem"]
                }

        except Exception as e:
            log.error(f"Erro ao confirmar 'Continuar' para jogador '{nome_jogador}': {e}")
            return {"acao": "erro", "mensagem": f"Erro ao continuar: {e}"}

    def exposed_obter_status_votacao(self):
        #permite que os clientes consultem o status da votação
        status = motor_global.obter_status_votacao()
        log.info(f"Status da votação solicitado: {status}")
        return status



    # --- Chat ---
    def exposed_enviar_mensagem(self, jogador, mensagem):
        log.info(f"Mensagem de '{jogador}': {mensagem}")
        return motor_global.enviar_mensagem_chat(jogador, mensagem)

    def exposed_obter_chat(self):
        log.info("Chat solicitado por cliente.")
        return motor_global.obter_chat()

    # status do jogo
    def exposed_obter_jogo_iniciado(self):
        status = motor_global.jogo_iniciado
        log.info(f"Estado do jogo solicitado: {'Iniciado' if status else 'Aguardando jogadores'}.")
        return status
