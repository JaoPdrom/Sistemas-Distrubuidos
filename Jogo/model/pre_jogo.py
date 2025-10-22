# pre_jogo.py
import os
import sys
import tkinter as tk
from tkinter import messagebox
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'view', 'prejogo'))

from view.prejogo.nome_jogador import Toplevel1 as TelaNome
from view.prejogo.aguardando_jogadores import Toplevel1 as TelaAguardando



class PreJogo:
    def __init__(self):
        """Inicializa a tela de nome do jogador."""
        self.root = tk.Tk()
        self.root.withdraw()  # esconde a janela raiz temporariamente

        # Cria a tela de nome
        self.janela_nome = tk.Toplevel(self.root)
        self.tela_nome = TelaNome(self.janela_nome)
        self.janela_nome.title("Escolha seu nome")

        # Conecta o botão "Entrar"
        self.tela_nome.TBtnEntrar.configure(command=self.confirmar_nome)

        # Variáveis de estado
        self.nome_jogador = None
        self.jogadores_conectados = 1  # começa com 1 só para simular

        self.root.mainloop()

    def confirmar_nome(self):
        """Obtém o nome digitado e avança para a tela de espera."""
        nome = self.tela_nome.TNomeJogador.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Por favor, insira um nome.")
            return

        self.nome_jogador = nome
        self.janela_nome.destroy()
        self.mostrar_tela_aguardando()

    def mostrar_tela_aguardando(self):
        """Abre a tela de espera enquanto 'aguarda' os outros jogadores."""
        self.janela_aguardando = tk.Toplevel(self.root)
        self.tela_aguardando = TelaAguardando(self.janela_aguardando)
        self.janela_aguardando.title("Aguardando jogadores...")

        # Adiciona um label dinâmico abaixo da mensagem original
        self.label_status = tk.Label(
            self.tela_aguardando.Frame1,
            text=f"Jogadores conectados: {self.jogadores_conectados}/4",
            background="#d9d9d9",
            font=("Arial", 10)
        )
        self.label_status.place(relx=0.2, rely=0.7)

        # Inicia uma thread simulando entrada de novos jogadores
        threading.Thread(target=self.simular_entrada_jogadores, daemon=True).start()

    def simular_entrada_jogadores(self):
        """Simula a chegada de outros jogadores a cada 2 segundos."""
        while self.jogadores_conectados < 4:
            time.sleep(2)
            self.jogadores_conectados += 1
            self.label_status.config(
                text=f"Jogadores conectados: {self.jogadores_conectados}/4"
            )

        # Quando atinge 4, mostra mensagem e inicia o jogo
        messagebox.showinfo("Pronto!", "Todos os jogadores conectados! Iniciando jogo...")
        self.iniciar_jogo()

    def iniciar_jogo(self):
        """Fecha a tela de espera e inicia a próxima fase (aqui apenas uma mensagem)."""
        self.janela_aguardando.destroy()
        label = tk.Label(self.root, text=f"Bem-vindo ao jogo, {self.nome_jogador}!", font=("Arial", 14))
        label.pack(pady=50)
        self.root.deiconify()


if __name__ == "__main__":
    PreJogo()
