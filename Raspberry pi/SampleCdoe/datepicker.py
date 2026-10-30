import tkinter as tk
from tkcalendar import DateEntry

root = tk.Tk()
cal = DateEntry(root, selectmode='day', date_pattern='mm-dd-yyyy')
cal.pack(padx=10, pady=10)

def get_date():
    print("test")
    print(cal.get_date())

tk.Button(root, text="Get Date", command=get_date).pack(pady=10)
root.mainloop()
