from fastapi import FastAPI, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ITService import ITService

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = ITService()



@app.get("/text/get_saved_files")
def getSavedFiles():
    return service.getSavedTextFiles()

@app.get("/text/start_game")
def start_txt_game(docId,prob):
    return service.startTxtGame(docId,prob)

@app.get("/text/guess_word")
def guess_text_word(game_id,word):
    return service.guessTextWord(game_id,word)

@app.get("/text/reveal_number")
def text_reveal_number(game_id,number):
    return service.textRevealNumber(game_id,number)

@app.delete("/text/delete_file")
def delete_file(file_id):
    return service.delete_file(file_id)

@app.post("/text/upload_file")
def upload_file(file: UploadFile):
    return service.upload_file(file)

@app.get("/text/start_char_game")
def start_char_game(file_id,prob):
    return service.start_char_game(file_id,prob)

@app.post("/img/upload_labeled_file")
def upload_labeled_file(file: UploadFile, label):
    return service.upload_labeled_file(file,label)

@app.get("/img/get")
def get_labeled_img(doc_id):
    ret =   service.get_saved_img(doc_id)
    return Response(content=ret['img'], media_type="image/" +ret['ext'].replace('.',''))

@app.get("/img/get_saved_img_num")
def get_saved_img_num():
    return service.getNumOfImages()

@app.get("/img/start_game")
def start_img_game():
    ret=  service.start_img_game()
    return ret

@app.get("/img/download_cached")
def download_cached_img(game_id):
    ret =  service.download_cached_img(game_id)
    return Response(content=ret['img_bytes'], media_type="image/png")
