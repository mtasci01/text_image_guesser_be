#
FROM python:3.11.5

# 
WORKDIR /code

EXPOSE 8000

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY . .

# 
CMD ["uvicorn", "text_controller:app", "--host=0.0.0.0", "--port", "8000"]