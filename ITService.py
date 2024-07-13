import configparser
import csv
import datetime
import io
import math
import os
import pathlib
import pickle
import uuid
from PIL import Image
import logging
from pathlib import Path
import nltk

import json

import bson
import numpy as np
import pymongo


class ITService:

    MIN_SIZE = 300
    NUM_SIDE_SEGMENTS = 8
    STORAGE_FOLDER = "storage"
    IMG_NAME_IN_FOLDER = "image.png"
    STATUS_VISIBLE = "visible"
    STATUS_NOT_VISIBLE = "not_visible"
    logging.basicConfig(level=logging.INFO)
    

    def __init__(self):
        
        self.config = self.read_config()
        if (not(self.config['imgguessing_usemongo'])):
            currPath = pathlib.Path().resolve()
            Path(str(currPath) + "/" + self.STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)
        else:    
            self.mongoclient = pymongo.MongoClient(self.config['mongo_connstr'])
            self.db = self.mongoclient[self.config['mongo_db']]
        self.stopwords = set(w.rstrip() for w in open('resources/stopwords.txt'))
        self.punctuation = {",",".",";",":","(",")","→","’","'","”","“","\""}

    def read_config(self):

        config = configparser.ConfigParser()
    
        config.read('config.ini')
    
        config_values = {
            'mongo_connstr': config.get('General', 'mongo_connstr'),
            'mongo_db': config.get('General', 'mongo_db'),
            'imgguessing_usemongo': config.getboolean('General', 'imgguessing_usemongo')
        }
    
        return config_values    

    def writeJson(self,filename,data):
        json_object = json.dumps(data, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)
            
    def getRightnowUTC(self):
        return round(datetime.datetime.now(datetime.timezone.utc).timestamp()*1000)
    
    def getSavedTextFiles(self):
        tList = list(self.db.text_guesser.find({}))
        for e in tList:
            e["fileid"] = str(e["_id"]) 
            e["_id"] = None
            e['filename'] = os.path.basename(e["fullFilename"])
        return tList
    
    def startGame(self,docId,pChange):
        pChange = float(pChange)
        fileDoc = self.db.text_guesser.find_one({'_id': bson.ObjectId(docId)})
        tokens = nltk.tokenize.word_tokenize(fileDoc["content"])
        changeCnt = 0
        ixDict = {}
        for i in range(len(tokens)):
            tokenL = tokens[i].lower()
            if (tokenL in self.stopwords or tokenL in self.punctuation):
                continue
            randnum = np.random.rand()
            if randnum <= pChange:
                placeholder = "{" + str(changeCnt) + "}"
                ixDict[str(changeCnt)] = {"i":i, "originalText":tokens[i]} 
                tokens[i] = placeholder
                changeCnt = changeCnt + 1
        text = ' '.join(tokens)
        text = text.replace(' . ', '. ')
        text = text.replace(' , ', ', ')
        text = text.replace(' ; ', '; ')
        text = text.replace(' : ', ': ')
        text = text.replace(" ’ ", "’")
        text = text.replace(" “ ", "“")         
        doc = {'tokens':tokens,'ixDict':ixDict, "text_id":bson.ObjectId(docId), "text":text}        
        docIn = self.db.text_guesser_game_cache.insert_one(doc)
        retDoc = {'game_id':str(docIn.inserted_id),"text":text}
        return retDoc        

    
    def checkClickOnImg(self, loadImgRes,p):
        blackRects = list(filter(lambda r: r['status'] == self.STATUS_NOT_VISIBLE, loadImgRes["rects"]))
        for r in blackRects:
            if self.pointInRectangle(r['rect'],p):
                r['status'] = self.STATUS_VISIBLE
                rect = r['rect']
                for x in range(rect[0],rect[2]):
                    for y in range(rect[1],rect[3]):
                        loadImgRes["img"].putpixel((x, y), loadImgRes["imgOriginal"].getpixel((x, y)))
                break
    


    def pointInRectangle(self,tl_br, p):
        bl = [tl_br[0],tl_br[3]]
        tr = [tl_br[2],tl_br[1]]
        if (p[0] >= bl[0] and p[0] <= tr[0] and p[1] <= bl[1] and p[1] >= tr[1]):
            return True
        else:
            return False    

    def uploadImgFiles(self,metadataFile):
        if (not(self.config['imgguessing_usemongo'])):
            self.uploadImgFilesFS(metadataFile)
        else:
            self.uploadImgFilesMongo(metadataFile)

    def uploadImgFilesMongo(self,metadataFile):
        with open(metadataFile, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                with open(row[0], 'rb') as f:
                    contents = f.read()
                    doc = {"createdAt":self.getRightnowUTC(),"label":row[1],"img": bson.Binary(pickle.dumps(contents))}
                    self.db.img_guesser.insert_one(doc)
                    logging.info("created doc with id " + str(doc["_id"]))

    def uploadImgFilesFS(self,metadataFile):
        currPath = pathlib.Path().resolve()
        with open(metadataFile, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                docId = uuid.uuid4()
                data={"label":row[1], "createdAt":self.getRightnowUTC(),"docId":str(docId)}
                docPath = str(currPath) + "/" + self.STORAGE_FOLDER + "/" + str(docId)
                Path(docPath).mkdir(parents=True, exist_ok=True)
                img = Image.open(row[0])
                img = img.save(docPath + "/" + self.IMG_NAME_IN_FOLDER,bitmap_format='png') 
                self.writeJson(docPath + "/data.json",data)
         
    def blackenPixels(self,rects,img):
        rectsToBlack = list(filter(lambda r: r['status'] == self.STATUS_NOT_VISIBLE, rects))
        for r in rectsToBlack:
            rect = r['rect']
            for x in range(rect[0],rect[2]):
                for y in range(rect[1],rect[3]):
                    img.putpixel((x,y),(0,0,0))
                  

    def getNumOfImages(self):
        numImgs = 0
        if (not(self.config['imgguessing_usemongo'])):
            currPath = pathlib.Path().resolve()
            contents = os.listdir(str(currPath) + "/" + self.STORAGE_FOLDER)
            numImgs = len(contents)
        else:
            numImgs = self.db.img_guesser.count_documents({})
        return numImgs
    
    def randomDoc(self):
        contents = []
        if (not(self.config['imgguessing_usemongo'])):
            currPath = pathlib.Path().resolve()
            contents = os.listdir(str(currPath) + "/" + self.STORAGE_FOLDER)
        else:
            contents = list(self.db.img_guesser.find({},{ "createdAt": 1 }))
            contents = list(map(lambda d: str(d["_id"]), contents))   
        if len(contents) == 0: return None
        return np.random.choice(contents)
    
    def countShownRects(self,rects):
        blackRects = list(filter(lambda r: r['status'] == self.STATUS_NOT_VISIBLE, rects))
        return len(rects),len(blackRects)

    def loadImg(self, docId):
        data  ={}
        if (not(self.config['imgguessing_usemongo'])):
            currPath = pathlib.Path().resolve()        
            f = open(str(currPath) + "/" + self.STORAGE_FOLDER + "/" + docId + "/data.json")
            data = json.load(f)
            imgpath = str(currPath) + "/" + self.STORAGE_FOLDER + "/" + docId + "/" + self.IMG_NAME_IN_FOLDER
            img = Image.open(imgpath)
        else:
            record = self.db.img_guesser.find_one({'_id': bson.ObjectId(docId)})
            if (record) is None:
                raise TypeError("doc not found " + docId)
            imgBytes = pickle.loads(record["img"])
            img = Image.open(io.BytesIO(imgBytes))
            data['label']= record['label']

        minSide = img.width
        if img.height < minSide:
            minSide = img.height
        if minSide % 2 == 1:
            minSide = minSide - 1
        if (minSide < self.MIN_SIZE):
            logging.info(docId + " not enough size")
            return
        squareSide = minSide/self.NUM_SIDE_SEGMENTS
        squareSide = math.floor(squareSide)
        minSide = squareSide*self.NUM_SIDE_SEGMENTS
        img = img.resize((minSide,minSide))
        imgO = img.copy() 
        rects = self.getRects(squareSide)
        rectChosen = np.random.choice(rects)
        rectChosen['status'] = self.STATUS_VISIBLE
        self.blackenPixels(rects,img)
          
        res = {"img":img, "imgOriginal":imgO, "rects":rects, "imgSize":minSide, "label":data['label'].lower()}
        return res   

    def getRects(self,squareSide):
        rects = []
        for y in range(self.NUM_SIDE_SEGMENTS):
            for x in range(self.NUM_SIDE_SEGMENTS):
                rect = [x*squareSide,y*squareSide, (x+1)*squareSide,(y+1)*squareSide]
                rectObj = {"rect":rect,"status":self.STATUS_NOT_VISIBLE}
                rects.append(rectObj)
        return rects    
