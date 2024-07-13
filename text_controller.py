from fastapi import FastAPI
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
