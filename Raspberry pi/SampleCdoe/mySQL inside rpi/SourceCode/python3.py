from tkinter import *
#import tkMessageBox
import MySQLdb
import ttk


db = MySQLdb.connect("localhost", "admin", "12345678", "accountDB")
curs=db.cursor()


# ************************************************************************************
# ************************************************************************************

class Main(Tk):
     def __init__(self, *args, **kwargs):
          Tk.__init__(self, *args, **kwargs)
          
          ## **************************************************************************
          ## *****  GUI BACKGROUND  ***************************************************
          self.BgPlain =           PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/bgPlain.gif")
          self.Bg =                PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/BGbackGround.gif")
          self.BgReg =             PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/bgReg.gif")
          
          self.BgbtnX =            PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnX.gif")
          self.BgbtnLogin =        PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnLogin.gif")
          self.BgbtnEdit =         PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnEdit.gif")
          self.BgbtnDelete =       PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnDelete.gif")
          self.BgbtnBack =         PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnBack.gif")
          self.BgbtnRegister =     PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnSave.gif")
          self.BgbtnLogout =     PhotoImage(file = "/home/pi/Desktop/SourceCode/BG/btnLogout.gif")
          ## **************************************************************************
          
          container = Frame(self)
          container.pack(side="top", fill="both", expand=True)
          container.grid_rowconfigure(0, weight=1)
          container.grid_columnconfigure(0, weight=1)
          
          self.frames = {}
          for F in (StartPage, Register, Data):      # FRAME *************
               page_name = F.__name__
               frame = F(parent=container, controller=self)
               self.frames[page_name] = frame
               frame.grid(row=0, column=0, sticky="nsew")

          self.show_frame("StartPage")

     def show_frame(self, page_name):
          frame = self.frames[page_name]
          frame.tkraise()


class StartPage(Frame):
     def __init__(self, parent, controller):
          global app
          global pwordVar, unameVar
          global txtReg
          Frame.__init__(self, parent)
          self.controller = controller

          def exitFunc () :
               app.destroy()

          def txtpwordFunc(event):
               global unameVar
               txtpword.delete(0, "end")
               txtpword.configure(show = '*')
               if unameVar.get() == "" :
                    unameVar.set('username')
               return None

          def txtUnameFunc(event):
               global pwordVar
               txtUname.delete(0, "end")
               if pwordVar.get() == "" :
                    txtpword.configure(show = '')
                    pwordVar.set('password')
               return None

          def click_link(event):
               global saveReg
               
               saveReg = 1         ## identification for register user
               controller.show_frame('Register')
               txtReg.place_forget()

          def LoginFunc () :
               global pwordVar, unameVar
               flag = 0
               curs.execute ("SELECT * FROM tblData")
               for reading in curs.fetchall():
                    if str(unameVar.get()) == str(reading[1]) and str(pwordVar.get()) == str(reading[2]) :
                         print ("get")
                         flag = 1
                         break
               if flag == 1:
                    txtReg.place_forget()
                    updateDatabase()
                    controller.show_frame('Data')
               else :
                    tkinter.messagebox.showerror("Error!", "Invalid Account !")






          Label(self, image = controller.Bg).pack()

          unameVar = StringVar()
          unameVar.set('username')
          txtUname = Entry(self, text = unameVar, justify = "center", foreground="gray", font = ("", 20, "bold"))
          txtUname.bind("<Button-1>", txtUnameFunc)
          txtUname.place(x = 280, y = 131, width = 250, height = 40)

          pwordVar = StringVar()
          pwordVar.set('password')
          txtpword = Entry(self, text = pwordVar, justify = "center", foreground="gray", font = ("", 20, "bold"))
          txtpword.bind("<Button-1>", txtpwordFunc)
          txtpword.place(x = 280 , y = 198, width = 250, height = 40)

          txtReg = Label(text="Not a member? Register Now !", foreground="#ffffff", bg = "#00436f")
          txtReg.bind("<1>", click_link)
          txtReg.place(x = 305, y = 400)

          btnLogin = Button(self, image = controller.BgbtnLogin, command = LoginFunc)
          btnLogin.place(x = 335, y = 275)


class Register(Frame):
     def __init__(self, parent, controller):
          global regNameVar, regPwordVar, regUnameVar
          global txtRegname
          
          Frame.__init__(self, parent)
          self.controller = controller

          def backFunc () :
               global txtReg
               controller.show_frame('StartPage')
               txtReg.place(x = 305, y = 400)

          def registerFunc () :
               global regNameVar, regPwordVar, regUnameVar
               global saveReg

               if saveReg == 1 :
               
                    if regNameVar.get() == "" or regPwordVar.get() == "" or regUnameVar.get() == "":
                         tkMessageBox.showerror("Error!", "Fill all information !")
                    else :
                         vName = str(regNameVar.get())
                         vUname = str(regPwordVar.get())
                         vPass = str(regUnameVar.get())
                         
                         try:
                              curs.execute ("""INSERT INTO tblData values(%s, %s, %s)""", (regNameVar.get(), regPwordVar.get(), regUnameVar.get()))
                              db.commit()
                              print ("Data committed")
                              regNameVar.set("")
                              regPwordVar.set("")
                              regUnameVar.set("")
                              tkMessageBox.showinfo("", "Registration Success !!")
                              
                              controller.show_frame("StartPage")

                         except:
                             print ("Error: the database is being rolled back")
                             db.rollback()
               elif saveReg == 2 :
                    curs.execute ("""UPDATE tblData SET uname=%s, password=%s WHERE name=%s""", (str(regUnameVar.get()), str(regPwordVar.get()), str(regNameVar.get())))
                    db.commit()
                    updateDatabase()
                    regNameVar.set("")
                    regPwordVar.set("")
                    regUnameVar.set("")
                    controller.show_frame("Data")
                    




          Label(self, image = controller.BgReg).pack()

          regNameVar = StringVar ()
          txtRegname = Entry(self, text = regNameVar, justify = "center", foreground="gray", font = ("", 15, "bold"))
          txtRegname.place(x = 325 , y = 135, width = 320, height = 30)

          regUnameVar = StringVar ()
          txtregUname = Entry(self, text = regUnameVar, justify = "center", foreground="gray", font = ("", 15, "bold"))
          txtregUname.place(x = 325 , y = 205, width = 320, height = 30)

          regPwordVar = StringVar ()
          txtRegPword = Entry(self, text = regPwordVar, justify = "center", foreground="gray", font = ("", 15, "bold"))
          txtRegPword.place(x = 325 , y = 274, width = 320, height = 30)

          
          btnReg = Button(self, image = controller.BgbtnRegister, command = registerFunc)
          btnReg.place(x = 250, y = 370)

          btnBack = Button(self, image = controller.BgbtnBack, command = backFunc)
          btnBack.place(x = 450, y = 370)

class Data(Frame):
     def __init__(self, parent, controller):
          global select
          global tree
          global txtSearch, searchVar
          
          Frame.__init__(self, parent)
          self.controller = controller
          
          def editFunc() :
               global regNameVar, regPwordVar, regUnameVar
               global saveReg
               global txtRegname
               
               saveReg = 2         ## identification for edit user
          
               item = tree.selection()[0]
               print(tree.item(item,"text"))

               for nm in tree.selection():
                    UserID, Password = tree.item(nm, 'values')
                    print (UserID,Password)
                    

               regNameVar.set(str(tree.item(item,"text")))
               regUnameVar.set(str(UserID))
               regPwordVar.set(str(Password))
               txtRegname.config(state = 'readonly')

               controller.show_frame('Register')

          def deleteFunc () :
               item = tree.selection()[0]
               print(tree.item(item,"text"))
               
               curs.execute ("""DELETE FROM tblData WHERE name = %s""", (str(tree.item(item,"text"))))
               db.commit()
               updateDatabase()
                             
                    

          def logoutFunc () :
               global pwordVar, unameVar
               global txtReg

               pwordVar.set("")
               unameVar.set("")

               Result = tkMessageBox.askyesno("Log-out", "Are you sure you want to log-out?")

               print (Result)
               if Result == False :
                    pass
               else :
                    txtReg.place(x = 305, y = 400)
                    controller.show_frame('StartPage')

          def searchFunc () :
               global txtSearch
               global tree
               global searchVar
               
               if txtSearch.get() != "" :
                    tree.delete(*tree.get_children())
                    curs.execute ("SELECT * FROM tblData")
                    for reading in curs.fetchall():
                         if str(reading[0]) == str(txtSearch.get()) : 
                              tree.insert('', 'end', text=str(reading[0]),  values=(str(reading[1]), str(reading[2])))
                    
               searchVar.set("")



          Label(self, image = controller.BgPlain).pack()

          searchVar = StringVar()
          txtSearch = Entry(self, text = searchVar)
          txtSearch.place(x = 10, y = 5)

          btnSearch = Button(self, text = "search", font = ("Helvetica", 7), command = searchFunc)
          btnSearch.place(x = 180, y = 5, width = 40, height = 20)


          btnEdit = Button(self, image = controller.BgbtnEdit, command = editFunc)
          btnEdit.place(x = 200,  y= 150)

          btnDelete = Button(self, image = controller.BgbtnDelete, command = deleteFunc)
          btnDelete.place(x = 450, y = 150)

          tree = ttk.Treeview(self, columns=('UserID', 'Password'))

          tree.column('#0', stretch=YES)
          tree.column('#1', stretch=YES)
          tree.column('#2', stretch=YES)

          tree.heading('#0', text='Name')
          tree.heading('#1', text='UserID')
          tree.heading('#2', text='Password')
          
          tree.place(x = 110, y = 200)

          btnLogout = Button(self,image = controller.BgbtnLogout, command = logoutFunc)
          btnLogout.place(x = 340, y = 425)

          



def updateDatabase():
     global tree
     tree.delete(*tree.get_children())
     curs.execute ("SELECT * FROM tblData")
     for reading in curs.fetchall():
          tree.insert('', 'end', text=str(reading[0]),  values=(str(reading[1]), str(reading[2])))



if __name__ == "__main__":
    app = Main()
    app.title('Sample Program')
    updateDatabase()
    app.mainloop()
