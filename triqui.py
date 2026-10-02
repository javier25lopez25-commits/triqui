"""Triqui (tres en raya): jugador vs. máquina, con interfaz gráfica (tkinter)."""
import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

ARCHIVO_PUNTOS = Path(__file__).with_name("puntajes.json")
INTENTOS = 2
LINEAS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
NIVELES = {  # nombre: (puntos por victoria, color)
    "Fácil": (10, "#2ECC71"),
    "Medio": (20, "#F39C12"),
    "Difícil": (30, "#E74C3C"),
}
PUNTOS_EMPATE = 5

FONDO = "#1B1464"
TABLERO = "#341F97"
CASILLA = "#FFEAA7"
COLOR_SIMBOLO = {"X": "#FF3F81", "O": "#00B8D4"}


def ganador(t):
    for a, b, c in LINEAS:
        if t[a] and t[a] == t[b] == t[c]:
            return t[a], (a, b, c)
    return None, None


def libres(t):
    return [i for i, v in enumerate(t) if not v]


def jugada_ganadora(t, simbolo):
    for i in libres(t):
        t[i] = simbolo
        g, _ = ganador(t)
        t[i] = ""
        if g:
            return i
    return None


def minimax(t, turno, yo, rival):
    g, _ = ganador(t)
    if g:
        return 1 if g == yo else -1
    if not libres(t):
        return 0
    puntajes = []
    for i in libres(t):
        t[i] = turno
        puntajes.append(minimax(t, rival if turno == yo else yo, yo, rival))
        t[i] = ""
    return max(puntajes) if turno == yo else min(puntajes)


def jugada_maquina(t, nivel, yo, rival):
    opciones = libres(t)
    if nivel == "Fácil":
        return random.choice(opciones)
    if nivel == "Medio":
        for simbolo in (yo, rival):  # primero ganar, luego bloquear
            i = jugada_ganadora(t, simbolo)
            if i is not None:
                return i
        return 4 if 4 in opciones else random.choice(opciones)
    if len(opciones) == 9:  # apertura: esquina o centro (óptimas), evita recorrer todo el árbol
        return random.choice([0, 2, 4, 6, 8])
    mejor, mejores = -2, []
    for i in opciones:
        t[i] = yo
        v = minimax(t, rival, yo, rival)
        t[i] = ""
        if v > mejor:
            mejor, mejores = v, [i]
        elif v == mejor:
            mejores.append(i)
    return random.choice(mejores)


def cargar_puntajes():
    try:
        return json.loads(ARCHIVO_PUNTOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def guardar_puntajes(datos):
    ARCHIVO_PUNTOS.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Triqui")
        self.configure(bg=FONDO)
        self.resizable(False, False)
        self.puntajes = cargar_puntajes()
        self.pendientes = []
        self.var_usuario = tk.StringVar()
        self.var_nivel = tk.StringVar(value="Fácil")
        self.var_simbolo = tk.StringVar(value="X")
        self.pantalla_inicio()

    def limpiar(self):
        for id_ in self.pendientes:
            self.after_cancel(id_)
        self.pendientes = []
        for w in self.winfo_children():
            w.destroy()

    def etiqueta(self, texto, tam=12, color="white", **kw):
        return tk.Label(self, text=texto, bg=FONDO, fg=color, font=("Segoe UI", tam, "bold"), **kw)

    # ---------- Pantalla de inicio ----------
    def pantalla_inicio(self):
        self.limpiar()
        self.etiqueta("TRIQUI", 36, "#FFD32A").pack(padx=60, pady=(20, 0))
        self.etiqueta("Jugador vs. Máquina", 12, "#7EFFF5").pack()

        self.etiqueta("Usuario:").pack(pady=(18, 4))
        tk.Entry(self, textvariable=self.var_usuario, font=("Segoe UI", 14), justify="center",
                 width=18, bg=CASILLA, relief="flat").pack()

        self.etiqueta("Nivel de dificultad:").pack(pady=(18, 4))
        marco = tk.Frame(self, bg=FONDO)
        marco.pack()
        for nivel, (pts, color) in NIVELES.items():
            tk.Radiobutton(marco, text=f"{nivel} (+{pts})", variable=self.var_nivel, value=nivel,
                           indicatoron=False, bg=color, fg="white", selectcolor="#6C5CE7",
                           font=("Segoe UI", 11, "bold"), width=13, relief="flat", pady=6
                           ).pack(side="left", padx=4)

        self.etiqueta("Tu símbolo:").pack(pady=(18, 4))
        marco = tk.Frame(self, bg=FONDO)
        marco.pack()
        for s in ("X", "O"):
            tk.Radiobutton(marco, text=s, variable=self.var_simbolo, value=s, indicatoron=False,
                           bg=COLOR_SIMBOLO[s], fg="white", selectcolor="#6C5CE7",
                           font=("Segoe UI", 16, "bold"), width=4, relief="flat"
                           ).pack(side="left", padx=6)

        tk.Button(self, text="¡JUGAR!", command=self.iniciar, bg="#FFD32A", fg=FONDO,
                  font=("Segoe UI", 16, "bold"), relief="flat", padx=20, pady=6
                  ).pack(pady=(22, 6))
        tk.Button(self, text="Ver ranking", command=self.ver_ranking, bg=TABLERO, fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat").pack(pady=(0, 20))

    def ver_ranking(self):
        if not self.puntajes:
            messagebox.showinfo("Ranking", "Aún no hay puntajes.")
            return
        orden = sorted(self.puntajes.items(), key=lambda kv: kv[1], reverse=True)[:10]
        messagebox.showinfo("Ranking", "\n".join(f"{i}. {u}: {p} pts" for i, (u, p) in enumerate(orden, 1)))

    # ---------- Partida ----------
    def iniciar(self):
        usuario = self.var_usuario.get().strip()
        if not usuario:
            messagebox.showwarning("Usuario", "Escribe un nombre de usuario para jugar.")
            return
        self.usuario = usuario
        self.nivel = self.var_nivel.get()
        self.humano = self.var_simbolo.get()
        self.maquina = "O" if self.humano == "X" else "X"
        self.puntos_sesion = 0
        self.intento = 0
        self.puntajes.setdefault(usuario, 0)
        self.pantalla_juego()
        self.nuevo_intento()

    def pantalla_juego(self):
        self.limpiar()
        self.lbl_info = self.etiqueta("", 13, "#FFD32A")
        self.lbl_info.pack(pady=(14, 0), padx=20)
        self.lbl_puntos = self.etiqueta("", 11, "#7EFFF5")
        self.lbl_puntos.pack()
        self.lbl_estado = self.etiqueta("", 14)
        self.lbl_estado.pack(pady=8)

        marco = tk.Frame(self, bg=TABLERO, padx=6, pady=6)
        marco.pack(padx=20)
        self.botones = []
        for i in range(9):
            b = tk.Button(marco, text="", width=4, height=1, font=("Segoe UI", 36, "bold"),
                          bg=CASILLA, relief="flat", command=lambda i=i: self.click(i))
            b.grid(row=i // 3, column=i % 3, padx=4, pady=4)
            self.botones.append(b)

        tk.Button(self, text="Salir al menú", command=self.pantalla_inicio, bg=TABLERO, fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat").pack(pady=14)

    def actualizar_puntos(self):
        self.lbl_info.config(text=f"{self.usuario} · {self.nivel} · Intento {self.intento} de {INTENTOS}")
        self.lbl_puntos.config(text=f"Puntos de esta sesión: {self.puntos_sesion}   |   "
                                    f"Total: {self.puntajes[self.usuario]}")

    def nuevo_intento(self):
        self.intento += 1
        self.tablero = [""] * 9
        self.activo = True
        for b in self.botones:
            b.config(text="", bg=CASILLA, state="normal")
        self.actualizar_puntos()
        # X siempre empieza; el jugador y la máquina se alternan según el símbolo elegido.
        if self.maquina == "X":
            self.turno_maquina()
        else:
            self.lbl_estado.config(text="Tu turno")

    def poner(self, i, simbolo):
        self.tablero[i] = simbolo
        self.botones[i].config(text=simbolo, fg=COLOR_SIMBOLO[simbolo], state="disabled",
                               disabledforeground=COLOR_SIMBOLO[simbolo])

    def click(self, i):
        if not self.activo or self.tablero[i]:
            return
        self.poner(i, self.humano)
        if not self.revisar():
            self.activo = False
            self.lbl_estado.config(text="La máquina piensa…")
            self.pendientes.append(self.after(450, self.turno_maquina))

    def turno_maquina(self):
        self.activo = False
        i = jugada_maquina(self.tablero, self.nivel, self.maquina, self.humano)
        self.poner(i, self.maquina)
        if not self.revisar():
            self.activo = True
            self.lbl_estado.config(text="Tu turno")

    def revisar(self):
        """Devuelve True si el intento terminó."""
        g, linea = ganador(self.tablero)
        if not g and libres(self.tablero):
            return False
        self.activo = False
        if g:
            for i in linea:
                self.botones[i].config(bg="#55EFC4")
        if g == self.humano:
            pts = NIVELES[self.nivel][0]
            texto = f"¡Ganaste! +{pts} puntos"
        elif g:
            pts, texto = 0, "Ganó la máquina. 0 puntos"
        else:
            pts, texto = PUNTOS_EMPATE, f"¡Empate! +{PUNTOS_EMPATE} puntos"
        self.puntos_sesion += pts
        self.puntajes[self.usuario] += pts
        guardar_puntajes(self.puntajes)
        self.actualizar_puntos()
        self.lbl_estado.config(text=texto)
        self.pendientes.append(self.after(1400, self.siguiente))
        return True

    def siguiente(self):
        if self.intento < INTENTOS:
            self.nuevo_intento()
            return
        otra = messagebox.askyesno(
            "Fin del juego",
            f"Terminaron los {INTENTOS} intentos.\n"
            f"{self.usuario}, sumaste {self.puntos_sesion} puntos (total {self.puntajes[self.usuario]}).\n\n"
            "¿Jugar de nuevo?")
        if otra:
            self.pantalla_inicio()
        else:
            self.destroy()


if __name__ == "__main__":
    App().mainloop()
