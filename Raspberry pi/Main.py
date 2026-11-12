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
from report_view import showReport   # Administrative Report page (report_view.py, same folder)

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



BASE = "http://localhost/cycierge"


def tenant_dialog(parent, room, new=False):
     """Tenant dialog, same fields and rules as the Android admin app.
     Edit tenant: Name / Username / New password (blank keeps the current one).
     New tenant : empty form, password required; check-in is set to now and "time stayed" restarts."""
     try:
          rows = requests.get(BASE + "/user/getdata.php", timeout=5).json()
     except Exception as e:
          messagebox.showerror("Error", "Couldn't load the tenant: " + str(e))
          return
     cur = next((r for r in rows if str(r.get("ID")) == str(room)), {})
     old_name = (cur.get("USERNAME") or "").strip()

     if new and old_name:
          if not messagebox.askyesno("New tenant", "Room " + str(room) + " is occupied by " + old_name +
                                     ".\nTheir stay ends now and time stayed restarts for the new tenant.\n\nContinue?"):
               return

     win = Toplevel(parent)
     win.title("New tenant" if new else "Edit tenant")
     win.transient(parent)
     win.grab_set()
     win.resizable(False, False)

     name_v = StringVar(value="" if new else (cur.get("USERNAME") or ""))
     uid_v = StringVar(value="" if new else (cur.get("USERID") or ""))
     pass_v = StringVar()

     Label(win, text=("New tenant - room no. " if new else "Edit tenant - room no. ") + str(room),
           font=('', 16, 'bold')).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 5))
     Label(win, text="Name of tenant:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
     name_e = Entry(win, textvariable=name_v, width=28)
     name_e.grid(row=1, column=1, padx=10, pady=10)
     Label(win, text="Username (tenant login):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
     Entry(win, textvariable=uid_v, width=28).grid(row=2, column=1, padx=10, pady=10)
     Label(win, text="Password:" if new else "New password:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
     Entry(win, textvariable=pass_v, width=28, show="*").grid(row=3, column=1, padx=10, pady=10)
     Label(win, fg="gray", text=("Check-in time is set to now; time stayed restarts at 0." if new
                                 else "Leave the password blank to keep the current one.")
           ).grid(row=4, column=0, columnspan=2, padx=10)
     err = Label(win, text="", fg="red")
     err.grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 0))

     def save():
          name, uid, pw = name_v.get().strip(), uid_v.get().strip(), pass_v.get()
          if not name or not uid or (new and not pw):
               err.config(text="Name, username and password are required" if new else "Name and username are required")
               return
          try:
               r = requests.post(BASE + ("/user/newtenant.php" if new else "/user/edituser.php"), timeout=5,
                                 json={"room": room, "name": name, "userid": uid, "password": pw})
               r.raise_for_status()
          except Exception as e:
               err.config(text="Couldn't save: " + str(e))
               return
          win.destroy()

     Button(win, text="CHECK IN" if new else "SAVE", command=save, bg='skyblue').grid(row=6, column=0, columnspan=2, pady=(15, 5), ipadx=40)
     Button(win, text="CANCEL", command=win.destroy).grid(row=7, column=0, columnspan=2, pady=(0, 20), ipadx=33)
     win.bind("<Return>", lambda e: save())
     name_e.focus_set()


class SampleApp(Tk):

     def __init__(self, *args, **kwargs):
          Tk.__init__(self, *args, **kwargs)

          
          
          container = Frame(self)
          container.pack(side="top", fill="both", expand=True)
          container.grid_rowconfigure(0, weight=1)
          container.grid_columnconfigure(0, weight=1)
          
          self.frames = {}
          for F in (StartPage, Main, showRecord, showReport):      # FRAME *************
               page_name = F.__name__
               frame = F(parent=container, controller=self)
               self.frames[page_name] = frame
               frame.grid(row=0, column=0, sticky="nsew")
               
          self.show_frame("Main")

     def show_frame(self, page_name):
          '''Show a frame for the given page name'''
          frame = self.frames[page_name]
          frame.tkraise()
          if hasattr(frame, 'on_show'):
               frame.on_show()


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
              tenant_dialog(controller, 1)

          def btn1nFunc():
              tenant_dialog(controller, 1, new=True)

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
             datenowvar = str(now.strftime("%Y-%m-%d"))
             print(timenowvar)

             req = requests.get("http://localhost/cycierge/admin/insertactivity.php?LOGSID='1'&LOGSDATE='"+str(datenowvar)+"'&LOGSTIME='"+str(timenowvar)+"'&LOGSACTIVITY='Admin Unlock Door 1'")
             if req:
                  print ('Database Updated')
             else:
                  print ('Failed')

          ###################################################################################################################################
          def btn2Func():
              tenant_dialog(controller, 2)

          def btn2nFunc():
              tenant_dialog(controller, 2, new=True)

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
             datenowvar = str(now.strftime("%Y-%m-%d"))
             print(timenowvar)

             req = requests.get("http://localhost/cycierge/admin/insertactivity.php?LOGSID='2'&LOGSDATE='"+str(datenowvar)+"'&LOGSTIME='"+str(timenowvar)+"'&LOGSACTIVITY='Admin Unlock Door 2'")
             if req:
                  print ('Database Updated')
             else:
                  print ('Failed')


               
          
          maincanva = Canvas(self, bg='white')
          btnReports = Button(maincanva, text = "REPORTS", bg = 'skyblue',
                        command = lambda: controller.show_frame("showReport"))
          btnReports.place(relx=0.5, rely=0.05, anchor='center', h=40, w=150)
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

          btn1a = Button(btncanva1, text = "EDIT TENANT", bg = 'skyblue',
                        command=btn1Func)
          btn1a.place(relx=0.125, rely=0.5, anchor='center',h=40, w=115)

          btn1n = Button(btncanva1, text = "NEW TENANT", bg = 'skyblue',
                        command = btn1nFunc)
          btn1n.place(relx=0.375, rely=0.5, anchor='center',h=40, w=115)

          btn1b = Button(btncanva1, text = "RECORDING", bg = 'skyblue',
                        command = btn1bFunc)
          btn1b.place(relx=0.625, rely=0.5, anchor='center',h=40, w=115)

          btn1c = Button(btncanva1, text = "UNLOCK", bg = 'skyblue',
                        command = btn1cFunc)
          btn1c.place(relx=0.875, rely=0.5, anchor='center',h=40, w=115)

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
          btn2a = Button(btncanva2, text = "EDIT TENANT", bg = 'skyblue',
                        command = btn2Func)
          btn2a.place(relx=0.125, rely=0.5, anchor='center',h=40, w=115)

          btn2n = Button(btncanva2, text = "NEW TENANT", bg = 'skyblue',
                        command = btn2nFunc)
          btn2n.place(relx=0.375, rely=0.5, anchor='center',h=40, w=115)

          btn2b = Button(btncanva2, text = "RECORDING", bg = 'skyblue',
                        command = btn2bFunc)
          btn2b.place(relx=0.625, rely=0.5, anchor='center',h=40, w=115)

          btn2c = Button(btncanva2, text = "UNLOCK", bg = 'skyblue',
                        command = btn2cFunc)
          btn2c.place(relx=0.875, rely=0.5, anchor='center',h=40, w=115)
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
                                        frame_width = int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
                                        frame_height = int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
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
                                        frame_width = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
                                        frame_height = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
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
