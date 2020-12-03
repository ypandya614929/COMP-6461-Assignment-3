#!/usr/bin/python
# -*- coding: utf-8 -*-

# commands
# --------
# python httpc.py -h
# python httpc.py get -h
# python httpc.py post -h
# python httpc.py get 'http://httpbin.org/get?course=networking&assignment=1'
# python httpc.py get 'http://httpbin.org/get?course=networking&assignment=1' -o output.txt
# python httpc.py get -v 'http://httpbin.org/get?course=networking&assignment=1'
# python httpc.py get -v 'http://httpbin.org/get?course=networking&assignment=1' -o output.txt
# python httpc.py post --h Content-Type:application/json -d '{"Assignment": 1}' http://httpbin.org/post
# python httpc.py post --h Content-Type:application/json -d '{"Assignment": 1}' http://httpbin.org/post -o output.txt
# python httpc.py post -v --h Content-Type:application/json -d '{"Assignment": 1}' http://httpbin.org/post
# python httpc.py post -v --h Content-Type:application/json -d '{"Assignment": 1}' http://httpbin.org/post -o output.txt
# python httpc.py post --h Content-Type:application/json -f "data.txt" "http://httpbin.org/post"
# python httpc.py post --h Content-Type:application/json -f "data.txt" "http://httpbin.org/post" -o output.txt
# python httpc.py post -v --h Content-Type:application/json -f "data.txt" "http://httpbin.org/post"
# python httpc.py post -v --h Content-Type:application/json -f "data.txt" "http://httpbin.org/post" -o output.txt
# python httpc.py get -v "http://google.com/"

import argparse
from httpclientlibrary import HTTPClientLibrary


class HTTPC:
    """
    HTTPC class used to represent all the client side operations
    Methods
    -------
    __init__(self, url)
        It is contructor for HTTPC class.
    processrequest(self)
        It is used to build and process request.
    parsingcommands(self)
        It is used to parse the commands.
    updateheader(self)
        It is used to update the header information.
    filewrite(self)
        It is used to write response in the file.
    fileread(self)
        It is used to read response from the file.
    requestconnection(self)
        It is used to create connection between HTTPClientLibrary class and
        updates it's parameters.
    response(self)
        It is used to display response on console or write in file.
    """

    def __init__(self):
        """It is contructor for HTTPC class.
        """
        self._params = None
        self._http_lib = None
        self._connection = None
        self._data = None

    def processrequest(self):
        """It is used to build and process request.
        """
        self._params = self.parsingcommands()
        self._http_lib = HTTPClientLibrary(self._params.URL)
        self._http_lib.setPort(self._params.port)
        self._connection = self.requestconnection(self._http_lib)

        while not self._data:
            self._data = self._connection.sendresponse()

        self.response()

    def parsingcommands(self):
        """It is used to parse the commands.

        Returns
        -------
        argparse
            a argparse class instance
        """
        parser = argparse.ArgumentParser(
            description="httpc is a curl-like application but supports HTTP protocol only.")
        subparsers = parser.add_subparsers(
            description='The commands are:')

        getparser = subparsers.add_parser(
            'get', help='executes a HTTP GET request and prints the response.')
        getparser.add_argument("-v", action='store_true',
                               dest="verbose", default=False,
                               help="Prints the detail of the response such as protocol, status, and headers.")
        getparser.add_argument("--h", action="append", dest='headers',
                               default=[], help="Associates headers to HTTP Request with the format 'key:value'.")
        getparser.add_argument("-o", action="store", dest="output", default="",
                               help="Allow the HTTP client to write the output response to the specified file",
                               required=False)
        getparser.add_argument("-p", action="store", dest="port", help="Port number", type=int, default=80)
        getparser.add_argument("URL", help="HTTP URL")
        getparser.add_argument("-arq", action='store_true', dest="arq", default=False, help="Automatic-Repeat-Request (ARQ)")
        getparser.set_defaults(method='get')

        postparser = subparsers.add_parser(
            'post', help='executes a HTTP POST request and prints the response.')
        postparser.add_argument("-v", action='store_true', dest="verbose", default=False,
                                help="Prints the detail of the response such as protocol, status, and headers.")
        postparser.add_argument("--h", action="append", dest="headers", default=[],
                                help="Associates headers to HTTP Request with the format 'key:value'.")
        group = postparser.add_mutually_exclusive_group(required=False)
        group.add_argument("-d", action="store", dest="data",
                           help="Associates an inline data to the body HTTP POST request.")
        group.add_argument("-f", action="store", dest="file", default="",
                           help="Associates the content of a file to the body HTTP POST request.")
        postparser.add_argument("-o", action="store", dest="output",
                                default="", help="Allow the HTTP client to write the output response to the specified file",
                                required=False)
        postparser.add_argument("-p", action="store", dest="port", help="Port number", type=int, default=80)
        postparser.add_argument("URL", help="HTTP URL")
        postparser.add_argument("-arq", action='store_true', dest="arq", default=False, help="Automatic-Repeat-Request (ARQ)")
        postparser.set_defaults(method='post')

        helpparser = subparsers.add_parser('help', help='prints this screen.')

        return parser.parse_args()

    def updateheader(self, headerlist=[]):
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
                    value = key_value[1]
                    header.update({key: value})
                except Exception:
                    continue
        return header

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
        f = open(filename, 'w')
        f.write(filedata)
        f.close()

    def fileread(self, filename):
        """It is used to read response from the file.

        Parameters
        -------
        filename
            a string containing filename
        """
        data = None
        try:
            f = open(self._params.file, 'r')
            data = f.read()
            f.close()
        except Exception:
            pass
        return data

    def requestconnection(self, http_lib_obj):
        """It is used to create connection between HTTPClientLibrary 
        class and updates it's parameters.

        Returns
        -------
        HTTPClientLibrary
            a HTTPClientLibrary class instance for connectivity
        """
        header = {}
        http_lib_obj.setMethod(self._params.method)
        http_lib_obj.setArq(self._params.arq)
        http_lib_obj.setHeader("User-Agent", "COMP-6461/1.0")

        if self._params.method.upper() == "POST":
            data = ""
            if self._params.data:
                data = self._params.data
                http_lib_obj.setData(data)
            if self._params.file:
                data = self.fileread(self._params.file)
                http_lib_obj.setFile(data)
            http_lib_obj.setHeader("Content-Length", str(len(data)))

        verbose = self._params.verbose if self._params.verbose else False
        http_lib_obj.setVerbose(verbose)

        if self._params.headers:
            headers = self.updateheader(self._params.headers)
            for key, value in headers.items():
                http_lib_obj.setHeader(key, value)

        http_lib_obj.buildRequest()
        return http_lib_obj

    def response(self):
        """It is used to display response on console or write in file.
        """
        consoledata = self._connection.getResponse()
        if self._params.output:
            self.filewrite(self._params.output, consoledata)
            print("=============== Output saved. ===============")
        else:
            print("\nOutput:\n\n" + consoledata)


if __name__ == '__main__':
    # main method
    httpc_obj = HTTPC()
    httpc_obj.processrequest()
