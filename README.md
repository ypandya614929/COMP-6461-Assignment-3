# COMP-6461-Assignment-2
COMP-6461-Assignment-2

## To setup virtualenv if not already
    
    virtualenv -p python3.7 env
    source env/bin/activate
    pip install -r requirements.txt

### HTTP Tests
    - Please start server with "python httpfs.py -v -p 8080 -d ." if not already running.
    - python tests.py

### HTTP Multithreading Tests
    - Please start server with "python httpfs.py -v -p 8080 -d ." if not already running.
    - python theadtests.py

### Assignment-2 Commands
    - python httpfs.py -h
    - python httpfs.py -d .
    - python httpfs.py -v -d .
    - python httpfs.py -p 8080 -d .
    - python httpfs.py -v -p 8080 -d .
    - python httpfs.py -v -p 8080 -d {PATH_TO_DIR}.
    - python httpc.py get -v -p 8080 "http://localhost/"
    - python httpc.py get -v -p 8080 "http://localhost/random.json"
    - python httpc.py post -v -p 8080 --h Content-Type:application/json -d \
        "some text here" "http://localhost/demo.txt"
    - python httpc.py get -v -p 8080 --h Content-Disposition:inline \
        "http://localhost/random.json"
    - python httpc.py get -v -p 8080 --h Content-Disposition:attachment \
        "http://localhost/random.json"
    - http://localhost:8080/random.json
    - http://localhost:8080/random.json?inline

#### Note
    Please note that `-h` is reserved for help function argument in python so for header \
    we have used `--h` instead.
