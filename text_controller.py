from fastapi import FastAPI, UploadFile
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

#uvicorn text_controller:app --reload

@app.get("/text/get_saved_files")
def getSavedFiles():
    return service.getSavedTextFiles()

@app.get("/text/start_game")
def startGame(docId,prob):
    return service.startTxtGame(docId,prob)

@app.get("/text/guess_word")
def startGame(game_id,word):
    return service.guessTextWord(game_id,word)

@app.get("/text/reveal_number")
def startGame(game_id,number):
    return service.textRevealNumber(game_id,number)

@app.delete("/text/delete_file")
def startGame(file_id):
    return service.delete_file(file_id)

@app.post("/text/upload_file")
def upload_file(file: UploadFile):
    return service.upload_file(file)
