import json
import urllib2

def new_wallet(a):
    pass
def balance(address):
    pass
def send(wallet, dst, amount):
    pass
def test():
    print(json.load(urllib2.urlopen("http://localhost:8081/get_block/0")))
    
