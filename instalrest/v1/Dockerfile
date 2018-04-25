FROM python:3.5.3
COPY . /code
WORKDIR /code
RUN apt-get update && apt-get install -y \
libpq-dev \
libstdc++6 \
libgcc-4.9-dev \
g++ \
gcc
RUN pip install .
RUN pip install -i http://127.0.0.1:6789/ instal
RUN pip install -r instalrest/requirements.txt
CMD ["python", "instalrest/v1/api.py"]