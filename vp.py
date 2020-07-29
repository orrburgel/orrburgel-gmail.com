#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,logging,os,os.path,datetime,uuid,magic,socket,threading,requests,json,hashlib,hmac,img2pdf
from datetime import datetime
import urllib.request as urllib2
from time import sleep
from io import BytesIO
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from PIL import Image
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse,parse_qs
from selenium.common import exceptions
from json import JSONDecodeError
BUSY = False
class HTTP(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

    def do_HEAD(self):
        self._set_response()
    
    def do_GET(self):
        global BUSY
        try:
            HOST = "http://"+self.headers.get('Host')+"/"
            if self.path == "/favicon.ico":
                mime = magic.Magic(mime=True)
                self.send_header('Content-type', mime.from_file(os.getcwd()+urlparse(self.path).path) + "; charset=utf-8")
                with open(os.getcwd()+urlparse(self.path).path, 'rb') as file:
                    self.wfile.write(file.read())
                return
            elif BUSY == True:
                self._set_response()
                OUTPUT = '{"status":"busy"}'
                print(OUTPUT)
                self.wfile.write((OUTPUT).encode('utf-8'))
                return
            elif urlparse(self.path).path.lower() == "/api":
                try:
                    BODY = parse_qs(urlparse(self.path).query)['body'][0]
                except KeyError:
                    self._set_response()
                    OUTPUT = '{"status":"missing body parameter"}'
                    print(OUTPUT)
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    return
                try:
                    DATA = json.loads(BODY)
                    print("-------------------")
                    print("INCOMING REQUEST:")
                    print(BODY)
                    print("-------------------")
                    URL = DATA["url"]
                    REQUEST = DATA["request"]
                    REQUESTID = DATA["request"]["request_id"]
                    USERID = DATA["request"]["user_id"]
                    MAPID = DATA["request"]["map_id"]
                    SIGN = DATA["sign"]
                    SECERTKEY = "24d7d99cf8fcd237a2c9ebcf32097a2ce6fa06c0b66908bd51a47d2668da8eab23b8356edae18464add19bb21c13da1605d92c0bf5ef695297d6f2616c79e9b0"
                    decode_request = URL+REQUESTID+USERID+MAPID+"shellyrom.com"
                    CORRECTSIGN = hmac.new((SECERTKEY).encode('utf-8'), (decode_request).encode('utf-8'), hashlib.sha512).hexdigest()
                    print("RECIEVED SIGN:"+SIGN)
                    print("CORRECT SIGN:"+CORRECTSIGN)
                except (KeyError,JSONDecodeError) as e:
                    self._set_response()
                    OUTPUT = '{"status":"bad json formatting"}'
                    print("-------------------")
                    print(OUTPUT)
                    print("-------------------")
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    return
                if HOST in URL or "127.0.0.1" in URL or "localhost" in URL:
                    self._set_response()
                    OUTPUT = '{"status":"bad url"}'
                    print("-------------------")
                    print(OUTPUT)
                    print("-------------------")
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    return
                if not "http://" in URL and not "https://" in URL:
                    self._set_response()
                    OUTPUT = '{"status":"missing http/s"}'
                    print("-------------------")
                    print(OUTPUT)
                    print("-------------------")
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    return
                if not "shellyrom.com" in URL:
                    self._set_response()
                    OUTPUT = '{"status":"not shellyrom"}'
                    print("-------------------")
                    print(OUTPUT)
                    print("-------------------")
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    return
                if SIGN == CORRECTSIGN:
                    self._set_response()
                    OUTPUT = '{"status":"compiling"}'
                    print("-------------------")
                    print(OUTPUT)
                    print("-------------------")
                    BUSY = True
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    printer_thread = threading.Thread(target=printer, args=(HOST,URL,REQUEST,REQUESTID,USERID,MAPID,SECERTKEY))
                    printer_thread.start()
                else:
                    self._set_response()
                    OUTPUT = '{"status":"invalid sign"}'
                    print("-------------------")
                    print(OUTPUT)
                    print("-------------------")
                    self.wfile.write((OUTPUT).encode('utf-8'))
                    return
            elif self.path == "/":
                self._set_response()
                OUTPUT = '{"status":"ready"}'
                print(OUTPUT)
                self.wfile.write((OUTPUT).encode('utf-8'))
                return
            elif os.path.isfile(os.getcwd()+urlparse(self.path).path):
                mime = magic.Magic(mime=True)
                self.send_header('Content-type', mime.from_file(os.getcwd()+"/data/"+urlparse(self.path).path.replace("/data/","")) + "; charset=utf-8")
                OUTPUT = os.getcwd()+"/data/"+urlparse(self.path).path.replace("/data/","")
                with open(OUTPUT, 'rb') as file:
                    self.wfile.write(file.read())
                return
            else:
                self._set_response()
                OUTPUT = '{"status":"page not found"}'
                print(OUTPUT)
                self.wfile.write((OUTPUT).encode('utf-8'))
                return
        except (ConnectionAbortedError,ConnectionRefusedError,BrokenPipeError) as e:
            pass

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass

def printer(HOST,URL,REQUEST,REQUESTID,USERID,MAPID,SECERTKEY):
    global BUSY
    try:
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--headless")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--force-gpu-mem-available-mb=4096")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=4096,4096")
        options.add_argument('--log-level=2')
        options.add_argument("--lang=he-IL")
        options.add_experimental_option('prefs', {'intl.accept_languages': "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"})
        dc = DesiredCapabilities.CHROME
        dc['loggingPrefs'] = {'driver': 'OFF', 'server': 'OFF', 'browser': 'OFF'}
        driver = webdriver.Chrome(ChromeDriverManager().install(), desired_capabilities=dc, options=options)
        driver.get(URL)
        sleep(1)
        PageCount = driver.execute_script('return document.getElementsByClassName("ThePage").length')
        imgs = []
        a4inpt = (img2pdf.mm_to_pt(210),img2pdf.mm_to_pt(297))
        layout_fun = img2pdf.get_layout_fun(a4inpt)
        PDFFILE = str(uuid.uuid4().hex) + '_' + str(datetime.now().date()) + '_' + str(datetime.now().time()).replace(':', '.')
        for PageNumber in range(0, PageCount):
            print("Capturing Page "+str(PageNumber + 1))
            PNGFILE = str(uuid.uuid4().hex) + '_' + str(datetime.now().date()) + '_' + str(datetime.now().time()).replace(':', '.')
            S = lambda X: driver.execute_script('return document.getElementsByClassName("ThePage")['+str(PageNumber)+'].parentElement.scroll'+X)
            driver.set_window_size(S('Width')-(PageNumber+1),S('Height'))
            #driver.set_window_size(2480,3508)
            print("Width:"+str(S('Width')))
            print("Height:"+str(S('Height')))
            print(str(S('Width'))+"x"+str(S('Height')))
            #print("using size: 2480,3508")
            driver.implicitly_wait(1)
            driver.refresh()
            elem = driver.find_elements_by_class_name("ThePage")[PageNumber]
            bcode = BytesIO(elem.screenshot_as_png)
            rgb = Image.open(bcode)
            rgb = rgb.convert('RGB')
            rgb.save("data/"+PNGFILE+".png", "PNG", resoultion=100.0, quality=100)
            imgs.append("data/"+PNGFILE+".png")
        with open("data/"+PDFFILE+".pdf","wb") as f:
            f.write(img2pdf.convert(imgs, layout_fun=layout_fun))
        driver.quit()
        decode_response = HOST+"data/"+PDFFILE+".pdf"+REQUESTID+USERID+MAPID+"shellyrom.com"
        CALLBACKSIGN = hmac.new((SECERTKEY).encode('utf-8'), (decode_response).encode('utf-8'), hashlib.sha512).hexdigest()
        CALLBACK = '{"status":"compiled","pdf_url":"'+HOST+"data/"+PDFFILE+".pdf"+'","request":{"request_id":"'+REQUESTID+'","user_id":"'+USERID+'","map_id":"'+MAPID+'"},"sign":"'+CALLBACKSIGN+'"}'
        print("-------------------")
        print("REPORTING READY PDF TO API:")
        print(CALLBACK)
        payload = {'payload': CALLBACK}
        r = requests.get(url = "https://shellyrom.com/api", params = payload) 
        print("-------------------")
        try:
            data = r.json()
            print("CALLBACK RESPONSE: "+data)
            print("CALLBACK RESPONSE STATUS: "+data['status'])
        except:
            print("EMPTY CALLBACK RESPONSE!")
        print("CALLBACK RESPONSE STATUS CODE:"+str(r.status_code))
        print("-------------------")
        directory = "./data"
        files_in_directory = os.listdir(directory)
        filtered_files = [file for file in files_in_directory if file.endswith(".png")]
        for file in filtered_files:
            path_to_file = os.path.join(directory, file)
            os.remove(path_to_file)
        BUSY = False
        return
    except:
        driver.quit()
        decode_error = REQUESTID+USERID+MAPID+"shellyrom.com"
        CALLBACKSIGN = hmac.new((decode_error).encode('utf-8'), (SECERTKEY).encode('utf-8'), hashlib.sha512).hexdigest()
        CALLBACK = '{"status":"error","request":{"request_id":"'+REQUESTID+'","user_id":"'+USERID+'","map_id":"'+MAPID+'"},"sign":"'+CALLBACKSIGN+'"}'
        print("-------------------")
        print("REPORTING ERROR TO API:")
        print("Unexpected error:", sys.exc_info()[0])
        print(CALLBACK)
        payload = {'payload': CALLBACK}
        r = requests.get(url = "https://shellyrom.com/api/", params = payload) 
        print("-------------------")
        print("CALLBACK RESPONSE STATUS CODE:"+str(r.status_code))
        try:
            data = r.json()
            print("CALLBACK RESPONSE STATUS: "+data['status'])
            print("CALLBACK RESPONSE: "+data)
        except:
            print("EMPTY CALLBACK RESPONSE!")
        print("-------------------")
        BUSY = False
        return

def runHTTP(server_class=HTTPServer, handler_class=HTTP, port=80, timeout=62):
    server_address = ('', port)
    httpd = ThreadingSimpleServer(server_address, handler_class)
    httpd.timeout = timeout
    print('Virtual Printer Started.')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Virtual Printer Stopped.')

if __name__ == '__main__':
    runHTTP()