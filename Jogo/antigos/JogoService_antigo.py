# service/servidor_controller.py
import os
import rpyc
from model.motor_jogo import MotorJogo  # importa o motor do jogo

# 🔹 Cria uma única instância global do jogo (compartilhada entre todos os clientes)
motor_global = MotorJogo("historia.yaml")

class JogoService(rpyc.Service):
    def on_connect(self, conn):
        print("[+] Novo cliente conectado.")

    def on_disconnect(self, conn):
        jogador = getattr(conn, 'jogador', None)
        if jogador:
            print(f"[-] Jogador '{jogador}' desconectado.")
        else:
            print("[-] Cliente desconectado nao identificado.")
        print("[-] Cliente desconectado.")

    # --- Jogadores ---
    def exposed_entrar_no_jogo(self, jogador):
        conn = self._conn
        conn.jogador = jogador  # Armazena o nome do jogador na conexão
        print(f"SERVIDOR: [+] Jogador '{jogador}' entrou no jogo.")
        return motor_global.adicionar_jogador(jogador)

    def exposed_obter_jogadores(self):
        jogadores = list(motor_global.jogadores_conectados.keys())
        print(f"SERVIDOR: Jogadores conectados: {jogadores}")
        return jogadores

    # --- História ---
    def exposed_obter_trecho(self):
        trecho = motor_global.obter_trecho_atual()
        print(f"SERVIDOR: Trecho atual: {trecho}")
        return trecho

    def exposed_obter_opcoes(self):
        trecho = motor_global.obter_trecho_atual(formatado=False)
        if isinstance(trecho, dict):
            opcoes = trecho.get("opcoes", [])
            print(f"[Servidor] Opções enviadas: {[o['texto'] for o in opcoes]}")
            return {str(i + 1): o["texto"] for i, o in enumerate(opcoes)}
        print("[Servidor] Nenhuma opção disponível para este trecho.")
        return {}

    # --- Votação ---
    def exposed_registrar_voto(self, jogador, opcao):
        try:
            print(f"[Servidor] Jogador '{jogador}' votou na opção {opcao}.")
            resultado = motor_global.registrar_voto(jogador, int(opcao))
            print(f"[Servidor] Resultado parcial da votação: {motor_global.votos}")
            return resultado
        except Exception as e:
            print(f"[ERRO] Falha ao registrar voto de {jogador}: {e}")
            return f"Erro ao registrar voto: {e}"

    # --- Chat ---
    def exposed_enviar_mensagem(self, jogador, mensagem):
        print(f"[Servidor] Mensagem de '{jogador}': {mensagem}")
        return motor_global.enviar_mensagem_chat(jogador, mensagem)

    def exposed_obter_chat(self):
        print("[Servidor] Chat solicitado por cliente.")
        return motor_global.obter_chat()

    # --- Status do jogo ---
    def exposed_obter_jogo_iniciado(self):
        status = motor_global.jogo_iniciado
        print(f"[Servidor] Estado do jogo solicitado: {'Iniciado' if status else 'Aguardando jogadores'}.")
        return status
