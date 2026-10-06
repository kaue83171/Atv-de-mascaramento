
from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Aplicativo de edicao de imagens e matrizes de pixels RGB.
class EditorImagem:
    # Prepara a janela o menu e os atalhos.
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

    # Cria o menu principal com as operacoes disponiveis.
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
            ("Salvar matriz e PNG editados (8)", self.salvar),
        ]
        for rotulo, comando in acoes:
            opcoes.add_command(label=rotulo, command=comando)
        mascaras = tk.Menu(opcoes, tearoff=False)
        mascaras.add_command(label="Mediana", command=self.aplicar_mediana)
        opcoes.add_cascade(label="Aplicar mascara", menu=mascaras)
        menu.add_cascade(label="Arquivo e edicao", menu=opcoes)
        self.root.config(menu=menu)

    # Atualiza a imagem exibida e o texto com sua resolucao.
    def atualizar(self):
        if self.imagem is None:
            self.painel.configure(image="")
            return
        self.foto = ImageTk.PhotoImage(self.imagem)
        self.painel.configure(image=self.foto)
        self.status.set(f"Resolucao: {self.imagem.width} x {self.imagem.height}")

    # Impede uma operacao quando ainda nao ha imagem carregada.
    def exigir_imagem(self):
        if self.imagem is None:
            messagebox.showinfo("Imagem", "Nenhuma matriz foi carregada. Use 1 ou 2.")
            return False
        return True

    # Abre um PNG, converte seus pixels para RGB e exibe a imagem.
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

    # Le as dimensoes e os valores RGB de um arquivo de texto.
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

    # Grava largura, altura e os valores RGB em formato de matriz.
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

    # Aplica uma rotacao ou espelhamento fornecido pelo menu.
    def transformar(self, operacao):
        if self.exigir_imagem():
            self.imagem = self.imagem.transpose(operacao)
            self.atualizar()

    # Recorta a imagem usando coordenadas de linha e coluna.
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

    # Pede o tamanho da mascara e aplica a mediana em cada pixel.
    def aplicar_mediana(self):
        if not self.exigir_imagem():
            return
        texto = tk.simpledialog.askstring(
            "Tamanho da mascara", "Escolha: 3x3, 5x5, 7x7, 9x9, 15x15 ou 21x21:",
            initialvalue="3x3")
        if texto is None:
            return
        texto = texto.strip().lower().replace("×", "x")
        tamanhos = {"3": 3, "3x3": 3, "5": 5, "5x5": 5, "7": 7, "7x7": 7,
                    "9": 9, "9x9": 9, "15": 15, "15x15": 15, "21": 21, "21x21": 21}
        tamanho = tamanhos.get(texto)
        if tamanho is None:
            messagebox.showerror("Mascara", "Escolha um tamanho: 3x3, 5x5, 7x7, 9x9, 15x15 ou 21x21.")
            return

        # O raio define quantos pixels ao redor do centro entram na mascara.
        raio = tamanho // 2
        largura, altura = self.imagem.size
        # Mantem os pixels originais separados da imagem que sera calculada.
        origem = self.imagem.load()
        resultado = Image.new("RGB", (largura, altura))
        destino = resultado.load()
        # Cada janela quadrada contem tamanho x tamanho valores por canal.
        quantidade = tamanho * tamanho
        for y in range(altura):
            for x in range(largura):
                # Guarda os valores vizinhos de vermelho, verde e azul.
                canais = [[], [], []]
                for dy in range(-raio, raio + 1):
                    # Limita as coordenadas para repetir a borda da imagem.
                    py = min(altura - 1, max(0, y + dy))
                    for dx in range(-raio, raio + 1):
                        px = min(largura - 1, max(0, x + dx))
                        pixel = origem[px, py]
                        for canal in range(3):
                            canais[canal].append(pixel[canal])
                # Ordena os vizinhos de cada canal e escolhe o valor central.
                destino[x, y] = tuple(sorted(canal)[quantidade // 2] for canal in canais)

        self.imagem = resultado
        nome_saida = f"imagem_mediana_{tamanho}x{tamanho}.png"
        try:
            self.imagem.save(nome_saida)
        except OSError as erro:
            messagebox.showerror("Erro", f"Nao foi possivel salvar a imagem filtrada:\n{erro}")
            return
        self.atualizar()
        self.status.set(f"Mascara de mediana {tamanho}x{tamanho} aplicada. Resultado: {nome_saida}")

    # Salva a imagem atual em PNG e sua matriz RGB em texto.
    def salvar(self):
        if self.exigir_imagem():
            self.salvar_matriz("matriz_editada.txt")
            self.imagem.save("imagem_editada.png")
            self.status.set("Salvos: matriz_editada.txt e imagem_editada.png")

    # Associa teclas numericas as mesmas operacoes do menu.
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







