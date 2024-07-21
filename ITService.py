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
import gridfs
import nltk

import json

import bson
import numpy as np
import pymongo


class ITService:

    MIN_SIZE = 300
    IMG_MAX_SIZE = 5000
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
        self.fs = gridfs.GridFS(self.db)

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
            #e['filename'] = os.path.basename(e["fullFilename"])
        return tList
    
    def tokenstoTxt(self,tokens):
        text = ' '.join(tokens)
        text = text.replace(' . ', '. ')
        text = text.replace(' , ', ', ')
        text = text.replace(' ; ', '; ')
        text = text.replace(' : ', ': ')
        text = text.replace(" ’ ", "’")
        text = text.replace(" “ ", "“")
        return text 
    
    def start_char_game(self,file_id,pChange):
        pChange = float(pChange)
        file_doc = self.db.text_guesser.find_one({'_id': bson.ObjectId(file_id)})
        ret = []
        if (file_doc) is None:
            raise TypeError("file_id not found " + file_id)
        ix = 0
        for c in file_doc["content"]:
            ret_obj = {"char":c, "to_replace":False, "ix":ix}
            if not(c in self.punctuation or c == ' '):
                randnum = np.random.rand()
                if randnum <= pChange:
                    ret_obj['to_replace']=True
            ret.append(ret_obj)
            ix = ix + 1
        return ret            
                


    
    def startTxtGame(self,file_id,pChange):
        pChange = float(pChange)
        file_doc = self.db.text_guesser.find_one({'_id': bson.ObjectId(file_id)})
        if (file_doc) is None:
            raise TypeError("file_id not found " + file_id) 
        tokens = nltk.tokenize.word_tokenize(file_doc["content"])
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
        text = self.tokenstoTxt(tokens)
        doc = {'tokens':tokens,'ixDict':ixDict, "text_id":bson.ObjectId(file_id), "text":text, "created_at":self.getRightnowUTC()}        
        docIn = self.db.text_guesser_game_cache.insert_one(doc)
        logging.info("started game with id " + str(docIn.inserted_id)) 
        retDoc = {'game_id':str(docIn.inserted_id),"text":text}
        return retDoc
            
    def guessTextWord(self,game_id,word):
        cache_doc = self.db.text_guesser_game_cache.find_one({"_id":bson.ObjectId(game_id)})
        if (cache_doc) is None:
            raise TypeError("game_id not found " + game_id) 
        for ix in cache_doc['ixDict']:
            ixObj = cache_doc['ixDict'][ix]
            if word.lower() == ixObj["originalText"].lower():
                cache_doc['tokens'][ixObj["i"]] = ixObj["originalText"]
        self.db.text_guesser_game_cache.update_one({"_id":bson.ObjectId(game_id)},{ "$set": { 'tokens': cache_doc['tokens'],"updated_at":self.getRightnowUTC() } } ) 
        text = self.tokenstoTxt(cache_doc['tokens'])       
        return {"text":text} 

    def delete_file(self, text_id):
        self.db.text_guesser.delete_one({'_id': bson.ObjectId(text_id)})
        logging.info("delete textDoc with id " + str(text_id)) 

    def upload_file(self,file):
        contents=[]
        with file.file as f:
            for line in io.TextIOWrapper(f, encoding='utf-8'):
                contents.append(line)
        content = os.linesep.join(contents)        
        text_doc = {"created_at":self.getRightnowUTC(),"filename":file.filename,"content":content, "scores":[]}

        self.db.text_guesser.insert_one(text_doc)
        logging.info("created text_doc with id " + str(text_doc["_id"]))     

    def upload_labeled_file(self,file,label):
        with file.file as f:
            doc = {"created_at":self.getRightnowUTC(),"filename":file.filename,"label":label,"img": bson.Binary(pickle.dumps(f.read()))}
            self.db.img_guesser.insert_one(doc)
            logging.info("created img_doc with id " + str(doc["_id"]))   

    def get_saved_img(self, doc_id):
        doc = self.db.img_guesser.find_one({'_id': bson.ObjectId(doc_id)})
        if (doc) is None:
            raise TypeError("doc not found " + doc_id)
        return {"img":pickle.loads(doc["img"]), "ext":os.path.splitext(doc["filename"])[1]}      
              
        
    def textRevealNumber(self,game_id,ix):
        ix = str(ix)
        cache_doc = self.db.text_guesser_game_cache.find_one({"_id":bson.ObjectId(game_id)})
        if (cache_doc) is None:
            raise TypeError("game_id not found " + game_id) 
        if not(ix in cache_doc['ixDict']):
            text = self.tokenstoTxt(cache_doc['tokens'])    
            return {"text":text}
        ixObj = cache_doc['ixDict'][ix]
        cache_doc['tokens'][ixObj["i"]] = ixObj["originalText"]
        self.db.text_guesser_game_cache.update_one({"_id":bson.ObjectId(game_id)},{ "$set": { 'tokens': cache_doc['tokens'],"updated_at":self.getRightnowUTC() } } )
        text = self.tokenstoTxt(cache_doc['tokens'])    
        return {"text":text}

    def click_img_sent(self,p,client_img_size,game_id):
       
        cache_doc = self.db.img_guesser_game_cache.find_one({"_id":bson.ObjectId(game_id)})
        if (cache_doc) is None:
            raise TypeError("game_id not found " + game_id) 
        p_x = math.floor((p[0]*cache_doc['img_size'])/client_img_size)
        p_y = math.floor((p[1]*cache_doc['img_size'])/client_img_size)
        
        img_bytes = pickle.loads(cache_doc["img"])
        cache_doc["img"] = Image.open(io.BytesIO(img_bytes))

        img_bytes_origin = pickle.loads(cache_doc["img_original"])
        cache_doc["img_original"] = Image.open(io.BytesIO(img_bytes_origin))

        self.checkClickOnImg(cache_doc,[p_x,p_y])

        img_byte_arr = io.BytesIO()
        cache_doc['img'].save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        self.db.img_guesser_game_cache.update_one({"_id":bson.ObjectId(game_id)},{ "$set": { 'img': bson.Binary(pickle.dumps(img_byte_arr)),'rects': cache_doc['rects'],"updated_at":self.getRightnowUTC() } } ) 
    
    

    def checkClickOnImg(self, loadImgRes,p):
        blackRects = list(filter(lambda r: r['status'] == self.STATUS_NOT_VISIBLE, loadImgRes["rects"]))
        for r in blackRects:
            if self.pointInRectangle(r['rect'],p):
                r['status'] = self.STATUS_VISIBLE
                rect = r['rect']
                for x in range(rect[0],rect[2]):
                    for y in range(rect[1],rect[3]):
                        loadImgRes["img"].putpixel((x, y), loadImgRes["img_original"].getpixel((x, y)))
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

    def init_black_img(self,rects,img_o, new_img):
        not_black = list(filter(lambda r: r['status'] == self.STATUS_VISIBLE, rects))
        for r in not_black:
            rect = r['rect']
            for x in range(rect[0],rect[2]):
                for y in range(rect[1],rect[3]):
                    new_img.putpixel((x,y),img_o.getpixel((x, y)))                

    def start_img_game(self):
        doc_id = self.randomDoc()
        ret = self.loadImg(doc_id) #optimize here
        if (ret['img'] == None):
            return
        img_byte_arr = io.BytesIO()
        ret['img'].save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        original_img_byte_arr = io.BytesIO()
        ret['img_original'].save(original_img_byte_arr, format='PNG')
        original_img_byte_arr = original_img_byte_arr.getvalue()
        

        doc = {'img':bson.Binary(pickle.dumps(img_byte_arr)),'img_original':bson.Binary(pickle.dumps(original_img_byte_arr)),
               "rects":ret['rects'],"img_size":ret['img_size'],"label":ret['label'],
                "img_id":bson.ObjectId(doc_id), "created_at":self.getRightnowUTC()}        
        self.db.img_guesser_game_cache.insert_one(doc)

        ret_ret = {"doc_id":doc_id,"label":ret['label'],"game_id":str(doc['_id'])}

        return ret_ret
    
    def get_all_labels(self):
        docs = self.db.img_guesser.find({},{ "label": 1 })
        return list(map(lambda d: str(d["label"]), docs))   
        
    
    def download_cached_img(self, game_id):
        cache_doc = self.db.img_guesser_game_cache.find_one({"_id":bson.ObjectId(game_id)})
        if (cache_doc) is None:
            raise TypeError("game_id not found " + game_id)
        img_bytes = pickle.loads(cache_doc["img"]) 
        return {"img_bytes":img_bytes} 
    
    def download_cached_original(self, game_id):
        cache_doc = self.db.img_guesser_game_cache.find_one({"_id":bson.ObjectId(game_id)})
        if (cache_doc) is None:
            raise TypeError("game_id not found " + game_id)
        img_origin_bytes = pickle.loads(cache_doc["img_original"]) 
        return {"img_origin_bytes":img_origin_bytes} 
                  

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
        data = {}
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
            raise TypeError(docId + " not enough size")
        if (minSide > self.IMG_MAX_SIZE):
            raise TypeError(docId + " too much size")
        squareSide = minSide/self.NUM_SIDE_SEGMENTS
        squareSide = math.floor(squareSide)
        minSide = squareSide*self.NUM_SIDE_SEGMENTS
        img = img.resize((minSide,minSide))
        img_o = img.copy()
        new_img = Image.new('RGB', (minSide,minSide)) 
        rects = self.getRects(squareSide)
        rectChosen = np.random.choice(rects)
        rectChosen['status'] = self.STATUS_VISIBLE
        self.init_black_img(rects,img_o,new_img)
          
        res = {"img":new_img, "img_original":img_o, "rects":rects, "img_size":minSide, "label":data['label'].lower(),"doc_id":docId}
        return res   

    def getRects(self,squareSide):
        rects = []
        for y in range(self.NUM_SIDE_SEGMENTS):
            for x in range(self.NUM_SIDE_SEGMENTS):
                rect = [x*squareSide,y*squareSide, (x+1)*squareSide,(y+1)*squareSide]
                rectObj = {"rect":rect,"status":self.STATUS_NOT_VISIBLE}
                rects.append(rectObj)
        return rects

    #-------------------------GRIDFS TESTS    
    def fs_upload_test(self,file):
        with file.file as f:
            a = self.fs.put(f)
            print(a)
            fs_out = self.fs.get(a)
            img_bytes = fs_out.read()

            pil_img = Image.open(io.BytesIO(img_bytes))

            img_bytes_new = io.BytesIO()
            pil_img.save(img_bytes_new, format='PNG')
            img_bytes_new = img_bytes_new.getvalue()

            return img_bytes_new
        
