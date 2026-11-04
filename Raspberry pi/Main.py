from tkinter import *
from PIL import Image as Img
from PIL import ImageTk
import cv2
import numpy as np
import tkinter.ttk as tableview
from datetime import datetime
from tkVideoPlayer import TkinterVideo
import threading
import requests
import json
import time
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime

record1 = 0
recordflag1 = 0

record2 = 0
recordflag2 = 0

btnflag = 0;


# ************************************************************************************
# ************************************************************************************

URL1 = "http://192.168.0.112/stream"
URL2 = "http://192.168.0.122/stream"
cap1 = cv2.VideoCapture(URL1)
cap2 = cv2.VideoCapture(URL2)



class SampleApp(Tk):

     def __init__(self, *args, **kwargs):
          Tk.__init__(self, *args, **kwargs)

          
          
          container = Frame(self)
          container.pack(side="top", fill="both", expand=True)
          container.grid_rowconfigure(0, weight=1)
          container.grid_columnconfigure(0, weight=1)
          
          self.frames = {}
          for F in (StartPage, Main, showRecord):      # FRAME *************
               page_name = F.__name__
               frame = F(parent=container, controller=self)
               self.frames[page_name] = frame
               frame.grid(row=0, column=0, sticky="nsew")
               
          self.show_frame("Main")

     def show_frame(self, page_name):
          '''Show a frame for the given page name'''
          frame = self.frames[page_name]
          frame.tkraise()


class StartPage(Frame):
     def __init__(self, parent, controller):
          Frame.__init__(self, parent)
          self.controller = controller


class Main(Frame):
     def __init__(self, parent, controller):
          global displayCam1
          global displayCam2
          global tbllogs1, tbllogs2
          global tblRecord2
          
          Frame.__init__(self, parent)
          self.controller = controller

          

          
          #############################################################################################
          def btn1Func():
              login_win = Toplevel(app)
              login_win.title("Login")
              login_win.geometry("300x450")
              
              login_win.transient(app)
              login_win.grab_set()

              #USERNAME
              Label(login_win, text="USERNAME:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
              usernamevar = Entry(login_win)
              usernamevar.grid(row=0, column=1, padx=10, pady=10)
              #USERID
              Label(login_win, text="USERID:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
              useridvar = Entry(login_win)
              useridvar.grid(row=1, column=1, padx=10, pady=10)
              #USERPASS
              Label(login_win, text="USERPASS:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
              userpassvar = Entry(login_win)
              userpassvar.grid(row=2, column=1, padx=10, pady=10)
              #USERPHONE
              Label(login_win, text="USERPHONE:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
              userphonevar = Entry(login_win)
              userphonevar.grid(row=3, column=1, padx=10, pady=10)
              #USERMONTH
              Label(login_win, text="MONTH:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
              usermonthvar = Entry(login_win)
              usermonthvar.grid(row=4, column=1, padx=10, pady=10)
              #USERDAY
              Label(login_win, text="DAY:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
              userdayvar = Entry(login_win)
              userdayvar.grid(row=5, column=1, padx=10, pady=10)
              #USERYEAR
              Label(login_win, text="YEAR:").grid(row=6, column=0, padx=10, pady=10, sticky="e")
              useryearvar = Entry(login_win)
              useryearvar.grid(row=6, column=1, padx=10, pady=10)


              def validate():
                  namevar = usernamevar.get()
                  idvar = useridvar.get()
                  passvar = userpassvar.get()
                  phonevar = userphonevar.get()
                  monthvar = usermonthvar.get()
                  dayvar = userdayvar.get()
                  yearvar = useryearvar.get()
                  datevar = str(yearvar) + "-" + str(monthvar) + "-" + str(dayvar)
                  now = datetime.now()
                  timenowvar = str(now.strftime("%H:%M"))
     
                  if namevar == "" or idvar == "" or passvar == "" or phonevar == "" or monthvar == "" or dayvar == "" or yearvar == "":
                       messagebox.showerror("Error", "Invalid credentials")
                  else:
                       req = requests.get("http://localhost/cycierge/user/updateuser.php?USERID='"+str(idvar)+"'&USERPASS='"+str(passvar)+"'&USERNAME='"+str(namevar)+"'&USERPHONE='"+str(phonevar)+"'&USERDATE='"+str(datevar)+"'&USERTIME='"+str(timenowvar)+"'&ID='1'")
                       if req:
                             print ('Database Updated')
                       else:
                             print ('Failed')
                       

                       
                       login_win.destroy()
              Button(login_win, text="OK", command=validate, bg = 'skyblue').grid(row=7, column=0, columnspan=2, pady=30, ipadx=30)

          def btn1bFunc () :
               global btnflag
               global tblRecord1
               btnflag = 1;
               tblRecord1.delete(*tblRecord1.get_children())

               data = requests.get("http://localhost/cycierge/user/getrecord.php")
               #print data.text
               parseData = json.loads(data.text)

               for row in range(0, len(parseData)):

                   if (str(parseData[row]["RECORDID"]) == "1") :
                        tblRecord1.insert('', 'end', text="",
                                  values=(str(parseData[row]["DT"])))
               controller.show_frame("showRecord")

          def btn1cFunc () :
             req = requests.get("http://localhost/cycierge/admin/unlock.php?USERLOCK='1'&ID='1'")
             if req:
                  print ('Database Updated')

             else:
                  print ('Failed')

             now = datetime.now()

             # Print formatted time (HH:MM:SS)
             print("Current Time =", now.strftime("%H:%M"))
             timenowvar = str(now.strftime("%H:%M"))
             print(timenowvar)
             datenowvar = str(now.strftime("%Y-%M-%d"))
             print(timenowvar)

             req = requests.get("http://localhost/cycierge/admin/insertactivity.php?LOGSID='1'&LOGSDATE='"+str(datenowvar)+"'&LOGSTIME='"+str(timenowvar)+"'&LOGSACTIVITY='Admin Unlock Door 1'")
             if req:
                  print ('Database Updated')
             else:
                  print ('Failed')

          ###################################################################################################################################
          def btn2Func():
              login_win = Toplevel(app)
              login_win.title("Login")
              login_win.geometry("300x450")
              
              login_win.transient(app)
              login_win.grab_set()

              #USERNAME
              Label(login_win, text="USERNAME:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
              usernamevar = Entry(login_win)
              usernamevar.grid(row=0, column=1, padx=10, pady=10)
              #USERID
              Label(login_win, text="USERID:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
              useridvar = Entry(login_win)
              useridvar.grid(row=1, column=1, padx=10, pady=10)
              #USERPASS
              Label(login_win, text="USERPASS:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
              userpassvar = Entry(login_win)
              userpassvar.grid(row=2, column=1, padx=10, pady=10)
              #USERPHONE
              Label(login_win, text="USERPHONE:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
              userphonevar = Entry(login_win)
              userphonevar.grid(row=3, column=1, padx=10, pady=10)
              #USERMONTH
              Label(login_win, text="MONTH:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
              usermonthvar = Entry(login_win)
              usermonthvar.grid(row=4, column=1, padx=10, pady=10)
              #USERDAY
              Label(login_win, text="DAY:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
              userdayvar = Entry(login_win)
              userdayvar.grid(row=5, column=1, padx=10, pady=10)
              #USERYEAR
              Label(login_win, text="YEAR:").grid(row=6, column=0, padx=10, pady=10, sticky="e")
              useryearvar = Entry(login_win)
              useryearvar.grid(row=6, column=1, padx=10, pady=10)


              def validate():
                  namevar = usernamevar.get()
                  idvar = useridvar.get()
                  passvar = userpassvar.get()
                  phonevar = userphonevar.get()
                  monthvar = usermonthvar.get()
                  dayvar = userdayvar.get()
                  yearvar = useryearvar.get()
                  datevar = str(yearvar) + "-" + str(monthvar) + "-" + str(dayvar)
                  now = datetime.now()
                  timenowvar = str(now.strftime("%H:%M"))
     
                  if namevar == "" or idvar == "" or passvar == "" or phonevar == "" or monthvar == "" or dayvar == "" or yearvar == "":
                       messagebox.showerror("Error", "Invalid credentials")
                  else:
                       req = requests.get("http://localhost/cycierge/user/updateuser.php?USERID='"+str(idvar)+"'&USERPASS='"+str(passvar)+"'&USERNAME='"+str(namevar)+"'&USERPHONE='"+str(phonevar)+"'&USERDATE='"+str(datevar)+"'&USERTIME='"+str(timenowvar)+"'&ID='2'")
                       if req:
                             print ('Database Updated')
                       else:
                             print ('Failed')
                       login_win.destroy()
              Button(login_win, text="OK", command=validate, bg = 'skyblue').grid(row=7, column=0, columnspan=2, pady=30, ipadx=30)

          def btn2bFunc () :
               global btnflag
               global tblRecord1
               btnflag = 2;
               tblRecord1.delete(*tblRecord1.get_children())

               data = requests.get("http://localhost/cycierge/user/getrecord.php")
               #print data.text
               parseData = json.loads(data.text)

               for row in range(0, len(parseData)):
                   if (str(parseData[row]["RECORDID"]) == "2") :
                        tblRecord1.insert('', 'end', text="",
                                  values=(str(parseData[row]["DT"])))
               controller.show_frame("showRecord")

          def btn2cFunc () :
             req = requests.get("http://localhost/cycierge/admin/unlock.php?USERLOCK='1'&ID='2'")
             if req:
                  print ('Database Updated')

             else:
                  print ('Failed')
             now = datetime.now()

             # Print formatted time (HH:MM:SS)
             print("Current Time =", now.strftime("%H:%M"))
             timenowvar = str(now.strftime("%H:%M"))
             print(timenowvar)
             datenowvar = str(now.strftime("%Y-%M-%d"))
             print(timenowvar)

             req = requests.get("http://localhost/cycierge/admin/insertactivity.php?LOGSID='2'&LOGSDATE='"+str(datenowvar)+"'&LOGSTIME='"+str(timenowvar)+"'&LOGSACTIVITY='Admin Unlock Door 2'")
             if req:
                  print ('Database Updated')
             else:
                  print ('Failed')


               
          
          maincanva = Canvas(self, bg='white')
          Label(maincanva, text = "ROOM # 1", font = ('',20,'bold')).place(relx=0.25, rely=0.05, anchor='center')
          
          displayCam1 = Label(maincanva)
          displayCam1.place(relx=0.25, rely=0.27, anchor='center',h=300, w=400)

          tbllogs1 = tableview.Treeview(maincanva, columns=('DATE', 'TIME', 'ACTIVITY'))

          tbllogs1.column('#0', width=0)
          tbllogs1.column('#1', width=100)
          tbllogs1.column('#2', width=100)
          tbllogs1.column('#3', width=100)

          tbllogs1.heading('#0', text='')
          tbllogs1.heading('#1', text='DATE')
          tbllogs1.heading('#2', text='TIME')
          tbllogs1.heading('#3', text='ACTIVITY')
          
          tbllogs1.place(relx=0.245, rely=0.65, anchor='center',h=300, w=500)

          btncanva1 = Canvas(self, bg='white')

          btn1a = Button(btncanva1, text = "NEW USER", bg = 'skyblue',
                        command=btn1Func)
          btn1a.place(relx=0.17, rely=0.5, anchor='center',h=40, w=150)

          btn1b = Button(btncanva1, text = "RECORDING", bg = 'skyblue',
                        command = btn1bFunc)
          btn1b.place(relx=0.5, rely=0.5, anchor='center',h=40, w=150)

          btn1c = Button(btncanva1, text = "UNLOCK", bg = 'skyblue',
                        command = btn1cFunc)
          btn1c.place(relx=0.83, rely=0.5, anchor='center',h=40, w=150)

          btncanva1.place(relx=0.25, rely=0.9, anchor='center',h=80, w=500)



          Label(maincanva, text = "ROOM # 2", font = ('',20,'bold')).place(relx=0.75, rely=0.05, anchor='center')
          displayCam2 = Label(maincanva)
          displayCam2.place(relx=0.75, rely=0.27, anchor='center',h=300, w=400)
          ####
          tbllogs2 = tableview.Treeview(maincanva, columns=('DATE', 'TIME', 'ACTIVITY'))
          tbllogs2.column('#0', width=0)
          tbllogs2.column('#1', width=100)
          tbllogs2.column('#2', width=100)
          tbllogs2.column('#3', width=100)

          tbllogs2.heading('#0', text='')
          tbllogs2.heading('#1', text='DATE')
          tbllogs2.heading('#2', text='TIME')
          tbllogs2.heading('#3', text='ACTIVITY')
          tbllogs2.place(relx=0.755, rely=0.65, anchor='center',h=300, w=500)
          ####
          btncanva2 = Canvas(self, bg='white')
          btn2a = Button(btncanva2, text = "NEW USER", bg = 'skyblue',
                        command = btn2Func)
          btn2a.place(relx=0.17, rely=0.5, anchor='center',h=40, w=150)

          btn2b = Button(btncanva2, text = "RECORDING", bg = 'skyblue',
                        command = btn2bFunc)
          btn2b.place(relx=0.5, rely=0.5, anchor='center',h=40, w=150)

          btn2c = Button(btncanva2, text = "UNLOCK", bg = 'skyblue',
                        command = btn2cFunc)
          btn2c.place(relx=0.83, rely=0.5, anchor='center',h=40, w=150)
          btncanva2.place(relx=0.75, rely=0.9, anchor='center',h=80, w=500)

          maincanva.place(relx=0.5, rely=0.5, anchor='center',h=850, w=1400)

          


class showRecord(Frame):
     def __init__(self, parent, controller):
          Frame.__init__(self, parent)
          self.controller = controller
          global displayVideo
          global tblRecord1


          def backFunc () :
               controller.show_frame("Main")

          def deleteFunc () :
               global btnflag


               result = messagebox.askyesno("Confirmation", "Do you want to DELETE all RECORD DATA?")
               if result:
                    req = requests.get("http://localhost/cycierge/admin/deleterecord.php?RECORDID='" + str(btnflag) + "'")
                    if req:
                         print ('Database Updated')
                    else:
                         print ('Failed')
                    controller.show_frame("showRecord")
               else:
                    pass
               
               
                         

          def treeSelection (item) :
               global displayVideo
               global tblRecord1, item_text
               for item in tblRecord1.selection () :
                    item_text = tblRecord1.item(item, 'values')
                    print (item_text[0])
                    displayVideo.load("/home/pi/Desktop/SourceCode/VideoCapture/" + str(item_text[0])+".avi")
                    displayVideo.play()
               
          maincanva = Canvas(self, bg='white')
          displayVideo = TkinterVideo(maincanva)
          displayVideo.place(relx=0.6, rely=0.5, anchor='center',h=300, w=400)

          tblRecord1 = tableview.Treeview(maincanva, columns=('DATE : TIME'))

          tblRecord1.column('#0', width=0)
          tblRecord1.column('#1', width=200)

          tblRecord1.heading('#0', text='')
          tblRecord1.heading('#1', text='DATE : TIME')
          tblRecord1.bind('<<TreeviewSelect>>', treeSelection)
          tblRecord1.place(relx=0.3, rely=0.5, anchor='center',h=500, w=220)


          btndelete = Button(maincanva, text = "DELETE DATA", bg="skyblue",
                        command = deleteFunc)
          btndelete.place(relx=0.3, rely=0.85, anchor='center',h=50, w=150)

          btn3 = Button(maincanva, text = "BACK", bg="skyblue",
                        command = backFunc)
          btn3.place(relx=0.5, rely=0.85, anchor='center',h=50, w=150)

          maincanva.place(relx=0.5, rely=0.5, anchor='center',h=850, w=1400)


#############################################################################################################
############################ S P E C I A L    F U N C T I O N ###############################################
#############################################################################################################

def getdatafromdb () :

     global tbllogs1, tbllogs2

     tbllogs1.delete(*tbllogs1.get_children())
     tbllogs2.delete(*tbllogs2.get_children())

     data = requests.get("http://localhost/cycierge/user/getlogs.php")
     #print data.text
     parseData = json.loads(data.text)

     for row in range(0, len(parseData)):
         if (str(parseData[row]["LOGSID"]) == "1") :
              tbllogs1.insert('', 'end', text="",
                        values=(str(parseData[row]["LOGSDATE"]),
                                str(parseData[row]["LOGSTIME"]),
                                str(parseData[row]["LOGSACTIVITY"])))
         if (str(parseData[row]["LOGSID"]) == "2") :
              tbllogs2.insert('', 'end', text="",
                        values=(str(parseData[row]["LOGSDATE"]),
                                str(parseData[row]["LOGSTIME"]),
                                str(parseData[row]["LOGSACTIVITY"])))
     app.after(1000, getdatafromdb)



     
          
class shoCamera1(threading.Thread):
     def __init__(self):
         super(shoCamera1, self).__init__()
         self.setDaemon(True)

     def run(self):
         global rcvvar, rcvmsgvar
         while True:
               global displayCam1
               global record1, recordflag1
               global out
               try:
                    ret, frame = cap1.read()
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    data = requests.get("http://localhost/cycierge/user/getdata.php")
                    #print data.text
                    parseData = json.loads(data.text)

                    for row in range(0, len(parseData)):
                        if (str(parseData[row]["ID"]) == "1") :
                              if (str(parseData[row]["USERCAM"]) == "1") :
                                   if (recordflag1 == 0) :
                                        now = datetime.now()
                                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                                        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                        cameranamevar = str(now.strftime("%Y%m%d%H%M%S"))
                                        out = cv2.VideoWriter('/home/pi/Desktop/SourceCode/VideoCapture/' + cameranamevar +'.avi', fourcc, 5, (frame_width, frame_height))
                                        req = requests.get("http://localhost/cycierge/admin/insertlogs.php?RECORDID='1'&DT='" + cameranamevar + "'")
                                        if req:
                                              print ('Database Updated')

                                        else:
                                              print ('Failed')
                                        recordflag1 = 1
                                   if (recordflag1 == 1) :
                                        print ("recording")
                                        out.write(frame)
                                        time.sleep
                              else :
                                   if (recordflag1 == 1) :
                                        recordflag1 = 0
                                        print ("release")
                                        out.release()
                    frame=cv2.flip(rgb,1)
                    img = Img.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    displayCam1.imgtk = imgtk
                    displayCam1.configure(image=imgtk)
               except :
                    pass
               
showcam1 = shoCamera1()
showcam1.start()




          
class shoCamera2(threading.Thread):
     def __init__(self):
         super(shoCamera2, self).__init__()
         self.setDaemon(True)

     def run(self):
         global rcvvar, rcvmsgvar
         while True:
               global displayCam2
               global record2, recordflag2
               global out
               try:
                    ret, frame = cap2.read()
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    data = requests.get("http://localhost/cycierge/user/getdata.php")
                    #print data.text
                    parseData = json.loads(data.text)

                    for row in range(0, len(parseData)):
                        if (str(parseData[row]["ID"]) == "2") :
                              if (str(parseData[row]["USERCAM"]) == "1") :
                                   if (recordflag2 == 0) :
                                        now = datetime.now()
                                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                                        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                        cameranamevar = str(now.strftime("%Y%m%d%H%M%S"))
                                        out = cv2.VideoWriter('/home/pi/Desktop/SourceCode/VideoCapture/' + cameranamevar +'.avi', fourcc, 5, (frame_width, frame_height))
                                        req = requests.get("http://localhost/cycierge/admin/insertlogs.php?RECORDID='2'&DT='" + cameranamevar + "'")
                                        if req:
                                              print ('Database Updated')

                                        else:
                                              print ('Failed')
                                        recordflag2 = 1
                                   if (recordflag2 == 1) :
                                        print ("recording")
                                        out.write(frame)
                                        time.sleep
                              else :
                                   if (recordflag2 == 1) :
                                        recordflag2 = 0
                                        print ("release")
                                        out.release()
                    frame=cv2.flip(rgb,1)
                    img = Img.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    displayCam2.imgtk = imgtk
                    displayCam2.configure(image=imgtk)
               except :
                    pass
               
showcam2 = shoCamera2()
showcam2.start()








if __name__ == "__main__":
    app = SampleApp()
    getdatafromdb()
    app.title("Sample GUI")
    app.minsize(1440,900)
    app.mainloop()
