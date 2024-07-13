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