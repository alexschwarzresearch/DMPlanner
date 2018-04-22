FROM python:3.6.3
ADD dmplanner /dmplanner
ADD requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python", "./dmplanner/dmplanner.py"]