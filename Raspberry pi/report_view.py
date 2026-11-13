"""CyCierge Pi dashboard - Administrative Report page (weekly / monthly / yearly).

Used by Main.py (a frame like the others). To test it on its own, on the Pi:
    python3 report_view.py
It reads http://localhost/cycierge/admin/getreport.php (localhost-only endpoint). Override with:
    CYCIERGE_BASE=http://localhost:8080/cycierge python3 report_view.py
"""
import calendar
import csv
import os
import threading
import tkinter as tk
import tkinter.ttk as ttk
from datetime import date, timedelta
from tkinter import messagebox

import requests
from tkcalendar import DateEntry

import cy_theme as cy

BASE = os.environ.get("CYCIERGE_BASE", "http://localhost/cycierge")
EXPORT_DIR = os.path.expanduser("~/Desktop/Reports")
PERIODS = {"Weekly": "week", "Monthly": "month", "Yearly": "year"}


def shift(day, period, direction):
    """Move `day` one week / month / year forward (+1) or back (-1)."""
    if period == "week":
        return day + timedelta(days=7 * direction)
    if period == "month":
        m = day.month - 1 + direction
        y, m = day.year + m // 12, m % 12 + 1
        return date(y, m, min(day.day, calendar.monthrange(y, m)[1]))
    y = day.year + direction
    return date(y, day.month, min(day.day, calendar.monthrange(y, day.month)[1]))


class showReport(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=cy.NAVY)
        self.controller = controller
        self.data = None
        self._loading = False

        _, right = cy.page_header(self, "Administrative Report", lambda: controller.show_frame("Main"))
        cy.CyButton(right, "EXPORT CSV", self.export, "amber").pack(side="right", padx=(8, 0))
        cy.CyButton(right, "REFRESH", self.load, "ghost").pack(side="right")

        body = tk.Frame(self, bg=cy.NAVY)
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        # --- controls -------------------------------------------------------------------------------
        bar = cy.card(body)
        bar.grid(row=0, column=0, sticky="ew")
        row = tk.Frame(bar, bg=cy.NAVY2)
        row.pack(fill="x", padx=14, pady=12)
        tk.Label(row, text="PERIOD", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(9, "bold")).pack(side="left")
        self.period = ttk.Combobox(row, values=list(PERIODS), state="readonly", width=10, style="Cy.TCombobox")
        self.period.current(0)
        self.period.pack(side="left", padx=(8, 18))
        self.period.bind("<<ComboboxSelected>>", lambda e: self.load())

        tk.Label(row, text="DATE", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(9, "bold")).pack(side="left")
        self.day = DateEntry(row, date_pattern="yyyy-mm-dd", width=11, background=cy.TEAL, foreground=cy.CREAM,
                             bordercolor=cy.LINE, headersbackground=cy.NAVY3, headersforeground=cy.MUTE,
                             selectbackground=cy.AMBER, selectforeground=cy.NAVY, normalbackground=cy.NAVY2,
                             normalforeground=cy.CREAM, weekendbackground=cy.NAVY2, weekendforeground=cy.AMBER,
                             othermonthbackground=cy.NAVY, othermonthforeground=cy.MUTE,
                             othermonthwebackground=cy.NAVY, othermonthweforeground=cy.MUTE,
                             disabledbackground=cy.NAVY, disabledforeground=cy.MUTE, font=cy.font(11))
        self.day.pack(side="left", padx=(8, 18), ipady=3)
        self.day.bind("<<DateEntrySelected>>", lambda e: self.load())

        cy.CyButton(row, "<  PREV", lambda: self.step(-1), "ghost").pack(side="left", padx=(0, 6))
        cy.CyButton(row, "TODAY", self.today, "teal").pack(side="left", padx=6)
        cy.CyButton(row, "NEXT  >", lambda: self.step(1), "ghost").pack(side="left", padx=6)
        self.range_lbl = tk.Label(row, text="", bg=cy.NAVY2, fg=cy.CREAM, font=cy.font(12, "bold"))
        self.range_lbl.pack(side="right")

        # --- all-rooms tiles (same numbers as the Android report) -------------------------------------
        tiles = tk.Frame(body, bg=cy.NAVY)
        tiles.grid(row=1, column=0, sticky="ew", pady=12)
        self.tiles = {}
        for i, (key, label) in enumerate((("occ", "OCCUPANCY"), ("checkins", "CHECK-INS"), ("unlocks", "UNLOCKS"), ("detections", "DETECTIONS"))):
            tiles.grid_columnconfigure(i, weight=1, uniform="tile")
            t = cy.card(tiles)
            t.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0 if i == 3 else 6))
            tk.Label(t, text=label, bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(9, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
            big = tk.Label(t, text="-", bg=cy.NAVY2, fg=cy.AMBER if key == "occ" else cy.CREAM, font=cy.font(26, "bold"))
            big.pack(anchor="w", padx=14)
            sub = tk.Label(t, text=" ", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(10))
            sub.pack(anchor="w", padx=14, pady=(0, 10))
            self.tiles[key] = (big, sub)

        # --- summary per unit -----------------------------------------------------------------------
        cols = ("ROOM", "TENANT", "CHECK-INS", "UNLOCKS", "BY TENANT", "BY ADMIN", "DETECTIONS", "OCCUPIED DAYS", "OCCUPANCY")
        f, self.sum = cy.make_tree(body, cols, [100, 200] + [120] * 7, stretch_col="*", height=4)
        for c in cols[2:]:
            self.sum.column(c, anchor="center")
        f.grid(row=2, column=0, sticky="ew")

        # --- breakdown (day by day for week/month, month by month for year) ---------------------------
        det = tk.Frame(body, bg=cy.NAVY)
        det.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        self.det_frame = det
        self.det = None

    # --- called by Main.show_frame each time the page is opened -------------------------------------
    def on_show(self):
        self.load()

    def _period(self):
        return PERIODS[self.period.get()]

    def step(self, direction):
        self.day.set_date(shift(self.day.get_date(), self._period(), direction))
        self.load()

    def today(self):
        self.day.set_date(date.today())
        self.load()

    def load(self):
        if self._loading:
            return
        self._loading = True
        period, day = self._period(), self.day.get_date().isoformat()

        def work():
            r = requests.get(BASE + "/admin/getreport.php", params={"period": period, "date": day}, timeout=10)
            r.raise_for_status()
            return r.json()

        def done(data, error):
            self._loading = False
            if error:
                messagebox.showerror("Report", "Could not load the report:\n%s" % error)
                return
            self.data = data
            self.render(data)
        self.controller.run_bg(work, done)

    def render(self, d):
        self.range_lbl.config(text="%s  to  %s     (%d of %d days elapsed)" % (d["start"], d["end"], d["elapsed_days"], d["days"]))
        t = d["totals"]
        self.tiles["occ"][0].config(text="%.1f %%" % t["occupancy_pct"])
        self.tiles["occ"][1].config(text="%d room-days" % t["occupied_days"])
        self.tiles["checkins"][0].config(text=str(t["checkins"]))
        self.tiles["unlocks"][0].config(text=str(t["unlocks"]))
        self.tiles["unlocks"][1].config(text="tenant %d  -  admin %d" % (t["unlocks_tenant"], t["unlocks_admin"]))
        self.tiles["detections"][0].config(text=str(t["detections"]))

        self.sum.delete(*self.sum.get_children())
        for r in d["rooms"]:
            self.sum.insert("", "end", values=(
                "Room %d" % r["room"], r["tenant"], r["checkins"], r["unlocks"], r["unlocks_tenant"], r["unlocks_admin"],
                r["detections"], r["occupied_days"], "%.1f %%" % r["occupancy_pct"]))
        self.sum.insert("", "end", values=("ALL ROOMS", "", t["checkins"], t["unlocks"], t["unlocks_tenant"], t["unlocks_admin"],
                                           t["detections"], t["occupied_days"], "%.1f %%" % t["occupancy_pct"]))

        # the breakdown table has a different set of columns per report, so it is rebuilt each time
        for w in self.det_frame.winfo_children():
            w.destroy()
        rooms = d["rooms"]
        cols = ["PERIOD"] + ["R%d %s" % (r["room"], k) for r in rooms for k in ("UNLOCKS", "DETECTIONS", "OCCUPIED")]
        f, self.det = cy.make_tree(self.det_frame, cols, [110] + [120] * (len(cols) - 1), stretch_col="*", height=8)
        for c in cols[1:]:
            self.det.column(c, anchor="center")
        f.pack(fill="both", expand=True)
        for i, b in enumerate(rooms[0]["buckets"] if rooms else []):
            row = [b["label"]]
            for r in rooms:
                bb = r["buckets"][i]
                row += [bb["unlocks"], bb["detections"], bb["occupied_days"]]
            self.det.insert("", "end", values=row)

    def export(self):
        if not self.data:
            messagebox.showinfo("Report", "Nothing to export yet.")
            return
        d = self.data
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            path = os.path.join(EXPORT_DIR, "cycierge_%s_%s.csv" % (d["period"], d["start"]))
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["CyCierge report", d["period"], d["start"], d["end"], "elapsed days", d["elapsed_days"], "generated", d["generated"]])
                w.writerow([])
                w.writerow(["room", "tenant", "check-ins", "unlocks", "by tenant", "by admin", "detections", "occupied days", "occupancy %"])
                for r in d["rooms"]:
                    w.writerow([r["room"], r["tenant"], r["checkins"], r["unlocks"], r["unlocks_tenant"], r["unlocks_admin"],
                                r["detections"], r["occupied_days"], r["occupancy_pct"]])
                t = d["totals"]
                w.writerow(["all", "", t["checkins"], t["unlocks"], t["unlocks_tenant"], t["unlocks_admin"], t["detections"],
                            t["occupied_days"], t["occupancy_pct"]])
                w.writerow([])
                w.writerow(["room", "period", "from", "to", "unlocks", "detections", "occupied days"])
                for r in d["rooms"]:
                    for b in r["buckets"]:
                        w.writerow([r["room"], b["label"], b["from"], b["to"], b["unlocks"], b["detections"], b["occupied_days"]])
        except Exception as e:
            messagebox.showerror("Report", "Could not write the CSV:\n%s" % e)
            return
        messagebox.showinfo("Report", "Saved:\n%s" % path)


if __name__ == "__main__":
    root = tk.Tk()
    cy.setup(root)
    root.title("CyCierge report (standalone)")
    root.minsize(1100, 680)

    class _Controller:
        def show_frame(self, name):
            root.destroy()

        def run_bg(self, work, done):
            def go():
                try:
                    res, err = work(), None
                except Exception as e:
                    res, err = None, e
                root.after(0, lambda: done(res, err))
            threading.Thread(target=go, daemon=True).start()

    page = showReport(root, _Controller())
    page.pack(fill="both", expand=True)
    page.on_show()
    root.mainloop()
