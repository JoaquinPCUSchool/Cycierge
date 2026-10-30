picture = "/home/pi/Desktop/SourceCode/BG/bgSplash.gif"
from Tkinter import *
import os
width = 0
def timer () :
    global width
    width = width + 1
    if width == 300 :
        print "END"
        Main.withdraw()
        os.system('python /home/pi/Desktop/SourceCode/Main.py')
    Main.after(5, timer)
Main = Tk ()
bgSplash = PhotoImage(file = picture)
Label(Main, image = bgSplash).pack()
Main.wm_attributes('-type', 'splash')
timer()
Main.mainloop()

