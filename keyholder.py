#! /usr/bin/python3
'''
Created on 11. mai 2012

@author: lars
'''

import tkinter.tix as Tix
import sqlite3
import time
import os
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


sqlitefilename = "keydatabase.sqlite"  # database name
database_schema = 'CREATE TABLE keys(\nkeyid INTEGER PRIMARY KEY,\nkeytag VARCHAR,\ntarget VARCHAR,\ndetails VARCHAR,\ncreatedate DATETIME)' # the setup for the database
location = "Some Location" #hard coded for now. To be included in a config table in the database at a later point

# checks if the sqlite database exists, and if it is properly set up. It expects path to  be the full path of the database file.
# if the file exists, but is not properly set up,  it returns false, without doing anything to the existing file. 
# If the existing file is properly set up, it returns true
def checkBase(path):
    if len(path):
        if os.path.isfile(path):
            base = sqlite3.connect(path)
            cursor = base.cursor()
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE tbl_name='keys'")
            except sqlite3.OperationalError:
                return(False)
            sql_list = list(cursor.fetchall())
            base.close()
            if len(sql_list):
                if sql_list[0][0] == database_schema:
                    return(True)
            else:
                return(False)
    return(False)

# creates a database. if successfull, it returns True. Else it returns False. It expects the filename to be  the  full  path of the file.
# It returns False if the file exists, and does not try to do anything to the database file.
# it checks if the database is properly set up, before returning true
def createBase(path):
    if os.path.isfile(path):
        return(checkBase(path))
    try:
        base = sqlite3.connect(path)
        cursor = base.cursor()
        cursor.execute(database_schema + ";")
        base.commit()
        base.close()
    except sqlite3.OperationalError:
        return(False)
    except sqlite3.DatabaseError:
        return(False)
    return(checkBase(path))

class AddKeyWindow(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self.master.titleframe.setTitle("Legg til nøkkel")
        self.addkeyframe = AddKeyFrame(self)
        self.resultframe = ResultFrame(self, "Nøkler som nylig er lagt til")
        self.updateResults()
        self.editkeyframe = None
        self.pack(side="left", fill="both", expand=True, anchor="nw")
        
    def updateResults(self):
        base = sqlite3.connect(sqlitefilename)
        c = base.cursor()
        keylist = []
        c.execute("SELECT keyid, keytag, target, details, createdate FROM keys ORDER BY keys.createdate DESC LIMIT 30")
        for each_item in c.fetchall():
            keylist.append(KeyItem(each_item[0],each_item[1],each_item[2],each_item[3],each_item[4]))
        c.close()
        base.close()
        self.resultframe.setList(keylist)
        
    def closeEdit(self):
        self.master.titleframe.setTitle("Legg til nøkkel")
        self.editkeyframe.destroy()
        self.editkeyframe = None
        self.addkeyframe.pack(side="top", fill="both", anchor="nw")
        self.updateResults()
        
    def openEdit(self, key):
        if self.editkeyframe:
            self.editkeyframe.destroy()
        self.master.titleframe.setTitle("Rediger nøkkel")
        self.addkeyframe.pack_forget()
        self.editkeyframe = EditKeyFrame(self, key)
        
class AddKeyFrame(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self["borderwidth"] = 2
        self["relief"] = "ridge"
        self.tagfield = Field(self, "Tag: ", 0, 0)
        self.shopfield = Field(self, "Butikk: ", 1, 0)
        self.detailfield = TextField(self, "Detaljer: ", 2, 0)
        self.detailfield.textfield.text.bind("<Tab>", self.tabText)
        self.addbutton = Tix.Button(self)
        self.addbutton["text"] = "Legg til nøkkel"
        self.addbutton["command"] = self.addKey
        self.addbutton.bind("<Tab>", self.tabButton)
        self.addbutton.grid(row=0, column=2)
        self.pack(side="top", fill="both", anchor="nw")
        self.tagfield.entry.focus_set()
        
    def addKey(self):
        if len(self.tagfield.getText()) + len(self.shopfield.getText()) + len(self.detailfield.getText()):
            base = sqlite3.connect(sqlitefilename)
            c = base.cursor()
            c.execute("INSERT INTO keys (keyid, keytag, target, details, createdate) VALUES(?, ?, ?, ?, ?)", (None, self.tagfield.getText(), self.shopfield.getText(), self.detailfield.getText().strip(), time.strftime("%Y-%m-%d %H:%M:%S.000")))
            base.commit()
            c.close()
            base.close()
            self.clearFields()
        self.master.updateResults()
        self.tagfield.entry.focus_set()
            
    def clearFields(self):
        self.tagfield.setText("")
        self.shopfield.setText("")
        self.detailfield.setText("")
        
    def tabButton(self, event=None):
        self.tagfield.entry.focus_set()
        return("break")
        
    def tabText(self, event=None):
        self.addbutton.focus_set()
        return("break")


class SearchKeyWindow(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self.editkeyframe = None
        self.master.titleframe.setTitle("Søk etter nøkkel")
        self.searchkeyframe = SearchKeyFrame(self)
        self.resultframe = ResultFrame(self, "Nøkler som passer til søket")
        self.pack(side="top", fill="both", expand=True, anchor="nw")
        self.updateResults()
        
    def updateResults(self, event=None):
        base = sqlite3.connect(sqlitefilename)
        c = base.cursor()
        keylist = []
        searchstrings = ('%' + self.searchkeyframe.tagfield.getText() + '%', '%' + self.searchkeyframe.shopfield.getText() + '%', '%' + self.searchkeyframe.detailfield.getText() + '%')
        c.execute("SELECT keyid, keytag, target, details, createdate FROM keys WHERE keys.keytag LIKE ? AND keys.target LIKE ? AND keys.details LIKE ? ORDER BY keys.target ASC, keys.keytag ASC", searchstrings)
        for each_item in c.fetchall():
            keylist.append(KeyItem(each_item[0],each_item[1],each_item[2],each_item[3],each_item[4]))
        c.close()
        base.close()
        self.resultframe.setList(keylist)
        
    def closeEdit(self):
        self.master.titleframe.setTitle("Søk etter nøkkel")
        self.editkeyframe.destroy()
        self.editkeyframe = None
        self.searchkeyframe.pack(side="top", fill="both", anchor="nw")
        self.updateResults()
        
    def openEdit(self, key):
        if self.editkeyframe:
            self.editkeyframe.destroy()
        self.master.titleframe.setTitle("Rediger nøkkel")
        self.searchkeyframe.pack_forget()
        self.editkeyframe = EditKeyFrame(self, key)
        
class SearchKeyFrame(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self["borderwidth"] = 2
        self["relief"] = "ridge"
        self.tagfield = Field(self, "Tag: ", 0, 0)
        self.tagfield.entry.bind('<KeyRelease>', self.master.updateResults)
        self.shopfield = Field(self, "Butikk: ", 1, 0)
        self.shopfield.entry.bind('<KeyRelease>', self.master.updateResults)
        self.detailfield = Field(self, "Detaljer: ", 2, 0)
        self.detailfield.entry.bind('<KeyRelease>', self.master.updateResults)
        self.pack(side="top", fill="both", anchor="nw")
        self.tagfield.entry.focus_set()

class EditKeyFrame(Tix.Frame):
    def __init__(self, master, key):
        Tix.Frame.__init__(self, master)
        self["borderwidth"] = 2
        self["relief"] = "ridge"
        self.key = key
        self.tagfield = Field(self, "Tag: ", 0, 0)
        self.tagfield.setText(key.getTag())
        self.shopfield = Field(self, "Butikk: ", 1, 0)
        self.shopfield.setText(key.getTarget())
        self.detailfield = TextField(self, "Detaljer: ", 2, 0)
        self.detailfield.textfield.text.bind("<Tab>", self.tabText)
        self.detailfield.setText(key.getDetails())
        self.editbutton = Tix.Button(self)
        self.editbutton.bind("<Tab>", self.tabButton)
        self.editbutton["text"] = "Endre nøkkel"
        self.editbutton["command"] = self.editKey
        self.editbutton.grid(row=0, column=2)
        self.pack(side="top", fill="both", anchor="nw")
        self.tagfield.entry.focus_set()
        
    def editKey(self):
        base = sqlite3.connect(sqlitefilename)
        c = base.cursor()
        c.execute("UPDATE keys SET keytag = ?, target = ?, details = ? WHERE keys.keyid == ?", (self.tagfield.getText(), self.shopfield.getText(), self.detailfield.getText().strip(), self.key.getId()))
        base.commit()
        c.close()
        base.close()
        self.master.closeEdit()
        
    def tabButton(self, event=None):
        self.tagfield.entry.focus_set()
        return("break")
        
    def tabText(self, event=None):
        self.editbutton.focus_set()
        return("break")
    
class TextField:
    def __init__(self, master, title, row=0, column=0):
        self.label = Tix.Label(master)
        self.label["text"] = title
        self.label.grid(row=row, column = column, sticky="w", padx=5, pady=5)
        self.textfield = Tix.ScrolledText(master)
        self.textfield.text["width"] = 46
        self.textfield.text["height"] = 10
        self.textfield.grid(row=row, column=column+1, sticky="w", padx=5, pady=5)
        
    def setText(self, text=""):
        self.textfield.text.delete(1.0, Tix.END)
        self.textfield.text.insert(1.0, text)
        
    def getText(self):
        return(self.textfield.text.get(1.0, Tix.END))
    
    def setLabel(self, title=""):
        self.label["text"] = title

class Field:
    def __init__(self, master, title="", row=0, column=0):
        self.label = Tix.Label(master)
        self.label["text"] = title
        self.label.grid(row=row, column=column, sticky="w", padx=5, pady=5)
        self.entry = Tix.Entry(master)
        self.entry["width"] = 40
        self.entry.grid(row=row, column=column+1, sticky="w", padx=5, pady=5)
        self.variable = Tix.StringVar()
        self.entry["textvariable"] = self.variable
        
    def setText(self, text=""):
        self.variable.set(text)
        
    def getText(self):
        return(self.variable.get())
    
    def setLabel(self, title=""):
        self.label["text"] = title
      
class MainWindow(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self.propagate(False)
        self["width"] = 800
        self["height"] = 600
        self.titleframe = TopFrame(self)
        self.titleframe.setTitle("Velg en handling")
        self.menue = Menue(self)
        self.mf = None
        self.pack(expand=True, fill="both")
        
class TopFrame(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self["borderwidth"] = 2
        self["relief"] = "ridge"
        self.title = Tix.Label(self)
        self.title["text"] = ""
        self.title.pack()
        self.pack(side="top", fill="x")
        
    def setTitle(self, title=""):
        self.title["text"] = title
        
class Menue(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self.propagate(False)
        self["width"] = 150
        self["borderwidth"] = 2
        self["relief"] = "ridge"
        self.title = Tix.Label(self)
        self.title["text"] = "Meny"
        self.title.pack(side="top", fill="x")
        self.addkeybutton = MenueButton(self,"Legg til nøkkel")
        self.addkeybutton["command"] = self.addkeys
        self.searchkeybutton = MenueButton(self, "Søk etter nøkkel")
        self.searchkeybutton["command"] = self.searchKeys
        self.createlistbutton = MenueButton(self, "Lag nøkkelliste")
        self.createlistbutton["command"] = self.makeKeyList
        self.pack(side="right",fill="y", anchor="ne")
        
    def addkeys(self):
        if self.master.mf:
            self.master.mf.destroy()
        self.master.mf = AddKeyWindow(self.master)
        
    def searchKeys(self):
        if self.master.mf:
            self.master.mf.destroy()
        self.master.mf = SearchKeyWindow(self.master)
        
    def makeKeyList(self):
        outname = "Nøkkelliste.pdf"
        table_list = [(u'Lokale', u'Tag', u'Detaljer')]
        base = sqlite3.connect(sqlitefilename)
        c = base.cursor()
        keylist = []
        c.execute("SELECT target, keytag, details FROM keys ORDER BY keys.target ASC, keys.keytag ASC")
        for each_item in c.fetchall():
            keylist.append((each_item[0],each_item[1],each_item[2]))
        c.close()
        base.close()
        table_list.extend(keylist)
        tlist = []
        styleSheet = getSampleStyleSheet()
        for each_row in table_list:
            tlist.append((Paragraph(each_row[0].replace('\n', '<br/>'), styleSheet['BodyText']), Paragraph(each_row[1].replace('\n', '<br/>'), styleSheet['BodyText']), Paragraph(each_row[2].replace('\n', '<br/>'), styleSheet['BodyText'])))
        table_list=tlist
        header_list = (Paragraph(u'<para alignment=center>Nøkkelliste<br/>{}<br/>{}</para>'.format(location, time.strftime("%d.%m.%Y")), styleSheet['BodyText']), None, None)
        table_list.insert(0, header_list)
        doc = SimpleDocTemplate(outname)
        elements = []
        body=Table(table_list, colWidths=(80, 80, 360), repeatRows=2)
        body.setStyle(TableStyle([('INNERGRID', (0,0), (-1, -1), 0.25, colors.black),
                                  ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                  ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                  ('SPAN', (0,0), (2,0))]))
        elements.append(body)
        doc.build(elements)

        
class MenueButton(Tix.Button):
    def __init__(self, master, title=""):
        Tix.Button.__init__(self, master)
        self["text"] = title
        self.pack(side="top", fill="x")
        
class ResultFrame(Tix.Frame):
    def __init__(self, master, title=""):
        Tix.Frame.__init__(self, master)
        self["borderwidth"] = 2
        self["relief"] = "ridge"
        self.topframe = Tix.Frame(self)
        self.title = Tix.Label(self.topframe)
        self.title["text"] = title
        self.title.pack(side="left", anchor="sw")
        self.editkeybutton = Tix.Button(self.topframe)
        self.editkeybutton["text"] = "Endre"
        self.editkeybutton["command"] = self.editKey
        self.editkeybutton.pack(side="right", anchor="se")
        self.deletekeybutton = Tix.Button(self.topframe)
        self.deletekeybutton["text"] = "Slett"
        self.deletekeybutton["command"] = self.deleteKey
        self.deletekeybutton.pack(side="right", anchor="se")
        self.topframe.pack(fill="x", anchor="nw", side="top")
        self.bottomframe = Tix.Frame(self)
        self.listbox = Tix.ScrolledListBox(self.bottomframe)
        self.listbox.pack(expand=True, fill="both", side="left", anchor="sw")
        self.listbox.listbox.bind("<ButtonRelease-1>", self.selectedItem)
        self.showframe = ShowFrame(self.bottomframe)
        self.bottomframe.pack(expand=True, fill="both", side="bottom")
        self.pack(expand=True, fill="both", anchor="sw", side="bottom")
        self.keylist = []
        
    def deleteKey(self):
        try:
            choice = int(self.listbox.listbox.curselection()[0])
        except TypeError:
            choice = -1
        if choice >= 0:
            base = sqlite3.connect(sqlitefilename)
            c = base.cursor()
            keylist = []
            c.execute("DELETE FROM keys WHERE keys.keyid = ?", (self.keylist[choice].getId(),))
            base.commit()
            c.execute("SELECT keyid, keytag, target, details, createdate FROM keys ORDER BY keys.createdate DESC LIMIT 30")
            for each_item in c.fetchall():
                keylist.append(KeyItem(each_item[0],each_item[1],each_item[2],each_item[3],each_item[4]))
            c.close()
            base.close()
            self.setList(keylist)
            
    def editKey(self):
        choice = -1
        try:
            choice = int(self.listbox.listbox.curselection()[0])
        except TypeError:
            pass
        if choice >= 0:
            self.master.openEdit(self.keylist[choice])
        
    def setList(self, keylist):
        self.keylist = keylist
        self.listbox.listbox.delete(0, Tix.END)
        for each_item in self.keylist:
            self.listbox.listbox.insert(Tix.END, "Tag: %s, Lokale: %s" % (each_item.getTag(), each_item.getTarget()))
    
    def selectedItem(self, event):
        try:
            choice = int(self.listbox.listbox.curselection()[0])
        except TypeError:
            choice = -1
        if choice >= 0:
            self.showframe.setItem(self.keylist[choice])
        else:
            self.showframe.clear()
         
class KeyItem:
    def __init__(self, keyid=0, keytag="", target="", details="", date=""):
        self.setId(keyid)
        self.keytag = keytag
        self.target = target
        self.details = details
        self.date = date
        
    def getTag(self):
        return(self.keytag)
    
    def getTarget(self):
        return(self.target)
    
    def getId(self):
        return(self.keyid)
    
    def getDetails(self):
        return(self.details)
    
    def setId(self, keyid):
        try:
            self.keyid = int(keyid)
        except TypeError:
            self.keyid = 0
        return(self.keyid)
    
class ShowFrame(Tix.Frame):
    def __init__(self, master):
        Tix.Frame.__init__(self, master)
        self.propagate(False)
        self["width"] = 200
        self.taglabel = Tix.Label(self)
        self.taglabel["text"] = "Tag:"
        self.taglabel.pack(side="top", fill="x", anchor="w")
        self.tagentry = Tix.Entry(self)
        self.tagentry["state"] = "disabled"
        self.tagentry["disabledforeground"] = self.tagentry["foreground"] 
        self.tagvar = Tix.StringVar()
        self.tagentry["textvariable"] = self.tagvar
        self.tagentry.pack(side="top", fill="x", anchor="w")
        self.shoplabel = Tix.Label(self)
        self.shoplabel["text"] = "Butikk:"
        self.shoplabel.pack(side="top", fill="x", anchor="w")
        self.shopentry = Tix.Entry(self)
        self.shopentry["state"] = "disabled"
        self.shopentry["disabledforeground"] = self.shopentry["foreground"] 
        self.shopvar = Tix.StringVar()
        self.shopentry["textvariable"] = self.shopvar
        self.shopentry.pack(side="top", fill="x", anchor="w")
        self.detaillabel = Tix.Label(self)
        self.detaillabel["text"] = "Detaljer:"
        self.detaillabel.pack(side="top", fill="x", anchor="w")
        self.detailtext = Tix.ScrolledText(self)
        self.detailtext.text["state"] = "disabled"
        self.detailtext.text["background"] = self.tagentry["disabledbackground"]
        self.detailtext.pack(side="top", fill="both", anchor="w")
        self.pack(fill="both", anchor="se", side="right")
        self.key = None
    
    def clear(self):
        self.setItem(KeyItem())
    
    def setItem(self, item):
        self.detailtext.text["state"] = "normal"
        self.tagentry["state"] = "normal"
        self.shopentry["state"] = "normal"
        self.tagvar.set(item.getTag())
        self.shopvar.set(item.getTarget())
        self.detailtext.text.delete(1.0, Tix.END)
        self.detailtext.text.insert(Tix.END, item.getDetails())
        self.tagentry["state"] = "disabled"
        self.shopentry["state"] = "disabled"
        self.detailtext.text["state"] = "disabled"
        
          
if __name__ == "__main__":
    #check database, and  create  it if necesary. Exit if the database does not exist after this procedure
    if not createBase(os.path.join(os.getcwd(), sqlitefilename)):
        print("Could not create or use the  database file.")
        exit()
    application = Tix.Tk()
    application.title("Keyholder")
    mw = MainWindow(application)
    application.mainloop()
    
