
from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class EditorImagem:
    def __init__(self, root):
        self.root = root
        self.root.title("Imagem PNG e Matriz RGB")
        self.imagem = None
        self.foto = None
        self.painel = tk.Label(root, bg="#333333")
        self.painel.pack(fill="both", expand=True)
        self.status = tk.StringVar(value="Abra um PNG ou carregue matriz.txt")
        tk.Label(root, textvariable=self.status, anchor="w").pack(fill="x")
        self._montar_menu()
        root.bind("<Key>", self.tecla)
        root.geometry("700x600")

    def _montar_menu(self):
        menu = tk.Menu(self.root)
        opcoes = tk.Menu(menu, tearoff=False)
        acoes = [
            ("Abrir imagem PNG (1)", self.abrir_png),
            ("Carregar matriz.txt (2)", self.abrir_matriz),
            ("Rotacionar 90° à direita (3)", lambda: self.transformar(Image.Transpose.ROTATE_270)),
            ("Rotacionar 90° à esquerda (4)", lambda: self.transformar(Image.Transpose.ROTATE_90)),
            ("Espelhar verticalmente (5)", lambda: self.transformar(Image.Transpose.FLIP_TOP_BOTTOM)),
            ("Espelhar horizontalmente (6)", lambda: self.transformar(Image.Transpose.FLIP_LEFT_RIGHT)),
            ("Recortar por coordenadas (7)", self.recortar),
            ("Aplicar mascara de mediana 3x3 (9)", self.aplicar_mediana),
            ("Salvar matriz e PNG editados (8)", self.salvar),
        ]
        for rotulo, comando in acoes:
            opcoes.add_command(label=rotulo, command=comando)
        menu.add_cascade(label="Arquivo e edicao", menu=opcoes)
        self.root.config(menu=menu)

    def atualizar(self):
        if self.imagem is None:
            self.painel.configure(image="")
            return
        self.foto = ImageTk.PhotoImage(self.imagem)
        self.painel.configure(image=self.foto)
        self.status.set(f"Resolucao: {self.imagem.width} x {self.imagem.height}")

    def exigir_imagem(self):
        if self.imagem is None:
            messagebox.showinfo("Imagem", "Nenhuma matriz foi carregada. Use 1 ou 2.")
            return False
        return True

    def abrir_png(self):
        nome = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png"), ("Todos", "*.*")], initialfile="imagem.png")
        if not nome:
            return
        try:
            with Image.open(nome) as original:
                self.imagem = original.convert("RGB")
            self.imagem.save("matriz.txt") if False else None
            self.salvar_matriz(Path("matriz.txt"))
            self.atualizar()
        except (OSError, ValueError) as erro:
            messagebox.showerror("Erro", f"Nao foi possivel ler a imagem:\n{erro}")

    def abrir_matriz(self):
        nome = filedialog.askopenfilename(filetypes=[("Matriz de texto", "*.txt"), ("Todos", "*.*")], initialfile="matriz.txt")
        if not nome:
            return
        try:
            tokens = Path(nome).read_text(encoding="utf-8").split()
            w, h = int(tokens[0]), int(tokens[1])
            if w <= 0 or h <= 0 or len(tokens) != 2 + w*h*3:
                raise ValueError("Dimensoes invalidas ou matriz incompleta.")
            rgb = bytes(max(0, min(255, int(v))) for v in tokens[2:])
            self.imagem = Image.frombytes("RGB", (w, h), rgb)
            self.imagem.save("imagem_nova.png")
            self.atualizar()
        except (OSError, ValueError, IndexError) as erro:
            messagebox.showerror("Erro", f"Nao foi possivel carregar a matriz:\n{erro}")

    def salvar_matriz(self, destino):
        if self.imagem is None:
            return
        w, h = self.imagem.size
        dados = self.imagem.tobytes()
        with Path(destino).open("w", encoding="utf-8") as arquivo:
            arquivo.write(f"{w} {h}\n")
            for y in range(h):
                inicio = y*w*3
                arquivo.write(" ".join(map(str, dados[inicio:inicio+w*3])) + "\n")

    def transformar(self, operacao):
        if self.exigir_imagem():
            self.imagem = self.imagem.transpose(operacao)
            self.atualizar()

    def recortar(self):
        if not self.exigir_imagem():
            return
        texto = tk.simpledialog.askstring("Recortar", "Informe L1C1-L3C4 (linhas e colunas comecam em 1):")
        if texto is None:
            return
        m = re.fullmatch(r"\s*L(\d+)\s*C(\d+)\s*-\s*L(\d+)\s*C(\d+)\s*", texto, re.I)
        if not m:
            messagebox.showerror("Recorte", "Formato invalido. Exemplo: L1C1-L3C4")
            return
        l1, c1, l2, c2 = map(int, m.groups())
        w, h = self.imagem.size
        if l1 < 1 or c1 < 1 or l2 < l1 or c2 < c1 or l2 > h or c2 > w:
            messagebox.showerror("Recorte", f"Coordenadas invalidas. Linhas: 1 a {h}; colunas: 1 a {w}.")
            return
        self.imagem = self.imagem.crop((c1-1, l1-1, c2, l2))
        self.atualizar()

    def aplicar_mediana(self):
        if not self.exigir_imagem():
            return
        largura, altura = self.imagem.size
        origem = self.imagem.load()
        resultado = Image.new("RGB", (largura, altura))
        destino = resultado.load()
        for y in range(altura):
            for x in range(largura):
                vizinhos = [origem[min(largura - 1, max(0, x + dx)), min(altura - 1, max(0, y + dy))]
                            for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
                destino[x, y] = tuple(sorted(pixel[c] for pixel in vizinhos)[4] for c in range(3))
        self.imagem = resultado
        try:
            self.imagem.save("imagem_mediana.png")
        except OSError as erro:
            messagebox.showerror("Erro", f"Nao foi possivel salvar a imagem filtrada:\n{erro}")
        self.atualizar()
        self.status.set("Mascara de mediana aplicada. Resultado: imagem_mediana.png")
    def salvar(self):
        if self.exigir_imagem():
            self.salvar_matriz("matriz_editada.txt")
            self.imagem.save("imagem_editada.png")
            self.status.set("Salvos: matriz_editada.txt e imagem_editada.png")

    def tecla(self, evento):
        mapa = {"1": self.abrir_png, "2": self.abrir_matriz,
                "3": lambda: self.transformar(Image.Transpose.ROTATE_270),
                "4": lambda: self.transformar(Image.Transpose.ROTATE_90),
                "5": lambda: self.transformar(Image.Transpose.FLIP_TOP_BOTTOM),
                "6": lambda: self.transformar(Image.Transpose.FLIP_LEFT_RIGHT),
                "7": self.recortar, "8": self.salvar, "9": self.aplicar_mediana}
        acao = mapa.get(evento.char)
        if acao:
            acao()

if __name__ == "__main__":
    root = tk.Tk()
   
    from tkinter import simpledialog
    tk.simpledialog = simpledialog
    EditorImagem(root)
    root.mainloop()



