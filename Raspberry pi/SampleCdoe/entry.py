import tkinter as tk
from tkinter import messagebox

def open_login_popup():
    # Create the popup window
    login_win = tk.Toplevel(root)
    login_win.title("Login")
    login_win.geometry("300x350")
    
    # Make it modal (blocks main window)
    login_win.transient(root)
    login_win.grab_set()

    # Username
    tk.Label(login_win, text="Username:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    user_entry = tk.Entry(login_win)
    user_entry.grid(row=0, column=1, padx=10, pady=10)

    # Password
    tk.Label(login_win, text="Password:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    pass_entry = tk.Entry(login_win, show="*")
    pass_entry.grid(row=1, column=1, padx=10, pady=10)

    def validate():
        username = user_entry.get()
        password = pass_entry.get()
        
        # Replace with actual authentication logic
        if username == "admin" and password == "1234":
            messagebox.showinfo("Success", "Login Successful!")
            login_win.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    # Login Button
    tk.Button(login_win, text="Login", command=validate).grid(row=2, column=0, columnspan=2, pady=10)

# Main Application
root = tk.Tk()
root.title("Main Window")
root.geometry("400x300")

tk.Button(root, text="Open Login", command=open_login_popup).pack(pady=20)

root.mainloop()
