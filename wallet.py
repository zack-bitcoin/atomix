from bitcoin import *
 
 
class Wallet:
 
    priv = ""
    pub = ""
    address = ""
 
    def createWallet(self,brainwalletpassword):
        self.priv = sha256(brainwalletpassword)
        self.pub = privtopub(self.priv)
        self.address = pubtoaddr(self.pub)
 
        print "Address : " + self.address
 
    def balance(self):
        print unspent(self.address)
 
    def sendBTC(self,dst, amount):
        h = history(self.address)
        #print h
        outs = [{'value': amount, 'address': dst}]
        tx = mksend(h,outs, self.address, 10000)
        tx2 = sign(tx,0,self.priv)
        pushtx(tx2)
 
x = Wallet()
 
password = raw_input("Your brain wallet password: ")
x.createWallet(password)
 
x.balance()
 
#x.sendBTC('1A1bBJwQMsbEbdyAnfe1ESvVAM3hmB6fSC', 20000)
