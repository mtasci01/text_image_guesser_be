# text_image_guesser_be

1. A very simple program to practice memorizing your texts. It randomly hides words or chars. Also a docx version available in an endpoint

2. A very simple image guessing program. You will upload your image with a label. The image will be turned in a square and has a min and max length

3. A location game to guess a location being given directions to it.

py 3.11.5

#uvicorn text_controller:app --reload

pip freeze -> for requirements 

docker build -t text_image_guesser_be .

docker run -d -p 8000:8000 --name text_image_guesser_be -v path_to_file/config.ini:/code/config.ini text_image_guesser_be:latest

docker volume create --name=mongodata

docker run -d -p 27017:27017 -v mongodata:/data/db --name mongo mongo:7.0.12 

docker inspect -> ip address for address of db