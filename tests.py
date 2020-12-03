from httpclientlibrary import HTTPClientLibrary
import unittest
from threading import Thread

class TestCases(unittest.TestCase):

    # ==================== Assignment 1 Test cases ====================

    def test_getrequest(self):
        http_lib_obj = HTTPClientLibrary("http://httpbin.org/get?course=algorithms&labassignment=1")
        http_lib_obj.setMethod('get')
        http_lib_obj.setVerbose(True)
        http_lib_obj.buildRequest()
        response_obj = http_lib_obj.sendresponse()
        # print(response_obj.getResponse())
        self.assertEqual(response_obj.getStatusCode(), '200')

    def test_postrequest(self):
        http_lib_obj = HTTPClientLibrary("http://httpbin.org/post")
        http_lib_obj.setMethod('post')
        data = '{"Assignment":"1"}'
        http_lib_obj.setData(data)
        http_lib_obj.setHeader("User-Agent", "COMP-6461/1.0")
        http_lib_obj.setHeader("Content-Type", "application/plain")
        http_lib_obj.setHeader("Content-Length",str(len(data)))
        http_lib_obj.setVerbose(True)
        http_lib_obj.buildRequest()
        response_obj = http_lib_obj.sendresponse()
        # print(response_obj.getResponse())
        self.assertEqual(response_obj.getStatusCode(), '200')
    
    def test_redirection(self):
        http_lib_obj = HTTPClientLibrary("http://google.com/")
        http_lib_obj.setMethod('get')
        http_lib_obj.setVerbose(False)
        http_lib_obj.buildRequest()
        response_obj = http_lib_obj.sendresponse()
        # print(response_obj.getResponse())
        self.assertEqual(response_obj.getStatusCode(), '200')


    # ==================== Assignment 2 Test cases ====================

    def test_asg2_getrequest(self, is_display=False):
        http_lib_obj = HTTPClientLibrary("http://localhost/random.json")
        http_lib_obj.setPort(8080)
        http_lib_obj.setMethod('get')
        http_lib_obj.setVerbose(False)
        http_lib_obj.buildRequest()
        response_obj = http_lib_obj.sendresponse()
        if is_display:
            print(response_obj.getResponse())
        self.assertEqual(response_obj.getStatusCode(), '200')

    def test_asg2_postrequest(self, is_display=False):
        http_lib_obj = HTTPClientLibrary("http://localhost/demo.txt")
        http_lib_obj.setPort(8080)
        http_lib_obj.setMethod('post')
        data = "test data for post method"
        http_lib_obj.setData(data)
        http_lib_obj.setHeader("User-Agent", "COMP-6461/1.0")
        http_lib_obj.setHeader("Content-Type", "application/plain")
        http_lib_obj.setHeader("Content-Length",str(len(data)))
        http_lib_obj.setVerbose(False)
        http_lib_obj.buildRequest()
        response_obj = http_lib_obj.sendresponse()
        if is_display:
            print(response_obj.getResponse())
        self.assertEqual(response_obj.getStatusCode(), '200')

if __name__ == '__main__':
    unittest.main()