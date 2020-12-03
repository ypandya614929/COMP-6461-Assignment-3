# COMP-6461-Assignment-3
COMP-6461-Assignment-3

## To setup virtualenv if not already
    
    virtualenv -p python3.8.6 env
    source env/bin/activate
    pip install -r requirements.txt

### Start Router
    - ./routers/macos/router --port=3000 --drop-rate=0.2 --seed 2387230234324
    - ./routers/macos/router --port=3000 --max-delay=100ms --seed 2387230234324
    - ./routers/macos/router --port=3000 --drop-rate=0.2 --max-delay=100ms --seed 2387230234324

### Start Server
    - python3 httpfs.py -arq -v -p 8080 -d .

### Assignment-3 Client Commands
    - python3 httpc.py get -arq -v -p 8080 "http://localhost/"
    - python3 httpc.py get -arq -v -p 8080 "http://localhost/random.json"
    - python3 httpc.py get -arq -p 8080 -o "output.json" "http://localhost/random.json"
    - python3 httpc.py post -arq -v -p 8080 --h Content-Type:application/json -d \
        "some text here" "http://localhost/demo.txt"
    - python3 httpc.py post -arq -v -p 8080 -o "output.json" \
        --h Content-Type:application/json -d "some text here" "http://localhost/demo.txt"
    - python3 httpc.py get -arq -v -p 8080 --h Content-Disposition:inline \
        "http://localhost/random.json"
    - python3 httpc.py get -arq -v -p 8080 --h Content-Disposition:attachment \
        "http://localhost/demo.txt"

### HTTP Tests
    - Please start server with "python3 httpfs.py -arq -v -p 8080 -d ." if not already running.
    - python3 tests.py

### HTTP Multithreading Tests
    - Please start server with "python3 httpfs.py -arq -v -p 8080 -d ." if not already running.
    - python3 theadtests.py

#### Note
    Please note that `-h` is reserved for help function argument in python so for header \
    we have used `--h` instead.
