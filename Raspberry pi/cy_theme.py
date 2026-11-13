"""CyCierge dashboard theme - same brochure palette as the tenant web app and the Android admin app
(see android-admin/.../Theme.kt and php/cycierge/user/style.css).

Everything look-and-feel lives here so Main.py and report_view.py stay about behaviour.
"""
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk

NAVY = "#0B1F3A"      # window background
NAVY2 = "#13294A"     # cards / bars
NAVY3 = "#1B3A5F"     # raised: hover, table headings
TEAL = "#0A6C72"
TEAL2 = "#0F868D"
AMBER = "#FCB415"     # primary action
AMBER2 = "#FFCF5C"    # primary hover
CREAM = "#FFF8E8"     # text
MUTE = "#9CC3C6"      # secondary text
OK = "#5FE0B0"
LOW = "#FF7A6B"
LINE = "#344D61"      # 28% MUTE over NAVY, used for borders

FONT = "TkDefaultFont"   # resolved to a real family in setup()


def setup(root):
    """Call once after Tk() exists: sets the base font, window colour and ttk styles."""
    global FONT
    FONT = tkfont.nametofont("TkDefaultFont").actual("family")
    root.configure(bg=NAVY)
    root.option_add("*Font", (FONT, 11))

    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure("Cy.Treeview", background=NAVY, fieldbackground=NAVY, foreground=CREAM,
                 bordercolor=LINE, lightcolor=NAVY, darkcolor=NAVY, rowheight=26, borderwidth=0, font=(FONT, 10))
    st.map("Cy.Treeview", background=[("selected", TEAL)], foreground=[("selected", CREAM)])
    st.configure("Cy.Treeview.Heading", background=NAVY3, foreground=MUTE, relief="flat",
                 font=(FONT, 9, "bold"), bordercolor=NAVY3, lightcolor=NAVY3, darkcolor=NAVY3, padding=(6, 5))
    st.map("Cy.Treeview.Heading", background=[("active", TEAL)])
    st.configure("Vertical.TScrollbar", background=NAVY3, troughcolor=NAVY, bordercolor=NAVY,
                 arrowcolor=MUTE, lightcolor=NAVY3, darkcolor=NAVY3, gripcount=0)
    st.map("Vertical.TScrollbar", background=[("active", TEAL)])
    st.configure("Cy.TCombobox", fieldbackground=NAVY, background=NAVY3, foreground=CREAM,
                 arrowcolor=AMBER, bordercolor=LINE, lightcolor=NAVY, darkcolor=NAVY, selectbackground=NAVY,
                 selectforeground=CREAM)
    st.map("Cy.TCombobox", fieldbackground=[("readonly", NAVY)], foreground=[("readonly", CREAM)])
    st.configure("DateEntry", fieldbackground=NAVY, background=NAVY3, foreground=CREAM, arrowcolor=AMBER,
                 bordercolor=LINE, lightcolor=NAVY, darkcolor=NAVY, selectbackground=NAVY, selectforeground=CREAM)
    st.map("DateEntry", fieldbackground=[("readonly", NAVY)], foreground=[("readonly", CREAM)])
    root.option_add("*TCombobox*Listbox.background", NAVY2)
    root.option_add("*TCombobox*Listbox.foreground", CREAM)
    root.option_add("*TCombobox*Listbox.selectBackground", TEAL)


def font(size=11, weight="normal"):
    return (FONT, size, weight)


# ----------------------------------------------------------------------------------------------
# widgets
# ----------------------------------------------------------------------------------------------
_STYLES = {   # kind: (bg, hover bg, fg, border)
    "amber": (AMBER, AMBER2, NAVY, AMBER),
    "teal": (TEAL, TEAL2, CREAM, TEAL),
    "ghost": (NAVY2, NAVY3, CREAM, LINE),
    "danger": (NAVY2, NAVY3, LOW, LOW),
}


class CyButton(tk.Button):
    """Flat button in one of four styles: amber (main action), teal, ghost, danger."""

    def __init__(self, parent, text, command, kind="ghost", **kw):
        bg, hover, fg, border = _STYLES[kind]
        kw.setdefault("padx", 14)
        kw.setdefault("pady", 8)
        super().__init__(parent, text=text, command=command, bg=bg, fg=fg, activebackground=hover,
                         activeforeground=fg, relief="flat", bd=0, cursor="hand2", font=font(11, "bold"),
                         highlightthickness=1, highlightbackground=border, highlightcolor=border, **kw)
        self._bg, self._hover = bg, hover
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))


def card(parent, **kw):
    """Bordered NAVY2 panel (the CyCard of the Android app)."""
    return tk.Frame(parent, bg=NAVY2, highlightthickness=1, highlightbackground=LINE, **kw)


def entry(parent, var, show=None, width=30):
    return tk.Entry(parent, textvariable=var, show=show, width=width, bg=NAVY, fg=CREAM, insertbackground=AMBER,
                    relief="flat", highlightthickness=1, highlightbackground=LINE, highlightcolor=AMBER,
                    font=font(12))


def pill(parent, text, color=MUTE):
    """Small rounded-look status chip; returns the Label so the caller can .config() it later."""
    return tk.Label(parent, text=text, fg=color, bg=NAVY, font=font(9, "bold"), padx=10, pady=3,
                    highlightthickness=1, highlightbackground=LINE)


def make_tree(parent, columns, widths, stretch_col=None, height=6):
    """Themed Treeview + scrollbar inside one frame. Returns (frame, tree)."""
    f = tk.Frame(parent, bg=NAVY, highlightthickness=1, highlightbackground=LINE)
    tree = ttk.Treeview(f, columns=columns, show="headings", style="Cy.Treeview", height=height)
    sb = ttk.Scrollbar(f, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    for c, w in zip(columns, widths):
        tree.heading(c, text=c)
        tree.column(c, width=w, minwidth=40, anchor="w", stretch=(stretch_col == "*" or c == stretch_col))
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return f, tree


def dialog(parent, title, heading, note=None):
    """Themed modal Toplevel with a heading. Returns (win, body_frame); put rows in body_frame with grid()."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=NAVY2)
    win.transient(parent)
    win.resizable(False, False)
    tk.Label(win, text=heading, font=font(17, "bold"), bg=NAVY2, fg=AMBER).pack(padx=26, pady=(22, 4))
    if note:
        tk.Label(win, text=note, bg=NAVY2, fg=MUTE, justify="center", font=font(10)).pack(padx=26)
    body = tk.Frame(win, bg=NAVY2)
    body.pack(padx=26, pady=(12, 0))
    return win, body


def field_row(body, row, label, var, show=None):
    tk.Label(body, text=label, bg=NAVY2, fg=MUTE, font=font(10, "bold")).grid(row=row, column=0, sticky="e", padx=(0, 12), pady=7)
    e = entry(body, var, show=show)
    e.grid(row=row, column=1, ipady=5, pady=7)
    return e


def dialog_footer(win, save_text, save_cmd):
    """Error label + SAVE / CANCEL. Returns the error Label."""
    err = tk.Label(win, text="", fg=LOW, bg=NAVY2, wraplength=380, font=font(10))
    err.pack(padx=26, pady=(8, 0))
    row = tk.Frame(win, bg=NAVY2)
    row.pack(pady=(10, 22))
    CyButton(row, "CANCEL", win.destroy, "ghost", width=12).pack(side="left", padx=6)
    CyButton(row, save_text, save_cmd, "amber", width=14).pack(side="left", padx=6)
    win.bind("<Return>", lambda e: save_cmd())
    win.bind("<Escape>", lambda e: win.destroy())
    win.update_idletasks()
    p = win.master
    x = p.winfo_rootx() + (p.winfo_width() - win.winfo_reqwidth()) // 2
    y = p.winfo_rooty() + (p.winfo_height() - win.winfo_reqheight()) // 2
    win.geometry("+%d+%d" % (max(0, x), max(0, y)))
    return err


def page_header(parent, title, back_cmd=None):
    """Top bar used by the sub-pages (recordings, report). Returns (bar, right_frame) - pack extra buttons in right_frame."""
    bar = tk.Frame(parent, bg=NAVY2)
    bar.pack(fill="x")
    if back_cmd:
        CyButton(bar, "<  BACK", back_cmd, "ghost").pack(side="left", padx=(16, 0), pady=10)
    tk.Label(bar, text=title, bg=NAVY2, fg=CREAM, font=font(18, "bold")).pack(side="left", padx=16)
    right = tk.Frame(bar, bg=NAVY2)
    right.pack(side="right", padx=16)
    tk.Frame(parent, bg=TEAL2, height=2).pack(fill="x")
    return bar, right
