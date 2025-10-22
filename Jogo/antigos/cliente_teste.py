import tkinter as tk
import rpyc
import interface


class ClienteGUI:
    def __init__(self, host="localhost", port=18812):
        # 🔌 Conecta ao servidor RPyC
        try:
            self.conn = rpyc.connect(host, port)
            print("✅ Conectado ao servidor RPyC.")
        except Exception as e:
            print("❌ Erro ao conectar ao servidor:", e)
            self.conn = None

        # 🪟 Inicializa a janela da interface
        self.root = tk.Tk()
        self.app = interface.Toplevel1(self.root)
        self.root.title("Jogo de Aventura Cooperativo")

        # Inicializa com o trecho atual da história
        self.atualizar_historia()

        # Atualiza automaticamente a cada 2 segundos (pode ajustar)
        self.root.after(2000, self.atualizar_historia)

        self.root.mainloop()

    def atualizar_historia(self):
        """Busca o trecho atual do servidor e mostra na GUI."""
        if not self.conn:
            self.app.Scrolledtext1.delete("1.0", "end")
            self.app.Scrolledtext1.insert("end", "Erro: não conectado ao servidor.")
            return

        try:
            trecho = self.conn.root.obter_trecho()  # 🔁 Chama o método remoto
            self.app.Scrolledtext1.delete("1.0", "end")
            self.app.Scrolledtext1.insert("end", trecho)
        except Exception as e:
            self.app.Scrolledtext1.delete("1.0", "end")
            self.app.Scrolledtext1.insert("end", f"Erro ao obter trecho: {e}")

        # Reagenda a atualização (loop contínuo)
        self.root.after(2000, self.atualizar_historia)


if __name__ == "__main__":
    ClienteGUI()
