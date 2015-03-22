import bitcoin as b

def new_wallet_mnemonic(brainwallet):
    a=b.sha256(brainwallet)
    return new_wallet(a)
def new_wallet(a):
    c=b.privtopub(a)
    d=b.pubtoaddr(c)
    return {"priv": a,
            "pub": c,
            "address": d}
def balance(address):
    v=b.unspent(address)
    out=0
    for i in v:
        out+=i["value"]
    return out
def send(wallet, dst, amount):
    h = b.history(wallet["address"])
    print("h: " +str(h))
    outs = [{'value': int(amount), 'address': dst}]
    tx = b.mksend(h,outs, wallet["address"], 10000)
    tx2 = b.sign(tx,0,wallet["priv"])
    b.pushtx(tx2)
def test():
    x=new_wallet_mnemonic(raw_input("your brain wallet password: "))
    print balance(x["address"])
#test()
