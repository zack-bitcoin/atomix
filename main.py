#!/usr/bin/python
import yashttpd
import json
import socket
import logging
import urlparse

import bitcoin_wallet
#definition seen production cause
pretty_html = '''\
<!DOCTYPE html>
<html>
<head>
</head>
<body onload="prettyPrint()">
<pre class="prettyprint linenums">
{}
</pre>
</body>
</html>
'''
def symbols_translate(string):
    replacements = [
        ('&', '&amp;'),
        (' ', '&nbsp;'),
        ('\t', 4*'&nbsp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ('\'', '&#39;'),
        ('"', '&quot;'),
        ('\n', '<br>')]
    for sym, repl in replacements:
        string = string.replace(sym, repl)  
    return string

def request2DB(request):
    v=request.split("&")
    DB={}
    for i in v:
        a=i.split("=")
        DB[a[0]]=a[1]
    return DB
def DB2request(DB):
    out=""
    for i in DB.keys():
        out+="&"+str(i)+"="+str(DB[i])
    return out[1:]
def db2html(db):
    out=""
    for k in db.keys():
        out+='<input type="hidden" name='+str(k)+' value='+str(db[k])+'>'
    return out

def wallet(DB, response):
    response['content']=response['content'].format("""wallet <a href='login'>log out</a>
    <form action="spend" method="POST">
    <h2>BITCOIN</h2>
    address: """+DB["address"]+"""<br>
    pubkey: """+DB["pub"]+"""<br>
    priv: """+DB["priv"]+"""<br>
    balance:  """+str(bitcoin_wallet.balance(DB["address"]))+"""
    <br>
    who to send to: 
    <input type="text" name="to" value="1B5kMyVu8DtXDvs5dqScrN98kA5RE6Ws3Q"> <br>
    amount to send: """ + db2html(DB) + """
    <input type="text" name="amount" value="0"> <br><br>
    <input type="hidden" name="brainwallet" value="brainwallet">
    <input type="submit" value="send money">
    </form> 
    """)#generate wallet
    yashttpd.set_type(response, 'text/html')
    return response
def login(DB, response):
    response['content']=response['content'].format("""
    <form action="create_wallet" method="POST">
    brainwallet:<br>
    <input type="text" name="brainwallet" value="brainwallet">
    <br><input type="submit" value="Login">
    </form>
    """)
    yashttpd.set_type(response, 'text/html')
    return response
Pages={'wallet': wallet,
       'login': login}

def home(DB, request): return yashttpd.redirect('/login')
def create_wallet(DB, response):
    wallet=bitcoin_wallet.new_wallet_mnemonic(DB["brainwallet"])
    for key in wallet:
        DB[key]=wallet[key]
    DB["amount"]=0
    return(yashttpd.redirect('/wallet?'+DB2request(DB)))

def spend(DB, request):
    print("SPENDSPND: " +str(DB))
    if int(DB["amount"])>0:
        if bitcoin_wallet.balance(DB["address"])>=int(DB["amount"]):
            bitcoin_wallet.send(DB, DB["to"], int(DB["amount"]))
    return yashttpd.redirect('/wallet?'+DB2request(DB))
DoGos={'home.html': home,
       '': home,
       'create_wallet':create_wallet,
       'spend': spend}

def fourohfour(DB, response):
    return 404
def handler(request):
    path = request['path']
    print("path: " +str(path))
    method=request["method"]
    DB={}
    if method == "GET" and "?" in path:
        a=path.split("?")
        path=a[0]
        DB=request2DB(a[1])
    if method == "POST":
        DB=request2DB(request["entity"])
    if path in DoGos.keys():
        return DoGos[path](DB, request)
    return Pages.get(path, fourohfour)(DB, {'code':200, 'content':pretty_html})
if __name__ == '__main__':
    yashttpd.yashttpd(handler, host='127.0.0.1', port=8000)
