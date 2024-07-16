# text_image_guesser_be

1. A very simple program to practice memorizing your texts.

2. A very simple image guessing program. The file to upload is a csv with 2 fields, the path to the image and the label you want guessed
the image will be resized to a square to fit the number of segments         

#uvicorn text_controller:app --reload

docker build -t text_image_guesser_be .

docker run -d -p 8000:8000 --name text_image_guesser_be -v path_to_file/config.ini:/code/config.ini text_image_guesser_be
docker run -d -p 27017:27017 --name mongo mongo:7.0.12