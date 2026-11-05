"""CyCierge Pi dashboard - Administrative Report page (weekly / monthly / yearly).

Used by Main.py (a frame like the others). To test it on its own, on the Pi:
    python3 report_view.py
It reads http://localhost/cycierge/admin/getreport.php (localhost-only endpoint). Override with:
    CYCIERGE_BASE=http://localhost:8080/cycierge python3 report_view.py
"""
import calendar
import csv
import os
from datetime import date, timedelta
from tkinter import *
import tkinter.ttk as ttk
from tkinter import messagebox

import requests
from tkcalendar import DateEntry

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


class showReport(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.data = None

        canvas = Canvas(self, bg="white")
        Label(canvas, text="ADMINISTRATIVE REPORT", font=("", 20, "bold"), bg="white").place(relx=0.5, rely=0.04, anchor="center")

        # --- controls -------------------------------------------------------------------------------
        Label(canvas, text="Period:", bg="white").place(relx=0.05, rely=0.10, anchor="w")
        self.period = ttk.Combobox(canvas, values=list(PERIODS), state="readonly", width=10)
        self.period.current(0)
        self.period.place(relx=0.10, rely=0.10, anchor="w")
        self.period.bind("<<ComboboxSelected>>", lambda e: self.load())

        Label(canvas, text="Date:", bg="white").place(relx=0.20, rely=0.10, anchor="w")
        self.day = DateEntry(canvas, date_pattern="yyyy-mm-dd", width=11)
        self.day.place(relx=0.24, rely=0.10, anchor="w")
        self.day.bind("<<DateEntrySelected>>", lambda e: self.load())

        Button(canvas, text="< PREV", bg="skyblue", command=lambda: self.step(-1)).place(relx=0.36, rely=0.10, anchor="w", h=30, w=80)
        Button(canvas, text="NEXT >", bg="skyblue", command=lambda: self.step(1)).place(relx=0.42, rely=0.10, anchor="w", h=30, w=80)
        Button(canvas, text="TODAY", bg="skyblue", command=self.today).place(relx=0.48, rely=0.10, anchor="w", h=30, w=80)
        Button(canvas, text="REFRESH", bg="skyblue", command=self.load).place(relx=0.54, rely=0.10, anchor="w", h=30, w=80)

        self.range_lbl = Label(canvas, text="", font=("", 12, "bold"), bg="white")
        self.range_lbl.place(relx=0.5, rely=0.16, anchor="center")

        # --- summary per unit -----------------------------------------------------------------------
        cols = ("ROOM", "TENANT", "CHECK-INS", "UNLOCKS", "BY TENANT", "BY ADMIN", "DETECTIONS", "OCCUPIED DAYS", "OCCUPANCY")
        self.sum = ttk.Treeview(canvas, columns=cols, show="headings", height=4)
        for c in cols:
            self.sum.heading(c, text=c)
            self.sum.column(c, width=260 if c == "TENANT" else 100, anchor="center")
        self.sum.place(relx=0.5, rely=0.28, anchor="center", w=1300, h=140)

        # --- breakdown (day by day for week/month, month by month for year) ---------------------------
        self.det = ttk.Treeview(canvas, show="headings")
        sb = ttk.Scrollbar(canvas, orient="vertical", command=self.det.yview)
        self.det.configure(yscrollcommand=sb.set)
        self.det.place(relx=0.5, rely=0.62, anchor="center", w=1280, h=380)
        sb.place(relx=0.5, rely=0.62, anchor="center", x=650, h=380)

        Button(canvas, text="EXPORT CSV", bg="skyblue", command=self.export).place(relx=0.3, rely=0.93, anchor="center", h=40, w=150)
        Button(canvas, text="BACK", bg="skyblue", command=lambda: controller.show_frame("Main")).place(relx=0.5, rely=0.93, anchor="center", h=40, w=150)

        canvas.place(relx=0.5, rely=0.5, anchor="center", h=850, w=1400)

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
        try:
            r = requests.get(BASE + "/admin/getreport.php",
                             params={"period": self._period(), "date": self.day.get_date().isoformat()}, timeout=10)
            r.raise_for_status()
            self.data = r.json()
        except Exception as e:
            messagebox.showerror("Report", "Could not load the report:\n%s" % e)
            return
        self.render(self.data)

    def render(self, d):
        self.range_lbl.config(text="%s to %s   (%d of %d days elapsed)" % (d["start"], d["end"], d["elapsed_days"], d["days"]))

        self.sum.delete(*self.sum.get_children())
        for r in d["rooms"]:
            self.sum.insert("", "end", values=(
                "Room %d" % r["room"], r["tenant"], r["checkins"], r["unlocks"], r["unlocks_tenant"], r["unlocks_admin"],
                r["detections"], r["occupied_days"], "%.1f %%" % r["occupancy_pct"]))
        t = d["totals"]
        self.sum.insert("", "end", values=("ALL ROOMS", "", t["checkins"], t["unlocks"], t["unlocks_tenant"], t["unlocks_admin"],
                                           t["detections"], t["occupied_days"], "%.1f %%" % t["occupancy_pct"]))

        rooms = d["rooms"]
        cols = ["PERIOD"] + ["R%d %s" % (r["room"], k) for r in rooms for k in ("UNLOCKS", "DETECTIONS", "OCCUPIED")]
        self.det["columns"] = cols
        for c in cols:
            self.det.heading(c, text=c)
            self.det.column(c, width=100 if c == "PERIOD" else 120, anchor="center")
        self.det.delete(*self.det.get_children())
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
    root = Tk()
    root.title("CyCierge report (standalone)")
    root.minsize(1440, 900)

    class _Controller:
        def show_frame(self, name):
            root.destroy()

    page = showReport(root, _Controller())
    page.pack(fill="both", expand=True)
    page.on_show()
    root.mainloop()
