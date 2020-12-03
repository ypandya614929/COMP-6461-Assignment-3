#!/usr/bin/python
# -*- coding: utf-8 -*-

DISPLAY_MAPPING_DICT = {
    200: '200 OK',
    301: '301 Moved Permanently',
    400: '400 Bad Request',
    403: '403 Forbidden',
    404: '404 Not Found',
    502: '502 Bad Gateway'
}


class HTTPServerLibrary:
    """
    HTTPServerLibrary class used to represent all the server side operations
    Methods for Asg2
    -------
    __init__(self, url)
        It is contructor for HTTPServerLibrary class.
    setData(self, data)
        It is used to set data.
    getData(self, data)
        It is used to get data.
    setStatusCode(self, status_code)
        It is used to set status code of response.
    getStatusCode(self)
        It is used to get status code of response.
    getHeader(self, key)
        It is used to get specific header value.
    setHeader(self, key, value)
        It is used to set header value.
    buildRequestheaders(self)
        It is used to generate headers.
    response(self)
        It is used to send the response back.
    """

    def __init__(self, status_code=None):
        """It is contructor for HTTPServerLibrary class.

        Parameters
        -------
        status_code
            a int containing status_code
        """
        self.status_code = status_code
        self.data = ""
        self.header = {}

    #  From assignment-1
    def setStatusCode(self, status_code):
        """It is used to set status code of response.

        Parameters
        -------
        status_code
            a int containing status code
        """
        self.status_code = status_code

    #  From assignment-1
    def getStatusCode(self):
        """It is used to get status code of response.
        Returns
        -------
        int
            a int containing status code
        """
        return self.status_code

    #  From assignment-1
    def setData(self, data):
        """It is used to set data.
        Parameters
        -------
        data
            a string containing data
        """
        self.data = data

    #  From assignment-1
    def getData(self):
        """It is used to get data of response.
        Returns
        -------
        string
            a string containing data
        """
        return self.data

    #  From assignment-1
    def getHeader(self, key):
        """It is used to get header value.
        Returns
        -------
        string
            a string containing header key's value
        """
        return self.header.get(key)

    #  From assignment-1
    def setHeader(self, key, value):
        """It is used to set header value.
        Parameters
        -------
        key
            a string containing header name
        value
            a string containing header value
        """
        self.header.update({key: value})

    #  From assignment-1
    def buildRequestheaders(self):
        """It is used to generate headers.
        Returns
        -------
        str
            a string containing header information
        """
        header = "\r\n"
        for key, value in self.header.items():
            header += (key + ": " + value + "\r\n")
        return header

    def response(self):
        """It is used to send the response back.
        Returns
        -------
        str
            a string containing response
        """
        return "HTTP/1.0 {} {}\r\n".format(DISPLAY_MAPPING_DICT.get(self.status_code), self.buildRequestheaders())
