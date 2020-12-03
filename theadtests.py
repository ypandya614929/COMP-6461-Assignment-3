#!/usr/bin/python
# -*- coding: utf-8 -*-

from httpclientlibrary import HTTPClientLibrary
from threading import Thread
import time

# ==================== Assignment 3 Test cases ====================


def test_asg3_getrequest(is_display=True):
    http_lib_obj = HTTPClientLibrary("http://localhost/demo.txt")
    http_lib_obj.setPort(8080)
    http_lib_obj.setArq(True)
    http_lib_obj.setMethod('get')
    http_lib_obj.setVerbose(False)
    http_lib_obj.buildRequest()
    response_obj = http_lib_obj.sendresponse()
    if is_display:
    	print(response_obj.getResponse())

def test_asg3_postrequest(is_display=False, num=0):
    http_lib_obj = HTTPClientLibrary("http://localhost/demo.txt")
    http_lib_obj.setPort(8080)
    http_lib_obj.setArq(True)
    http_lib_obj.setMethod('post')
    data = "\n{} test data for post method".format(num)
    http_lib_obj.setData(data)
    http_lib_obj.setHeader("User-Agent", "COMP-6461/1.0")
    http_lib_obj.setHeader("Content-Type", "application/plain")
    http_lib_obj.setHeader("Content-Length",str(len(data)))
    http_lib_obj.setVerbose(False)
    http_lib_obj.buildRequest()
    response_obj = http_lib_obj.sendresponse()
    if is_display:
        print(response_obj.getResponse())


# ==================== Concurrent Read ====================

for i in range(0, 3):
    Thread(target=test_asg3_getrequest, args=(True,)).start()
time.sleep(1)


# ==================== Concurrent Write ====================

for num in range(0, 3):
    Thread(target=test_asg3_postrequest, args=(True, num)).start()
time.sleep(1)


# ==================== Concurrent Read & Write ====================

# for num in range(11, 16):
#     Thread(target=test_asg2_postrequest, args=(False, num)).start()
#     Thread(target=test_asg2_getrequest, args=(True,)).start()