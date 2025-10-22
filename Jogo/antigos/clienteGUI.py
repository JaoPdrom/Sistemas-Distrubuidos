import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import rpyc
import time

class ClienteGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Jogo Cooperativo")

        try:
            self.conn = rpyc.connect("localhost", 18812)
            self.servico = self.conn.root
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível conectar ao servidor: {e}")
            self.master.destroy()
            return

        self.jogador = simpledialog.askstring("Nome", "Digite seu nome de jogador:")
        if not self.jogador:
            self.master.destroy()
            return

        msg = self.servico.entrar_no_jogo(self.jogador)
        messagebox.showinfo("Bem-vindo", msg)

        # --- Widgets ---
        self.texto_historia = tk.Text(master, height=10, width=50, state="disabled")
        self.texto_historia.pack(pady=5)

        self.frame_opcoes = tk.Frame(master)
        self.frame_opcoes.pack(pady=5)

        self.chat_texto = tk.Text(master, height=10, width=50, state="disabled")
        self.chat_texto.pack(pady=5)

        self.entry_msg = tk.Entry(master, width=40)
        self.entry_msg.pack(side="left", padx=5)
        self.botao_enviar = tk.Button(master, text="Enviar", command=self.enviar_chat)
        self.botao_enviar.pack(side="left")

        threading.Thread(target=self.atualizar_loop, daemon=True).start()

    def atualizar_loop(self):
        while True:
            try:
                self.atualizar_interface()
            except Exception as e:
                print(f"Erro ao atualizar interface: {e}")
            time.sleep(1)

    def atualizar_interface(self):
        # História
        trecho = self.servico.obter_trecho()
        self.texto_historia.config(state="normal")
        self.texto_historia.delete(1.0, tk.END)
        if isinstance(trecho, dict):
            texto = trecho.get("texto", "")
        else:
            texto = trecho
        self.texto_historia.insert(tk.END, texto)
        self.texto_historia.config(state="disabled")

        # Chat
        chat = self.servico.obter_chat()
        self.chat_texto.config(state="normal")
        self.chat_texto.delete(1.0, tk.END)
        self.chat_texto.insert(tk.END, chat)
        self.chat_texto.config(state="disabled")

        # Botões de voto
        for widget in self.frame_opcoes.winfo_children():
            widget.destroy()

        opcoes = dict(self.servico.obter_opcoes())  # converte proxy RPyC
        for chave, descricao in opcoes.items():
            btn = tk.Button(self.frame_opcoes, text=f"{chave}: {descricao}",
                            command=lambda o=chave: self.votar(o))
            btn.pack(side="left", padx=5)

    def votar(self, opcao):
        try:
            resultado = self.servico.registrar_voto(self.jogador, opcao)
            messagebox.showinfo("Votação", resultado)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível registrar voto: {e}")

    def enviar_chat(self):
        msg = self.entry_msg.get()
        if msg:
            try:
                self.servico.enviar_mensagem(self.jogador, msg)
                self.entry_msg.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível enviar mensagem: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClienteGUI(root)
    root.mainloop()
