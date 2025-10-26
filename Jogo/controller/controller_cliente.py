# controller/controller_cliente.py
import tkinter as tk
from tkinter import messagebox
import threading
import time
import rpyc

#importa telas da view
from view.prejogo.nome_jogador import Toplevel1 as TelaNome
from view.prejogo.aguardando_jogadores import Toplevel1 as TelaAguardando
from view.jogo_interface import Jogo as TelaJogo


class ClienteApp:
    #controller principal do cliente, gerencia telas e comunicação RPyC

    def __init__(self):
        #cria a janela raiz do Tkinter e a esconde imediatamente
        self.root = tk.Tk()
        self.root.withdraw()

        self.conn = None
        self.servico = None
        self.jogador = None

        self.conectar_servidor()
        if self.servico:
            self.mostrar_tela_nome()
            self.root.mainloop()


    #conexao com o servidor
    def conectar_servidor(self):
        try:
            self.conn = rpyc.connect("localhost", 18812)
            self.servico = self.conn.root
            print("[Cliente] Conectado ao servidor RPyC.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao conectar no servidor:\n{e}")
            self.root.destroy()


    #tela de nome do jogador
    def mostrar_tela_nome(self):
        self.janela_nome = tk.Toplevel(self.root)
        self.tela_nome = TelaNome(self.janela_nome)
        self.janela_nome.title("Escolha seu nome")
        self.tela_nome.TBtnEntrar.config(command=self.confirmar_nome)

    def confirmar_nome(self):
        nome = self.tela_nome.TNomeJogador.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Por favor, insira um nome válido.")
            return

        self.jogador = nome
        resposta = self.servico.entrar_no_jogo(self.jogador)
        messagebox.showinfo("Conectado", resposta)
        self.janela_nome.destroy()
        self.mostrar_tela_aguardando()



    #tela de espera
    def mostrar_tela_aguardando(self):
        self.janela_aguardando = tk.Toplevel(self.root)
        self.tela_aguardando = TelaAguardando(self.janela_aguardando)
        self.janela_aguardando.title("Aguardando jogadores...")

        self.label_status = tk.Label(
            self.tela_aguardando.Frame1,
            text="Jogadores conectados: 1/4",
            background="#d9d9d9",
            font=("Arial", 10)
        )
        self.label_status.place(relx=0.18, rely=0.7)

        threading.Thread(target=self.loop_aguardando, daemon=True).start()

    def loop_aguardando(self):
        #Atualiza a tela de espera até que o jogo comece
        while True:
            try:
                jogadores = self.servico.obter_jogadores()
                total = len(jogadores)
                self.label_status.config(text=f"Jogadores conectados: {total}/4")

                #verifica com o servidor se o jogo ja começou (>= 4 jogadores)
                jogo_iniciado = self.servico.obter_jogo_iniciado()
                if jogo_iniciado:
                    print("[Cliente] Jogo iniciado!")
                    #usa after() para garantir que a GUI feche no thread correto
                    self.janela_aguardando.after(0, self.janela_aguardando.destroy)
                    self.root.after(200, self.iniciar_jogo)
                    break

            except Exception as e:
                print("Erro ao verificar jogadores:", e)
                break

            time.sleep(1)


    #tela do jogo principal
    def iniciar_jogo(self):
        #inicializa a tela principal do jogo e configura os componentes
        self.janela_jogo = tk.Toplevel(self.root)
        self.janela_jogo.protocol('WM_DELETE_WINDOW', self.root.destroy)
        self.tela_jogo = TelaJogo(self.janela_jogo)
        self.janela_jogo.title(f"Jogo - {self.jogador}")

        #ativa os boteos da interface
        self.tela_jogo.btnChatEnviarMensagem.config(command=self.enviar_chat)
        self.tela_jogo.btnVotOpcao1.config(command=lambda: self.votar(1))
        self.tela_jogo.btnVotOpcao2.config(command=lambda: self.votar(2))
        self.tela_jogo.btnVotOpcao3.config(command=lambda: self.votar(3))
        self.tela_jogo.btnContinuar.config(command=self.on_continuar)

        #verifica se o primeiro trecho tem opções disponíveis
        try:
            opcoes = self.servico.obter_opcoes()
            if not opcoes:
                #nenhuma opção: é introdução entao habilita botão Continuar
                self.tela_jogo.btnContinuar.config(state="normal")
                self.mostrar_status_votacao("📖 Introdução carregada — clique em 'Continuar' para começar.")
            else:
                #se tem opções: desabilita até o fim da votação
                self.tela_jogo.btnContinuar.config(state="disabled")
        except Exception as e:
            print(f"Erro ao verificar opções iniciais: {e}")
            self.tela_jogo.btnContinuar.config(state="disabled")

        #inicializa a primeira atualização da interface
        self.loop_atualizacao()  #as proximas execucoes serao agendadas por after()


    def loop_atualizacao(self):
        try:
            #se a janela do jogo foi fechada, para o loop
            if not getattr(self, "janela_jogo", None) or not self.janela_jogo.winfo_exists():
                return

            #executa as atualizacoes apenas se a root ainda existir
            if getattr(self, "root", None) and self.root.winfo_exists():
                self.atualizar_historia()
                self.atualizar_chat()
                self.atualizar_opcoes()

                #agenda a proxima execucao apenas se o root ainda existir
                self.root.after(1000, self.loop_atualizacao)

        except Exception as e:
            #se der erro porque a janela fechou, ignora silenciosamente
            if "invalid command name" not in str(e):
                print("Erro ao atualizar interface:", e)



    def atualizar_historia(self):
        trecho = self.servico.obter_trecho()
        self.tela_jogo.STHistoria.config(state="normal")
        self.tela_jogo.STHistoria.delete("1.0", tk.END)
        self.tela_jogo.STHistoria.insert(tk.END, trecho)
        self.tela_jogo.STHistoria.config(state="disabled")


    def atualizar_chat(self):
        chat = self.servico.obter_chat()
        self.tela_jogo.STChat.config(state="normal")
        self.tela_jogo.STChat.delete("1.0", tk.END)
        self.tela_jogo.STChat.insert(tk.END, chat)
        self.tela_jogo.STChat.config(state="disabled")


    def atualizar_opcoes(self):
        opcoes = self.servico.obter_opcoes()
        botoes = [
            self.tela_jogo.btnVotOpcao1,
            self.tela_jogo.btnVotOpcao2,
            self.tela_jogo.btnVotOpcao3
        ]

        for i, botao in enumerate(botoes, start=1):
            if str(i) in opcoes:
                botao.config(text=f"{i}: {opcoes[str(i)]}", state="normal")
            else:
                botao.config(text=f"Opção {i}", state="disabled")

    def votar(self, opcao):
        #envia o voto do jogador e mostra o progresso na área de status
        try:
            resultado = self.servico.registrar_voto(self.jogador, str(opcao))
            self.mostrar_status_votacao(resultado)

            #se o resultado indicar que todos ja votaram, habilita o botao Continuar
            if (
                "venceu" in resultado
                or "Aguardando todos clicarem" in resultado
                or "Todos os jogadores já votaram" in resultado
            ):
                self.tela_jogo.btnContinuar.config(state="normal")

        except Exception as e:
            self.mostrar_status_votacao(f"Erro ao votar: {e}")


    def on_continuar(self):
        #confirma que o jogador está pronto para avançar
        try:
            resposta = self.servico.confirmar_continuar(self.jogador)
            self.mostrar_status_votacao(resposta["mensagem"])

            if resposta["acao"] == "avancar":
                #limpa o status de votação anterior
                self.tela_jogo.STStatusVotacao.config(state="normal")
                self.tela_jogo.STStatusVotacao.delete("1.0", tk.END)
                self.tela_jogo.STStatusVotacao.config(state="disabled")

                #atualiza o texto da história
                self.atualizar_historia()

                #desativa o botão até a próxima votação
                self.tela_jogo.btnContinuar.config(state="disabled")

        except Exception as e:
            self.mostrar_status_votacao(f"Erro ao continuar: {e}")



    def mostrar_status_votacao(self, msg):
        #adiciona mensagens na area de status da votacao
        self.tela_jogo.STStatusVotacao.config(state="normal")
        self.tela_jogo.STStatusVotacao.insert(tk.END, msg + "\n")
        self.tela_jogo.STStatusVotacao.see(tk.END)
        self.tela_jogo.STStatusVotacao.config(state="disabled")


    def enviar_chat(self):
        msg = self.tela_jogo.TEntryChat.get().strip()
        if not msg:
            return
        try:
            self.servico.enviar_mensagem(self.jogador, msg)
            self.tela_jogo.TEntryChat.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível enviar mensagem: {e}")

