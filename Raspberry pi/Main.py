"""CyCierge Pi dashboard (Tkinter).

One window, everything on the first screen: both rooms with live camera, tenant, time stayed,
battery, door state, actions and the activity log. Recordings and Reports are sub-pages.

Run:   python3 Main.py          (or double-click the CyCierge icon - see install_shortcut.sh)
Debug: python3 Main.py          prints to the terminal; the icon writes ~/cycierge-dashboard.log

Design: same brochure palette as the tenant web app and the Android admin app (cy_theme.py).
Threading: ALL network and camera work runs in background threads; the Tk thread only draws.
That is what keeps the buttons responsive.
"""
import os
import queue
import re
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import cv2
import requests
from PIL import Image as Img
from PIL import ImageTk

import cy_theme as cy
from report_view import showReport   # Administrative Report page (report_view.py, same folder)

try:
    from tkVideoPlayer import TkinterVideo
except ImportError:                  # dashboard still works, only the recordings player is missing
    TkinterVideo = None

# ************************************************************************************
# SETTINGS
# ************************************************************************************
APP_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.environ.get("CYCIERGE_VIDEO_DIR", os.path.join(APP_DIR, "VideoCapture"))
BASE = os.environ.get("CYCIERGE_BASE", "http://localhost/cycierge")
CAMERAS = {1: os.environ.get("CYCIERGE_CAM1", "http://192.168.0.112/stream"),    # Pi-side cameras
           2: os.environ.get("CYCIERGE_CAM2", "http://192.168.0.122/stream")}
ROOMS = (1, 2)
MIRROR = True          # the live preview was always mirrored; recordings are saved un-mirrored
REC_FPS = 5            # recording frame rate
POLL_SECONDS = 1.0     # how often tenants + logs are refreshed
MAX_LOG_ROWS = 200     # per room, newest first

os.makedirs(VIDEO_DIR, exist_ok=True)
_name_lock = threading.Lock()      # two rooms can start recording in the same second


# ************************************************************************************
# SERVER ACCESS (always with a timeout, never on the Tk thread)
# ************************************************************************************
def api(path, **params):
    r = requests.get(BASE + path, params=params, timeout=5)
    r.raise_for_status()
    return r


def api_json(path, **params):
    return api(path, **params).json()


def room_arg(room):
    return "'%d'" % room


def stay_text(row):
    """'3 days 4 hr 12 min' since check-in (USERDATE + USERTIME), '-' when unknown."""
    if not row:
        return "-"
    stamp = "%s %s" % ((row.get("USERDATE") or "").strip(), (row.get("USERTIME") or "").strip())
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            d = datetime.now() - datetime.strptime(stamp, fmt)
        except ValueError:
            continue
        if d.total_seconds() < 0:
            return "-"
        h, m = divmod(d.seconds // 60, 60)
        return "%d %s %d hr %d min" % (d.days, "day" if d.days == 1 else "days", h, m)
    return "-"


# ************************************************************************************
# BACKGROUND WORKERS
# ************************************************************************************
class Poller(threading.Thread):
    """Fetches tenants (getdata.php) and logs (getlogs.php) every second and keeps the latest copy."""

    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.wake = threading.Event()     # set() = refresh right now
        self.tenants = {}                 # room -> TBLUSER row
        self.logs = {r: [] for r in ROOMS}
        self.online = False
        self.version = 0

    def run(self):
        while True:
            try:
                rows = api_json("/user/getdata.php")
                logs = api_json("/user/getlogs.php")
                tenants = {int(r["ID"]): r for r in rows}
                per_room = {r: [] for r in ROOMS}
                for l in logs:
                    if str(l.get("LOGSID")) in map(str, ROOMS):
                        per_room[int(l["LOGSID"])].append(l)
                for r in ROOMS:
                    per_room[r].sort(key=lambda l: (str(l["LOGSDATE"]), str(l["LOGSTIME"])), reverse=True)
                    per_room[r] = per_room[r][:MAX_LOG_ROWS]
                with self.lock:
                    self.tenants, self.logs, self.online = tenants, per_room, True
                    self.version += 1
            except Exception as e:
                with self.lock:
                    if self.online:
                        print("poll failed:", e)
                    self.online = False
            self.wake.wait(POLL_SECONDS)
            self.wake.clear()

    def snapshot(self):
        with self.lock:
            return self.tenants, self.logs, self.online, self.version

    def tenant(self, room):
        with self.lock:
            return self.tenants.get(room)

    def want_record(self, room):
        """True/False from USERCAM, None while the server hasn't answered yet (keep current state)."""
        row = self.tenant(room)
        if row is None:
            return None
        return str(row.get("USERCAM")) == "1"


class CameraWorker(threading.Thread):
    """Reads one ESP32-CAM stream, keeps the newest frame, and records while USERCAM == 1."""

    def __init__(self, room, url, poller):
        super().__init__(daemon=True)
        self.room, self.url, self.poller = room, url, poller
        self.lock = threading.Lock()
        self.frame = None
        self.online = False
        self.stopping = False
        self.writer = None
        self.last_write = 0.0
        self.retry_at = 0.0

    def run(self):
        cap = None
        while not self.stopping:
            if cap is None:
                cap = cv2.VideoCapture(self.url)
            ok, frame = (cap.read() if cap.isOpened() else (False, None))
            if not ok or frame is None:
                self.online = False
                self._stop_recording()
                cap.release()
                cap = None
                time.sleep(2)           # camera off / rebooting: retry every 2 s instead of spinning
                continue
            self.online = True
            with self.lock:
                self.frame = frame
            self._record(frame)
        if cap is not None:
            cap.release()
        self._stop_recording()

    def _record(self, frame):
        want = self.poller.want_record(self.room)
        if want is None:
            want = self.writer is not None
        if want and self.writer is None and time.time() >= self.retry_at:
            h, w = frame.shape[:2]
            with _name_lock:           # file names are timestamps: if taken (other room, same second) use the next second
                stamp = datetime.now()
                while os.path.exists(os.path.join(VIDEO_DIR, stamp.strftime("%Y%m%d%H%M%S") + ".avi")):
                    stamp += timedelta(seconds=1)
                name = stamp.strftime("%Y%m%d%H%M%S")
                writer = cv2.VideoWriter(os.path.join(VIDEO_DIR, name + ".avi"), cv2.VideoWriter_fourcc(*"XVID"), REC_FPS, (w, h))
            if not writer.isOpened():
                print("room %d: can't write to %s" % (self.room, VIDEO_DIR))
                self.retry_at = time.time() + 5
                return
            self.writer = writer
            try:
                api("/admin/insertlogs.php", RECORDID=room_arg(self.room), DT="'%s'" % name)
                print("room %d: recording %s" % (self.room, name))
            except Exception as e:
                print("room %d: recording saved but not registered:" % self.room, e)
        elif not want and self.writer is not None:
            self._stop_recording()
        if self.writer is not None and time.time() - self.last_write >= 1.0 / REC_FPS:
            self.writer.write(frame)
            self.last_write = time.time()

    def _stop_recording(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            print("room %d: recording stopped" % self.room)

    def latest(self):
        with self.lock:
            return self.frame

    def close(self):
        self.stopping = True


# ************************************************************************************
# DIALOGS (same fields and rules as the Android admin app)
# ************************************************************************************
def tenant_dialog(app, room, new=False):
    """Edit tenant: Name / Username / New password (blank keeps the current one).
    New tenant: empty form, password required; check-in is set to now and "time stayed" restarts."""
    cur = app.poller.tenant(room)
    if cur is None:
        messagebox.showerror("Error", "Couldn't load the tenant: the dashboard can't reach the server.")
        return
    old_name = (cur.get("USERNAME") or "").strip()
    if new and old_name:
        if not messagebox.askyesno("New tenant", "Room %d is occupied by %s.\nTheir stay ends now and time stayed restarts "
                                                 "for the new tenant.\n\nContinue?" % (room, old_name)):
            return

    win, body = cy.dialog(app, "New tenant" if new else "Edit tenant",
                          ("New tenant - room %d" if new else "Edit tenant - room %d") % room,
                          "Check-in time is set to now; time stayed restarts at 0." if new
                          else "Leave the password blank to keep the current one.")
    name_v = tk.StringVar(value="" if new else (cur.get("USERNAME") or ""))
    uid_v = tk.StringVar(value="" if new else (cur.get("USERID") or ""))
    pass_v = tk.StringVar()
    name_e = cy.field_row(body, 0, "Name of tenant", name_v)
    cy.field_row(body, 1, "Username (tenant login)", uid_v)
    cy.field_row(body, 2, "Password" if new else "New password", pass_v, show="*")

    def save():
        name, uid, pw = name_v.get().strip(), uid_v.get().strip(), pass_v.get()
        if not name or not uid or (new and not pw):
            err.config(text="Name, username and password are required" if new else "Name and username are required")
            return
        err.config(text="Saving...", fg=cy.MUTE)

        def work():
            r = requests.post(BASE + ("/user/newtenant.php" if new else "/user/edituser.php"), timeout=5,
                              json={"room": room, "name": name, "userid": uid, "password": pw})
            r.raise_for_status()

        def done(_, error):
            if error:
                err.config(text="Couldn't save: %s" % error, fg=cy.LOW)
            else:
                app.poller.wake.set()
                win.destroy()
        app.run_bg(work, done)

    err = cy.dialog_footer(win, "CHECK IN" if new else "SAVE", save)
    win.wait_visibility()
    win.grab_set()
    name_e.focus_set()


ADMIN_ERRORS = {
    "wrong_password": "Current password is wrong.",
    "blocked": "Too many failed attempts. Try again in 10 minutes.",
    "bad_username": "Username must be 3-32 characters: letters, numbers, dot, dash or underscore.",
    "weak_password": "New password must be at least 8 characters.",
    "password_too_long": "New password is too long (72 characters max).",
    "same_password": "New password must be different from the current one.",
    "nothing_to_change": "Nothing to change.",
}


def admin_login_dialog(app):
    """Change the admin login (used by the Android admin app and the web admin page).
    Signs in with the CURRENT login first, then calls admin/api/change_credentials.php - the same
    endpoint and rules as the Android app. A blank new username / new password keeps the current one.
    Other signed-in phones and browsers are signed out by the Pi after a successful change."""
    win, body = cy.dialog(app, "Admin login", "Change admin login",
                          "Leave the new username or password blank to keep the current one.\n"
                          "This also changes the web admin login and signs out other devices.")
    cur_user_v, cur_pass_v = tk.StringVar(), tk.StringVar()
    new_user_v, new_pass_v, conf_v = tk.StringVar(), tk.StringVar(), tk.StringVar()
    cur_user_e = cy.field_row(body, 0, "Current username", cur_user_v)
    cy.field_row(body, 1, "Current password", cur_pass_v, show="*")
    cy.field_row(body, 2, "New username", new_user_v)
    cy.field_row(body, 3, "New password", new_pass_v, show="*")
    cy.field_row(body, 4, "Confirm new password", conf_v, show="*")

    def save():
        cu, cp = cur_user_v.get().strip(), cur_pass_v.get()
        nu, np_, cf = new_user_v.get().strip(), new_pass_v.get(), conf_v.get()
        problem = None
        if not cu or not cp:
            problem = "Enter the current username and password."
        elif not nu and not np_:
            problem = ADMIN_ERRORS["nothing_to_change"]
        elif nu and not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", nu):
            problem = ADMIN_ERRORS["bad_username"]
        elif np_ and len(np_) < 8:
            problem = ADMIN_ERRORS["weak_password"]
        elif np_ != cf:
            problem = "New passwords don't match."
        if problem:
            err.config(text=problem, fg=cy.LOW)
            return
        err.config(text="Saving...", fg=cy.MUTE)

        def work():
            """Returns an error message, or None when the login was changed."""
            s = requests.Session()
            r = s.post(BASE + "/admin/api/login.php", json={"username": cu, "password": cp}, timeout=5)
            if r.status_code == 401:
                return "Wrong current username or password."
            if r.status_code == 429:
                return ADMIN_ERRORS["blocked"]
            r.raise_for_status()
            r = s.post(BASE + "/admin/api/change_credentials.php", timeout=5,
                       json={"current_password": cp, "new_username": nu, "new_password": np_})
            if not r.ok:
                try:
                    key = r.json().get("error", "")
                except ValueError:
                    key = ""
                return ADMIN_ERRORS.get(key, "Couldn't save: HTTP %d" % r.status_code)
            return None

        def done(msg, error):
            if error:
                err.config(text="Couldn't save: %s" % error, fg=cy.LOW)
            elif msg:
                err.config(text=msg, fg=cy.LOW)
            else:
                messagebox.showinfo("Admin login", "Admin login updated.\nOther signed-in phones and browsers have been signed out.", parent=win)
                win.destroy()
        app.run_bg(work, done)

    err = cy.dialog_footer(win, "SAVE", save)
    win.wait_visibility()
    win.grab_set()
    cur_user_e.focus_set()


# ************************************************************************************
# APP + PAGES
# ************************************************************************************
class SampleApp(tk.Tk):

    def __init__(self):
        super().__init__()
        cy.setup(self)
        self.title("CyCierge Dashboard")
        self.minsize(1100, 680)
        try:
            self._icon = tk.PhotoImage(file=os.path.join(APP_DIR, "cycierge.png"))
            self.iconphoto(True, self._icon)
        except tk.TclError:
            pass
        try:
            self.attributes("-zoomed", True)          # start maximised on the Pi desktop
        except tk.TclError:
            pass
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        self._jobs = queue.Queue()
        self.poller = Poller()
        self.cams = {r: CameraWorker(r, CAMERAS[r], self.poller) for r in ROOMS}
        self.poller.start()
        for c in self.cams.values():
            c.start()

        container = tk.Frame(self, bg=cy.NAVY)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (Main, showRecord, showReport):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("Main")
        self.after(50, self._pump)

    def show_frame(self, page_name, **kw):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show(**kw)

    # ---- run slow things off the Tk thread; `done(result, error)` is called back ON the Tk thread ----
    def run_bg(self, work, done=None):
        def go():
            try:
                res, error = work(), None
            except Exception as e:
                res, error = None, e
            if done:
                self._jobs.put(lambda: done(res, error))
        threading.Thread(target=go, daemon=True).start()

    def _pump(self):
        try:
            while True:
                self._jobs.get_nowait()()
        except queue.Empty:
            pass
        self.after(50, self._pump)

    def quit_app(self):
        for c in self.cams.values():
            c.close()
        for c in self.cams.values():
            c.join(timeout=3)        # lets an open recording finish properly
        self.destroy()


class RoomPanel(tk.Frame):
    """One room: header chips, camera, tenant + time stayed, actions, activity log."""

    def __init__(self, parent, app, room):
        super().__init__(parent, bg=cy.NAVY2, highlightthickness=1, highlightbackground=cy.LINE)
        self.app, self.room = app, room
        self._shown_frame = None
        self._shown_logs = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(4, weight=1)

        # row 0 - title + chips
        head = tk.Frame(self, bg=cy.NAVY2)
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        tk.Label(head, text="ROOM %d" % room, bg=cy.NAVY2, fg=cy.AMBER, font=cy.font(20, "bold")).pack(side="left")
        self.cam_chip = cy.pill(head, "CAMERA OFFLINE", cy.LOW)
        self.batt_chip = cy.pill(head, "BATTERY -", cy.MUTE)
        self.door_chip = cy.pill(head, "DOOR -", cy.MUTE)
        for chip in (self.cam_chip, self.batt_chip, self.door_chip):
            chip.pack(side="right", padx=(6, 0))

        # row 1 - camera (image is fitted into this frame, keeping its aspect ratio)
        self.cam_box = tk.Frame(self, bg="#0A1629", highlightthickness=1, highlightbackground=cy.LINE)
        self.cam_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        self.cam_box.pack_propagate(False)
        self.cam = tk.Label(self.cam_box, text="CAMERA OFFLINE", bg="#0A1629", fg=cy.MUTE, font=cy.font(12, "bold"))
        self.cam.pack(expand=True)

        # row 2 - tenant + time stayed
        info = tk.Frame(self, bg=cy.NAVY2)
        info.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 2))
        info.grid_columnconfigure(0, weight=1)
        info.grid_columnconfigure(1, weight=1)
        tk.Label(info, text="TENANT", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(info, text="TIME STAYED", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(9, "bold")).grid(row=0, column=1, sticky="w")
        self.tenant_lbl = tk.Label(info, text="-", bg=cy.NAVY2, fg=cy.CREAM, font=cy.font(15, "bold"), anchor="w")
        self.tenant_lbl.grid(row=1, column=0, sticky="w")
        self.stay_lbl = tk.Label(info, text="-", bg=cy.NAVY2, fg=cy.CREAM, font=cy.font(15, "bold"), anchor="w")
        self.stay_lbl.grid(row=1, column=1, sticky="w")

        # row 3 - actions
        actions = tk.Frame(self, bg=cy.NAVY2)
        actions.grid(row=3, column=0, sticky="ew", padx=16, pady=10)
        for i in range(4):
            actions.grid_columnconfigure(i, weight=1, uniform="act")
        cy.CyButton(actions, "EDIT TENANT", lambda: tenant_dialog(app, room), "ghost").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        cy.CyButton(actions, "NEW TENANT", lambda: tenant_dialog(app, room, new=True), "teal").grid(row=0, column=1, sticky="ew", padx=6)
        cy.CyButton(actions, "RECORDINGS", lambda: app.show_frame("showRecord", room=room), "ghost").grid(row=0, column=2, sticky="ew", padx=6)
        self.unlock_btn = cy.CyButton(actions, "UNLOCK", self.unlock, "amber")
        self.unlock_btn.grid(row=0, column=3, sticky="ew", padx=(6, 0))

        # row 4 - activity log
        logs = tk.Frame(self, bg=cy.NAVY2)
        logs.grid(row=4, column=0, sticky="nsew", padx=16, pady=(0, 16))
        tk.Label(logs, text="ACTIVITY", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(9, "bold")).pack(anchor="w", pady=(0, 4))
        f, self.tree = cy.make_tree(logs, ("DATE", "TIME", "ACTIVITY"), (110, 90, 300), stretch_col="ACTIVITY", height=4)
        f.pack(fill="both", expand=True)

    # ---- actions -------------------------------------------------------------------------------
    def unlock(self):
        room = self.room
        self.unlock_btn.config(state="disabled")          # no double-unlock from a double click
        self.after(2000, lambda: self.unlock_btn.config(state="normal"))

        def work():
            api("/admin/unlock.php", USERLOCK="'1'", ID=room_arg(room))
            now = datetime.now()
            api("/admin/insertactivity.php", LOGSID=room_arg(room), LOGSDATE="'%s'" % now.strftime("%Y-%m-%d"),
                LOGSTIME="'%s'" % now.strftime("%H:%M"), LOGSACTIVITY="'Admin Unlock Door %d'" % room)

        def done(_, error):
            if error:
                messagebox.showerror("Unlock", "Couldn't unlock room %d:\n%s" % (room, error))
            self.app.poller.wake.set()
        self.app.run_bg(work, done)

    # ---- refresh (called by Main on the Tk thread) ---------------------------------------------
    def show_data(self, row, logs, online):
        self.tenant_lbl.config(text=(row or {}).get("USERNAME") or "-")
        self.stay_lbl.config(text=stay_text(row))
        if row:
            try:
                pct = max(0, min(100, int(float(row.get("USERBATT")))))
                color = cy.LOW if pct < 20 else (cy.AMBER if pct < 50 else cy.OK)
                self.batt_chip.config(text="BATTERY %d%%" % pct, fg=color)
            except (TypeError, ValueError):
                self.batt_chip.config(text="BATTERY -", fg=cy.MUTE)
            unlocking = str(row.get("USERLOCK")) == "1"
            self.door_chip.config(text="UNLOCKING..." if unlocking else "LOCKED", fg=cy.AMBER if unlocking else cy.OK)
        elif not online:
            self.batt_chip.config(text="BATTERY -", fg=cy.MUTE)
            self.door_chip.config(text="DOOR -", fg=cy.MUTE)

        shown = [(l["LOGSDATE"], l["LOGSTIME"], l["LOGSACTIVITY"]) for l in logs]
        if shown != self._shown_logs:                  # only redraw when it changed, keeps the scroll position
            self._shown_logs = shown
            self.tree.delete(*self.tree.get_children())
            for v in shown:
                self.tree.insert("", "end", values=v)

    def show_camera(self):
        worker = self.app.cams[self.room]
        frame = worker.latest() if worker.online else None
        if frame is None:
            if self._shown_frame is not None:
                self._shown_frame = None
                self.cam.config(image="", text="CAMERA OFFLINE")
                self.cam.imgtk = None
            self.cam_chip.config(text="CAMERA OFFLINE", fg=cy.LOW)
            return
        self.cam_chip.config(text="LIVE", fg=cy.OK)
        if frame is self._shown_frame:
            return
        self._shown_frame = frame
        bw, bh = self.cam_box.winfo_width() - 2, self.cam_box.winfo_height() - 2
        if bw < 20 or bh < 20:
            return
        h, w = frame.shape[:2]
        scale = min(bw / w, bh / h)
        img = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
        if MIRROR:
            img = cv2.flip(img, 1)
        imgtk = ImageTk.PhotoImage(image=Img.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
        self.cam.imgtk = imgtk
        self.cam.config(image=imgtk, text="")


class Main(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=cy.NAVY)
        self.controller = controller
        self._version = -1

        # top bar: brand, server status, clock, REPORTS, ADMIN LOGIN
        bar = tk.Frame(self, bg=cy.NAVY2)
        bar.pack(fill="x")
        tk.Label(bar, text="CyCierge", bg=cy.NAVY2, fg=cy.CREAM, font=cy.font(24, "bold")).pack(side="left", padx=(18, 8), pady=10)
        tk.Label(bar, text="ADMIN DASHBOARD", bg=cy.NAVY2, fg=cy.AMBER, font=cy.font(10, "bold")).pack(side="left", pady=(10, 0))
        right = tk.Frame(bar, bg=cy.NAVY2)
        right.pack(side="right", padx=18)
        cy.CyButton(right, "ADMIN LOGIN", lambda: admin_login_dialog(controller), "ghost").pack(side="right", padx=(8, 0))
        cy.CyButton(right, "REPORTS", lambda: controller.show_frame("showReport"), "teal").pack(side="right", padx=(8, 0))
        self.clock = tk.Label(right, text="", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(11))
        self.clock.pack(side="right", padx=(0, 14))
        self.server_chip = cy.pill(right, "SERVER ...", cy.MUTE)
        self.server_chip.pack(side="right", padx=(0, 14))
        tk.Frame(self, bg=cy.TEAL2, height=2).pack(fill="x")

        # both rooms side by side
        rooms = tk.Frame(self, bg=cy.NAVY)
        rooms.pack(fill="both", expand=True, padx=14, pady=14)
        rooms.grid_rowconfigure(0, weight=1)
        self.panels = {}
        for i, r in enumerate(ROOMS):
            rooms.grid_columnconfigure(i, weight=1, uniform="room")
            p = RoomPanel(rooms, controller, r)
            p.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == len(ROOMS) - 1 else 7))
            self.panels[r] = p

        self.after(100, self.tick_data)
        self.after(100, self.tick_cams)

    def tick_data(self):
        tenants, logs, online, version = self.controller.poller.snapshot()
        self.clock.config(text=datetime.now().strftime("%a %d %b %Y   %H:%M:%S"))
        self.server_chip.config(text="SERVER ONLINE" if online else "SERVER OFFLINE", fg=cy.OK if online else cy.LOW)
        for r, p in self.panels.items():
            p.show_data(tenants.get(r), logs.get(r, []), online)    # also keeps "time stayed" ticking
        self.after(1000, self.tick_data)

    def tick_cams(self):
        for p in self.panels.values():
            p.show_camera()
        self.after(80, self.tick_cams)


class showRecord(tk.Frame):
    """Recordings of one room: pick a date/time on the left, the video plays on the right."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=cy.NAVY)
        self.controller = controller
        self.room = 1
        self.paths = {}                    # tree item id -> .avi path

        bar, right = cy.page_header(self, "Recordings", lambda: controller.show_frame("Main"))
        self.title_lbl = bar.winfo_children()[1]
        cy.CyButton(right, "DELETE DATA", self.delete_all, "danger").pack()

        body = tk.Frame(self, bg=cy.NAVY)
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = cy.card(body)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        f, self.tree = cy.make_tree(left, ("DATE : TIME",), (240,), stretch_col="DATE : TIME", height=20)
        f.pack(fill="both", expand=True, padx=14, pady=14)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_card = cy.card(body)
        right_card.grid(row=0, column=1, sticky="nsew")
        self.player_box = tk.Frame(right_card, bg="#0A1629")
        self.player_box.pack(fill="both", expand=True, padx=14, pady=14)
        self.player = None
        if TkinterVideo is not None:
            try:
                self.player = TkinterVideo(self.player_box, scaled=True, keep_aspect=True)
            except TypeError:                     # older tkVideoPlayer without keep_aspect
                self.player = TkinterVideo(self.player_box, scaled=True)
            self.player.pack(fill="both", expand=True)
        self.msg = tk.Label(right_card, text="Select a recording on the left." if self.player else
                            "tkVideoPlayer is not installed:  pip3 install tkVideoPlayer", bg=cy.NAVY2, fg=cy.MUTE, font=cy.font(11))
        self.msg.pack(pady=(0, 12))

    def on_show(self, room=None):
        if room is not None:
            self.room = room
        self.title_lbl.config(text="Recordings - Room %d" % self.room)
        self.msg.config(text="Loading..." if self.player else self.msg.cget("text"))
        self.reload()

    def reload(self):
        room = self.room

        def work():
            return api_json("/user/getrecord.php")

        def done(rows, error):
            if room != self.room:
                return
            self.tree.delete(*self.tree.get_children())
            self.paths.clear()
            if error:
                self.msg.config(text="Couldn't load recordings: %s" % error)
                return
            mine = [r for r in rows if str(r["RECORDID"]) == str(room)]
            for r in sorted(mine, key=lambda r: str(r["DT"]), reverse=True):
                dt = str(r["DT"])
                try:
                    label = datetime.strptime(dt, "%Y%m%d%H%M%S").strftime("%Y-%m-%d   %H:%M:%S")
                except ValueError:
                    label = dt
                iid = self.tree.insert("", "end", values=(label,))
                self.paths[iid] = os.path.join(VIDEO_DIR, dt + ".avi")
            if self.player:
                self.msg.config(text="%d recording(s). Select one to play." % len(mine) if mine else "No recordings yet.")
        self.controller.run_bg(work, done)

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel or not self.player:
            return
        path = self.paths.get(sel[0])
        if not path or not os.path.exists(path):
            self.msg.config(text="Video file not found: %s" % path)
            return
        self.msg.config(text=os.path.basename(path))
        self.player.load(path)
        self.player.play()

    def delete_all(self):
        if not messagebox.askyesno("Confirmation", "Do you want to DELETE all RECORD DATA of room %d?" % self.room):
            return
        room = self.room
        self.controller.run_bg(lambda: api("/admin/deleterecord.php", RECORDID=room_arg(room)),
                               lambda _, error: messagebox.showerror("Delete", str(error)) if error else self.reload())


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
