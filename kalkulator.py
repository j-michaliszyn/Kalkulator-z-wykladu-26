"""Kalkulator BIN/DEC. Uruchom: python3 kalkulator.py"""

from fractions import Fraction
from operator import add, mul, sub, truediv
import tkinter as tk
from tkinter import font


BASE_NAME = {2: "BIN", 10: "DEC"}
OPERATIONS = {"+": add, "−": sub, "×": mul, "÷": truediv}


def read_number(raw, base):
    whole, _, tail = raw.lstrip("-").partition(",")
    value = Fraction(int(whole + tail, base), base ** len(tail))
    return -value if raw.startswith("-") else value


def notation(value, base, places=24):
    """Long division; an ellipsis marks digits beyond the display limit."""
    n, remainder = divmod(abs(value.numerator), value.denominator)
    result = ("−" if value < 0 else "") + (format(n, "b") if base == 2 else str(n))
    if remainder:
        digits = []
        while remainder and len(digits) < places:
            digit, remainder = divmod(remainder * base, value.denominator)
            digits.append(str(digit))
        result += "," + "".join(digits) + ("…" if remainder else "")
    return result


class Calculator:
    """A pocket calculator. Each operator finishes the preceding operation."""

    def __init__(self):
        self.base = 10
        self.clear()

    def clear(self):
        self.value = Fraction(0)
        self.raw = None
        self.left = None
        self.op = None
        self.waiting = False
        self.last = None
        self.error = ""

    def edit(self, key):
        if key.isdigit() and int(key) >= self.base:
            return
        if self.error:
            self.clear()
        raw = self.raw or "0"
        if key == "back":
            if self.raw is None:
                return
            raw = raw[:-1]
            if raw in ("", "-"):
                raw = "0"
        elif key == ",":
            if "," in raw:
                return
            raw += ","
        elif len(raw.lstrip("-").replace(",", "")) < 160:
            raw = (raw[:-1] if raw in ("0", "-0") else raw) + key
        else:
            return
        self.raw = raw
        self.value = read_number(raw, self.base)
        self.waiting = False
        self.last = None

    def sign(self):
        if self.error:
            self.clear()
        if self.waiting:
            self.raw, self.value = "0", Fraction(0)
        if self.raw is not None:
            self.raw = self.raw[1:] if self.raw.startswith("-") else "-" + self.raw
        elif self.value == 0:
            self.raw = "-0"
        self.value = -self.value
        self.waiting = False
        self.last = None

    def switch(self, base):
        if self.base != base:
            self.base = base
            # Keep the exact value even when its new expansion is infinite.
            self.raw = None

    def operate(self, key):
        if self.error:
            return
        if self.op and not self.waiting:
            left, op, right = self.left, self.op, self.value
            if op == "÷" and right == 0:
                self.clear()
                self.error = "Dzielenie przez zero"
                return
            result = OPERATIONS[op](left, right)
            if max(result.numerator.bit_length(), result.denominator.bit_length()) > 4096:
                self.clear()
                self.error = "Wynik zbyt duży"
                return
            self.value = result
            self.last = (left, op, right)
        elif key == "=" and self.waiting:
            return
        self.raw = None
        if key == "=":
            self.left = self.op = None
            self.waiting = False
        else:
            self.left, self.op = self.value, key
            self.last = None
            self.waiting = True

    def equation(self):
        show = lambda n: notation(n, self.base)
        if self.op:
            return f"{show(self.left)} {self.op}"
        if self.last:
            left, op, right = self.last
            return f"{show(left)} {op} {show(right)} ="
        return ""

PAPER, INK, DISPLAY = "#44f2eb", "#aa2f2d", "#773e39"
MINT, SOFT, DIM = "#44edd0", "#44e7de", "#44c8bc"


class Window:
    def __init__(self, root):
        self.root = root
        self.calc = Calculator()
        root.title("Kalkulator · BIN / DEC")
        root.configure(bg=PAPER)
        root.geometry("424x572")
        root.minsize(340, 470)
        families = set(font.families(root))
        self.sans = next((f for f in ("Inter", "Segoe UI", "Helvetica", "DejaVu Sans")
                          if f in families), "TkDefaultFont")
        self.mono = next((f for f in ("IBM Plex Mono", "Consolas", "Menlo", "DejaVu Sans Mono")
                          if f in families), "TkFixedFont")
        frame = tk.Frame(root, bg=PAPER, padx=18, pady=16)
        frame.pack(fill="both", expand=True)

        bar = tk.Frame(frame, bg=PAPER)
        bar.pack(fill="x", pady=(0, 14))
        tk.Label(bar, text="Kalkulator", bg=PAPER, fg=INK,
                 font=(self.sans, 17, "bold")).pack(side="left")
        modes = tk.Frame(bar, bg=SOFT, padx=3, pady=3)
        modes.pack(side="right")
        self.tabs = {}
        for base in (10, 2):
            button = self.button(modes, BASE_NAME[base],
                                 lambda b=base: self.change_base(b), SOFT, INK, 10)
            button.pack(side="left", ipadx=6, ipady=3)
            self.tabs[base] = button

        screen = tk.Frame(frame, bg=DISPLAY, padx=16, pady=12)
        screen.pack(fill="x")
        self.caption = tk.Label(screen, anchor="w", bg=DISPLAY, fg=MINT,
                                font=(self.sans, 10, "bold"))
        self.caption.pack(fill="x")
        self.history = self.readout(screen, DIM, 11)
        self.number = self.readout(screen, "#ffffff", 27)
        tk.Frame(screen, bg="#3b5f56", height=1).pack(fill="x", pady=(7, 6))
        second = tk.Frame(screen, bg=DISPLAY)
        second.pack(fill="x")
        self.alt_name = tk.Label(second, bg=DISPLAY, fg=DIM, font=(self.mono, 10, "bold"))
        self.alt_name.pack(side="left", padx=(0, 8))
        self.alt = self.readout(second, MINT, 13)
        pad = tk.Frame(frame, bg=PAPER)
        pad.pack(fill="both", expand=True, pady=(12, 0))
        rows = [("AC", "±", "⌫", "÷"), ("7", "8", "9", "×"),
                ("4", "5", "6", "−"), ("1", "2", "3", "+"), ("0", ",", "=")]
        self.digits = {}
        for col in range(4):
            pad.columnconfigure(col, weight=1, uniform="key")
        for row, keys in enumerate(rows):
            pad.rowconfigure(row, weight=1, uniform="row")
            col = 0
            for key in keys:
                span = 2 if key == "0" else 1
                bg = MINT if key == "=" else SOFT if key in OPERATIONS or row == 0 else "#ffffff"
                btn = self.button(pad, key, lambda k=key: self.press(k), bg, INK, 16)
                btn.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=3, pady=3)
                if key.isdigit():
                    self.digits[key] = btn
                col += span
        root.bind("<KeyPress>", self.keyboard)
        self.refresh()

    def button(self, parent, label, command, bg, fg, size):
        return tk.Button(parent, text=label, command=command, bg=bg, fg=fg,
                         activebackground="#c0dccc", activeforeground=INK,
                         disabledforeground="#9da9a2", relief="flat", borderwidth=0,
                         highlightthickness=1, highlightbackground=PAPER,
                         highlightcolor="#508b79", font=(self.sans, size, "bold"),
                         cursor="hand2", takefocus=True)

    def readout(self, parent, color, size):
        field = tk.Entry(parent, readonlybackground=DISPLAY, fg=color, width=1,
                         state="readonly", relief="flat", bd=0, highlightthickness=0,
                         justify="right", selectbackground="#47756b",
                         selectforeground="white", font=(self.mono, size))
        field.pack(fill="x", expand=True, pady=2)
        return field

    @staticmethod
    def write(field, value):
        field.configure(state="normal")
        field.delete(0, "end")
        field.insert(0, value)
        field.configure(state="readonly")
        field.xview_moveto(1)

    def change_base(self, base):
        self.calc.switch(base)
        self.refresh()

    def press(self, key):
        c = self.calc
        if key == "AC":
            c.clear()
        elif key == "±":
            c.sign()
        elif key in OPERATIONS or key == "=":
            c.operate(key)
        else:
            c.edit("back" if key == "⌫" else key)
        self.refresh()

    def keyboard(self, event):
        if event.state & 0x0c:  # Keep native copy and system shortcuts available.
            return
        special = {"Return": "=", "KP_Enter": "=", "BackSpace": "⌫",
                   "Escape": "AC", "Delete": "AC", "F9": "±",
                   "KP_Decimal": ",", "KP_Separator": ","}
        chars = {"*": "×", "/": "÷", "-": "−", ".": ","}
        key = special.get(event.keysym, chars.get(event.char, event.char))
        if key.lower() in ("b", "d"):
            self.change_base(2 if key.lower() == "b" else 10)
        elif key in (*"0123456789,+=", "×", "÷", "−", "⌫", "AC", "±"):
            self.press(key)
        else:
            return
        return "break"

    def refresh(self):
        c = self.calc
        other = 2 if c.base == 10 else 10
        self.caption.configure(text="System dwójkowy" if c.base == 2 else "System dziesiętny")
        for base, btn in self.tabs.items():
            btn.configure(bg=DISPLAY if base == c.base else SOFT,
                          fg="white" if base == c.base else INK)
        for key, btn in self.digits.items():
            enabled = int(key) < c.base
            btn.configure(state="normal" if enabled else "disabled",
                          bg="white" if enabled else "#e7e9e2",
                          cursor="hand2" if enabled else "arrow")
        main = c.error or (c.raw.replace("-", "−") if c.raw is not None else notation(c.value, c.base))
        size = 16 if c.error or len(main) > 16 else 21 if len(main) > 11 else 27
        self.number.configure(font=(self.mono, size))
        self.write(self.history, c.equation())
        self.write(self.number, main)
        self.alt_name.configure(text=BASE_NAME[other])
        self.write(self.alt, "" if c.error else notation(c.value, other))


if __name__ == "__main__":
    app = tk.Tk()
    Window(app)
    app.mainloop()
