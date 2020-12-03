#!/usr/bin/python
# -*- coding: utf-8 -*-

# commands
# --------
# python httpfs.py -h
# python httpfs.py -d .
# python httpfs.py -v -d .
# python httpfs.py -p 8080 -d .
# python httpfs.py -v -p 8080 -d .
# python httpfs.py -v -p 8080 -d {PATH_TO_DIR}.
# python httpc.py get -v -p 8080 "http://localhost/"
# python httpc.py get -v -p 8080 "http://localhost/random.json"
# python httpc.py post -v -p 8080 --h Content-Type:application/json -d "some text here" "http://localhost/demo.txt"
# python httpc.py get -v -p 8080 --h Content-Disposition:inline "http://localhost/random.json"
# python httpc.py get -v -p 8080 --h Content-Disposition:attachment "http://localhost/random.json"
# http://localhost:8080/random.json
# http://localhost:8080/random.json?inline


import socket
from threading import Thread
import argparse
import os
import json
import pathlib
from httpserverlibrary import HTTPServerLibrary
import magic
from lockfile import FileLock
import rsocket as arq_socket


MAPPING_DICT = {
    200: 'OK',
    301: 'Moved Permanently',
    400: 'Bad Request',
    403: 'Forbidden',
    404: 'Not Found',
    502: 'Bad Gateway'
}


class HTTPF:
    """
    HTTPF class used to represent all the operations
    Methods
    -------
    __init__(self, url)
        It is contructor for HTTPF class.
    run(self)
        It is used to store the parsed values and 
        start further execution
    process_header_request(self, data, http_s_obj)
        It is used to build and process request to
        determine header values.
    parsingcommands(self)
        It is used to parse the commands.
    get_actual_path(self, path)
        It is used to correct the path location
        and return updated path.
    check_and_print_debug_message(self, msg)
        It is used to print logs.
    updateheader(self, headerlist, http_s_obj)
        It is used to update the header information.
    filewrite(self)
        It is used to write response in the file.
    fileread(self)
        It is used to read response from the file.
    process_GET_request(self, path, http_s_obj)
        It is used to process a POST method request.
    start(self)
        It is used to start the socket server.
    process_POST_request(self, path, data, http_s_obj)
        It is used to process a POST method request.
    content_header_disposition(self, query, http_s_obj)
        It is used to update disposition header.
    process_http_request(self, c, addr)
        It is used to process http request.
    """

    def __init__(self):
        """It is contructor for HTTPF class.
        """
        self._params = None

    def run(self):
        """It is used to store the parsed values and 
        start further execution
        """
        self._params = self.parsingcommands()
        self.start()

    #  From assignment-1
    def parsingcommands(self):
        """It is used to parse the commands.

        Returns
        -------
        argparse
            a argparse class instance
        """
        parser = argparse.ArgumentParser(
            description="httpfs is a simple file server.")
        parser.add_argument("-v", action="store_true", dest="debug",
                            help="Prints debugging messages.", default=False)
        parser.add_argument("-p", action="store", dest="port",
                            help="Specifies the port number that the server will listen and serve at. Default is 8080.",
                            type=int, default=8080)
        parser.add_argument("-d", action="store", dest="path_to_dir",
                            help="Specifies the directory that the server will use to read/writerequested files. \
                            Default is the current directory when launching theapplication.",
                            default='./')
        parser.add_argument("-arq", action='store_true', dest="arq", default=False, help="Automatic-Repeat-Request (ARQ)")

        return parser.parse_args()

    def get_actual_path(self, path):
        """It is used to correct the path location
        and return updated path.

        Parameters
        -------
        path
            a string containing path location

        Returns
        -------
        string
            path variable containing string value of 
            location
        """
        if self._params.path_to_dir[-1] != '/':
            if path:
                path = self._params.path_to_dir + '/' + path
                path = path.replace('//', '/')
        return path

    def check_and_print_debug_message(self, msg):
        """It is used to print logs.

        Parameters
        -------
        msg
            a string containing log message
        """
        if self._params.debug:
            print("Info: {}".format(msg))

    #  From assignment-1
    def fileread(self, filename):
        """It is used to read response from the file.

        Parameters
        -------
        filename
            a string containing filename
        """
        data = None
        f = open(filename, 'r')
        data = f.read()
        f.close()
        try:
            data = data.decode()
        except (UnicodeDecodeError, AttributeError):
            data = data.encode("utf-8")

        return data

    #  From assignment-1
    def filewrite(self, filename, data):
        """It is used to write response in the file.

        Parameters
        -------
        filename
            a string containing filename
        data
            file data to write it into file
        """
        try:
            filedata = data.decode("utf-8")
        except Exception:
            filedata = data
        lock = FileLock(filename)
        lock.acquire()
        with open(filename, 'w+') as f:
            f.write(filedata)
        lock.release()

    def process_GET_request(self, path, http_s_obj):
        """It is used to process a GET method request.

        Parameters
        -------
        path
            a string containing path location
        http_s_obj
            a object of HTTPServerLibrary class

        Returns
        -------
        HTTPServerLibrary
            a object of HTTPServerLibrary class
        """
        try:
            self.check_and_print_debug_message("GET directory path: " + path)
            if path[-1] == '/':
                http_s_obj.setData(json.dumps(
                    os.listdir(path)).encode("utf-8"))
                http_s_obj.setHeader("Content-Type", "application/json")
                http_s_obj.setHeader('Content-Disposition', 'inline')
                http_s_obj.setStatusCode(200)
            else:
                if os.path.exists(path):
                    http_s_obj.setStatusCode(200)
                    mime_type = magic.from_file(path, mime=True)
                    http_s_obj.setHeader("Content-Type", mime_type)
                    data = self.fileread(path)
                    http_s_obj.setData(data)
                    http_s_obj.setHeader("Content-Length", str(len(data)))
                else:
                    http_s_obj.setStatusCode(404)
                    http_s_obj.setData(MAPPING_DICT.get(404))
        except Exception as e:
            self.check_and_print_debug_message(str(e))
            http_s_obj.setStatusCode(400)
            http_s_obj.setData(MAPPING_DICT.get(400))

        return http_s_obj

    def process_POST_request(self, path, data, http_s_obj):
        """It is used to process a POST method request.

        Parameters
        -------
        path
            a string containing path location
        data
            a string containing data
        http_s_obj
            a object of HTTPServerLibrary class

        Returns
        -------
        HTTPServerLibrary
            a object of HTTPServerLibrary class
        """
        try:
            self.check_and_print_debug_message("POST directory path: " + path)
            pathlib.Path(os.path.dirname(path)).mkdir(
                parents=True, exist_ok=True)
            self.filewrite(path, data)
            http_s_obj.setStatusCode(200)
            http_s_obj.setData("Data saved successfully.")
        except Exception as e:
            self.check_and_print_debug_message(str(e))
            http_s_obj.setStatusCode(400)
            http_s_obj.setData(MAPPING_DICT.get(400))

        return http_s_obj

    def content_header_disposition(self, query, http_s_obj):
        """It is used to update disposition header.

        Parameters
        -------
        query
            a string containing query location
        http_s_obj
            a object of HTTPServerLibrary class

        Returns
        -------
        HTTPServerLibrary
            a object of HTTPServerLibrary class
        """
        if (query and (query.find('inline') != -1)) or (http_s_obj.getStatusCode() != 200):
            http_s_obj.setHeader('Content-Disposition', 'inline')

    def process_http_request(self, c, addr):
        """It is used to process http request

        Parameters
        -------
        c
            a connection object for sending and receiving data
        addr
            a string containing address/location of client.
        """
        self.check_and_print_debug_message(
            'New Client connected: ' + str(addr))
        is_processed = False
        try:
            while not is_processed:
                if self._params.arq:
                    data = c.recvall().decode("utf-8")
                else:
                    data = c.recv(2048).decode("utf-8")
                if data:
                    http_s_obj = HTTPServerLibrary()
                    http_s_obj.setHeader('Content-Disposition', 'attachment')
                    parse_dict = self.process_header_request(data, http_s_obj)
                    self.check_and_print_debug_message("Request Type: " + parse_dict.get('type', ''))
                    self.check_and_print_debug_message("Request Path: " + parse_dict.get('path', ''))
                    self.check_and_print_debug_message("Request Query: " + parse_dict.get('query', ''))
                    self.check_and_print_debug_message("Request Body: " + parse_dict.get('data', ''))
                    self.check_and_print_debug_message("Request Headers: " + str(parse_dict.get('headers', '')))
                    if ".." not in parse_dict.get('path'):
                        path = self.get_actual_path(parse_dict.get('path', ''))
                        method = parse_dict.get('type', '')
                        if method:
                            if method.upper() == 'GET':
                                http_s_obj = self.process_GET_request(
                                    path, http_s_obj)
                            elif method.upper() == 'POST':
                                http_s_obj = self.process_POST_request(
                                    path, parse_dict.get('data', ''), http_s_obj)
                            else:
                                http_s_obj.setStatusCode(400)
                                http_s_obj.setData(MAPPING_DICT.get(400))
                    else:
                        self.check_and_print_debug_message(
                            "Info: Forbidden " + path)
                        http_s_obj.setStatusCode(403)
                        http_s_obj.setData(MAPPING_DICT.get(403))

                    self.content_header_disposition(
                        parse_dict.get('query', ''), http_s_obj)
                    self.check_and_print_debug_message(
                        "Response: " + http_s_obj.response())
                    if self._params.arq:
                        c.sendall(http_s_obj.response().encode("utf-8"), False)
                    else:
                        c.sendall(http_s_obj.response().encode("utf-8"))
                    res_data = http_s_obj.getData()
                    try:
                        c.sendall(res_data.encode("utf-8"))
                    except Exception as e:
                        c.sendall(res_data)
                    is_processed = True
                else:
                    is_processed = True
        except Exception as e:
            self.check_and_print_debug_message(
                "Something went wrong: " + str(e))
            c.close()
        finally:
            self.check_and_print_debug_message(
                "HTTP Client connection is closed.")
            c.close()

    def process_header_request(self, request, http_s_obj):
        """It is used to build and process request to
        determine header values.

        Parameters
        -------
        request
            a dict containing request
        http_s_obj
            a object of HTTPServerLibrary class

        Returns
        -------
        dict
            a response_dict containing headers.
        """
        response_dict = {}
        data = request.split("\r\n\r\n")
        header_info = data[0].split("\r\n")
        headers = self.updateheader(header_info, http_s_obj)
        response_dict.update({'type': header_info[0].split()[0]})
        response_dict.update({'headers': headers})
        body = data[1]
        response_dict.update({'data': body})
        path = header_info[0].split()[1]
        if path.find('?') != -1:
            split_sym = '?'
        if path.find('&') != -1:
            split_sym = '&'
        try:
            req = path.split(split_sym)
            path = req[0]
            query = req[1]
        except Exception as e:
            query = ''
        response_dict.update({'path': path})
        response_dict.update({'query': query})

        return response_dict

    def start(self):
        """It is used to start the socket server.
        """
        if self._params.arq:
            s = arq_socket.rsocket()
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('', self._params.port))
            s.listen(5)
            self.check_and_print_debug_message(
                'HTTP Server is running on port: ' + str(self._params.port))
            while True:
                c, addr = s.accept()
                Thread(
                    target=self.process_http_request,
                    args=(c, addr)
                ).start()
        except Exception as e:
            self.check_and_print_debug_message(str(e))
            s.close()
        finally:
            self.check_and_print_debug_message(
                "HTTP Server connection is closed.")
            s.close()

    #  From assignment-1
    def updateheader(self, headerlist=[], http_s_obj=None):
        """It is used to update the header information.

        Returns
        -------
        dict
            a dict contains header key value pairs.
        """
        header = {}
        for headerparam in headerlist:
            key_value = headerparam.split(":", 1)
            if len(key_value) == 2:
                try:
                    key = key_value[0]
                    value = key_value[1].strip()
                    header.update({key: value})
                    if http_s_obj:
                        if http_s_obj.header.get(key):
                            http_s_obj.header.update({key: value})
                except Exception:
                    continue
        return header

if __name__ == '__main__':
    # main method
    httpf_obj = HTTPF()
    httpf_obj.run()
