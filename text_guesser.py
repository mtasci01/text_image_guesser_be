import datetime
import logging
import os
import tkinter as tk
from bson import ObjectId
import nltk
import numpy as np
from pathlib import Path
import configparser

import pymongo

app = tk.Tk() 


app.title("Text Guesser!") 

class GlobalState:
    def __init__(self):
        self.filename = ""
        self.tokens=[]
        self.savedFileId = None
        self.totalGuessed = 0
        self.pChange = 0.1
        self.ixDict = {}

gState = GlobalState()        

def getRightnowUTC():
    return round(datetime.datetime.now(datetime.timezone.utc).timestamp()*1000)
    

def read_config():

    config = configparser.ConfigParser()
 
    config.read('config.ini')
 
    config_values = {
        'mongo_connstr': config.get('General', 'mongo_connstr'),
        'mongo_db': config.get('General', 'mongo_db')
    }
 
    return config_values

config = read_config()
mongoclient = pymongo.MongoClient(config['mongo_connstr'])
db = mongoclient[config['mongo_db']]
logging.basicConfig(level=logging.INFO)
stopwords = set(w.rstrip() for w in open('resources/stopwords.txt'))
punctuation = {",",".",";",":","(",")","→","’","'","”","“","\""}

def uploadSaveBtnPress():
    fullFilename = tk.filedialog.askopenfilename()
    if fullFilename != None and fullFilename != "":
        f = open(fullFilename,encoding="utf-8")
        fread = f.read()
        insertTextFile(fullFilename,fread)
        drawUploadFrame() 

def getSavedFiles():
    return list(db.text_guesser.find({}))

def deletefileBtnPress(fileId):
    deleteSavedFile(fileId)
    drawUploadFrame() 

def deleteSavedFile(fileId):
    answer = tk.messagebox.askyesno(title='confirmation',
                    message='Are you sure that you delete the file?')
    if answer:
        db.text_guesser.delete_one({'_id': ObjectId(fileId)})
        logging.info("delete textDoc with id " + str(fileId))     

def insertTextFile(fullFilename, content):
    textDoc = {"createdAtUTC":getRightnowUTC(),"fullFilename":fullFilename,"content":content, "scores":[]}

    db.text_guesser.insert_one(textDoc)
    logging.info("created textDoc with id " + str(textDoc["_id"]))
    tk.messagebox.showinfo(title = "Success", message = "File saved")

def playFromSavedBtnPressed(docId):
    fileDoc = db.text_guesser.find_one({'_id': ObjectId(docId)})
    pT = probAndTokenizer(fileDoc["content"])
    if pT == True:
        gState.savedFileId = docId
        drawTextFrame()
        textwidgetText(gState.tokens)


def drawMainFrame():
    gState.savedFileId = None
    gState.totalGuessed = 0
    frame1.grid(row=0, column=0)
    frame2.grid_forget()
    frame3.grid_forget()
    frame4.grid_forget()
    frame5.grid_forget()

def drawUploadFrame():
    frame1.grid_forget()
    frame4.grid(row=0, column=0)
    frame2.grid_forget()
    frame3.grid_forget()

    for widget in frame5.winfo_children():
       widget.destroy()
    lst = getSavedFiles()
    total_rows = len(lst)
    for i in range(total_rows):
        filename = os.path.basename(lst[i]["fullFilename"])
        e = tk.Label(frame5,text=filename, fg='blue',
                        font=('Arial',12,))
        e.grid(row=i + 3, column=0,padx=3,pady=3)
        
        b = tk.Button(frame5, text='Play', command=lambda i=i: playFromSavedBtnPressed(lst[i]["_id"] ))
        b.grid(row=i + 3, column=1,padx=3,pady=3)
        b2 = tk.Button(frame5, text='Delete the file', command=lambda i=i: deletefileBtnPress(lst[i]["_id"] ))
        b2.grid(row=i + 3, column=2,padx=3,pady=3)
    if (total_rows == 0):
        noSavedLabel = tk.Label(frame5,
                            text="No Files saved in DB",
                            font=("Helvetica", 15))
        noSavedLabel.grid(row=0, column=0, padx=20, pady=10)    
    frame5.grid(row=1, column=0)    

def drawTextFrame():
    frame1.grid_forget()
    frame2.grid(row=0, column=0)
    frame3.grid(row=0, column=1)
    if gState.savedFileId == None:
        saveScoreButton.grid_forget()
    else:
        saveScoreButton.grid()    
    frame4.grid_forget()
    frame5.grid_forget()

def playnowBtnPress():
    gState.filename = tk.filedialog.askopenfilename()
    if gState.filename != None and gState.filename != "":
        lsf = loadSourceFile()
        if lsf == True:
            drawTextFrame()
            textwidgetText(gState.tokens)

def saveScoreBtnPress():
    if (gState.savedFileId == None):
        return
    
    answer = tk.messagebox.askyesno(title='confirmation',
             message='Are you sure to save your score with guessed '  + str(gState.totalGuessed) + ' out of ' + str(len(gState.ixDict)) +  '? ' )
    
    if answer:
        fileDoc = db.text_guesser.find_one({'_id': ObjectId(gState.savedFileId)})    
        if (fileDoc == None):
            logging.error("textDoc " + str(gState.savedFileId) + " not found") 
            return
        scoreObj = {"createdAtUTC":getRightnowUTC(), "totalGuessed":gState.totalGuessed, "totalChangedTokens":len(gState.ixDict), "probOfTokenChange":gState.pChange}
        scores = fileDoc["scores"]
        scores.append(scoreObj)
        db.text_guesser.find_one_and_update(
            {"_id" : ObjectId(gState.savedFileId)},
            {"$set":
                {"scores": scores}
            },upsert=False
        )
        logging.info("saved score for " + str(gState.savedFileId))    
         

def textwidgetText(tokens):
    text = ' '.join(tokens)
    text = text.replace(' . ', '. ')
    text = text.replace(' , ', ', ')
    text = text.replace(' ; ', '; ')
    text = text.replace(' : ', ': ')
    text = text.replace(" ’ ", "’")
    text = text.replace(" “ ", "“") 

    textwidget.delete('1.0',tk.END)
    textwidget.insert('1.0',text)
    textwidget.grid(row=0, column=0, padx=10, pady=10)       

def isfloat(num):
    try:
        float(num)
        return True
    except:
        return False
    
def pChangeDefault():
    tk.messagebox.showwarning(title = "Warning", message = "Not a valid probability, defaulting to 0.1")
    gState.pChange = 0.1

def probAndTokenizer(fread):
    gState.pChange = tk.simpledialog.askstring("Input", "Enter probability of hiding word (between 0 and 1)", parent=app)
    if gState.pChange == None:
        return False
    if not(isfloat(gState.pChange)):
        pChangeDefault()
    else:
        gState.pChange = float(gState.pChange)
        if not(gState.pChange > 0 and gState.pChange < 1):
            pChangeDefault()

    gState.tokens = nltk.tokenize.word_tokenize(fread)
    changeCnt = 0
    gState.ixDict = {}
    for i in range(len(gState.tokens)):
        tokenL = gState.tokens[i].lower()
        if (tokenL in stopwords or tokenL in punctuation):
            continue
        randnum = np.random.rand()
        if randnum <= gState.pChange:
            placeholder = "{" + str(changeCnt) + "}"
            gState.ixDict[str(changeCnt)] = {"i":i, "originalText":gState.tokens[i]} 
            gState.tokens[i] = placeholder
            changeCnt = changeCnt + 1
    return True


def loadSourceFile():
    my_file = Path(gState.filename)
    if not(my_file.is_file()):
        tk.messagebox.showwarning(title = "Warning", message = gState.filename + " not a valid file")
        return False

    f = open(gState.filename,encoding="utf-8")
    fread = f.read()
    return probAndTokenizer(fread)
    

def revealNumber(event=None):
    ix = revealNumTextInput.get()
    if not(ix in gState.ixDict):
       tk.messagebox.showwarning(title = "Warning", message = ix + " not a valid choice")
    ixObj = gState.ixDict[ix]
    gState.tokens[ixObj["i"]] = ixObj["originalText"] 
    textwidgetText(gState.tokens)
    revealNumTextInput.delete(0, tk.END)

def guessWord(event=None):
    guess = guessWordTextInput.get()
    for ix in gState.ixDict:
        ixObj = gState.ixDict[ix]
        if guess.lower() == ixObj["originalText"].lower():
            gState.tokens[ixObj["i"]] = ixObj["originalText"]
            gState.totalGuessed = gState.totalGuessed + 1
    textwidgetText(gState.tokens)
    guessWordTextInput.delete(0, tk.END) 
                 
  
# ---------------- frame1 
frame1 = tk.Frame(app, padx=15, pady=15) 
  
welcomeLabel = tk.Label(frame1,
                         text="Welcome to Text Guesser! Pick your choice",
                         font=("Helvetica", 15))
welcomeLabel.grid(row=0, column=0,  padx=20, pady=10)
playNowButton = tk.Button(frame1, text='Upload your text file and play right away!', command=playnowBtnPress)
playNowButton.grid(row=1, column=0, padx=20, pady=10)
uploadPageBtn = tk.Button(frame1, text='Upload and store your text file! (uses DB)', command=drawUploadFrame)
uploadPageBtn.grid(row=2, column=0, padx=20, pady=10)

# ---------------- frame2

frame2 = tk.Frame(app, padx=15, pady=15)
#------------------------frame 3
guessWordLabel = tk.Label(frame2,
                         text="Guess a word",
                         font=("Helvetica", 15))

guessWordLabel.grid(row=0, column=0, padx=20, pady=10)
guessWordTextInput = tk.Entry(frame2)
guessWordTextInput.grid(row=1, column=0, padx=10)
guessWordTextInput.bind("<Return>", guessWord)
revealNumLabel = tk.Label(frame2,
                         text="Reveal number",
                         font=("Helvetica", 15))
revealNumLabel.grid(row=2, column=0, padx=20, pady=10)
revealNumTextInput = tk.Entry(frame2)
revealNumTextInput.grid(row=3, column=0, padx=10)
revealNumTextInput.bind("<Return>", revealNumber)
backButton = tk.Button(frame2,text="BACK TO MAIN", command=drawMainFrame)
backButton.grid(row=4, column=0,  pady=10, padx=10)
saveScoreButton = tk.Button(frame2,text="SAVE SCORE", command=saveScoreBtnPress)
saveScoreButton.grid(row=5, column=0, pady=10, padx=10)
#------------------------frame 3
frame3 = tk.Frame(app, padx=15, pady=15)
textwidget = tk.Text(frame3,wrap=tk.WORD)
textwidget.insert(tk.END, "your text here")
textwidget.bind("<Key>", lambda e: "break")
 
# ---------------- frame4
frame4 = tk.Frame(app, padx=15, pady=15) 
  
uploadSaveBtn = tk.Button(frame4, text='Upload your text file!', command=uploadSaveBtnPress)
uploadSaveBtn.grid(row=1, column=0, padx=20, pady=10)
backMainButton = tk.Button(frame4, text='Back to main', command=drawMainFrame)
backMainButton.grid(row=2, column=0, padx=20, pady=10)
frame5 = tk.Frame(app, padx=15, pady=15) 
             

drawMainFrame()
app.mainloop() 
