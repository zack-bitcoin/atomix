import re
import bitcoin as b
#refunds might not work due to the transaction maliability bug.
fee=20000
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
def mk_spend_txids(wallet, dst, amount, h):
    l=len(h)
    outs = [{'value': int(amount), 'address': dst}]
    tx = b.mksend(h,outs, wallet["address"], fee)
    for i in range(l):
        tx=b.sign(tx, i, wallet["priv"])
    return(tx)
def mk_spend(wallet, dst, amount):
    h = b.history(wallet["address"])
    h = filter(lambda x: 'spend' not in x, h)
    return mk_spend_txids(wallet, dst, amount, h)
def send(wallet, dst, amount): return b.pushtx(mk_spend(wallet, dst, amount))
def txid(tx): return b.txhash(tx)
SIGHASH_ALL=1
def sign(tx, i, priv, t="default", script="", hashcode=SIGHASH_ALL):
    i = int(i)
    #if (not is_python2 and isinstance(re, bytes)) or not re.match('^[0-9a-fA-F]*$', tx):
    if not re.match('^[0-9a-fA-F]*$', tx):
        return binascii.unhexlify(custom_sign(safe_hexlify(tx), i, priv, hashcode))
    if len(priv) <= 33:
        priv = b.safe_hexlify(priv)
    pub = b.privkey_to_pubkey(priv)
    address = b.pubkey_to_address(pub)
    if t not in ["atomic_1", "atomic_2"]:
        script=b.mk_pubkey_script(address)
    if script=="": error()
    signing_tx = b.signature_form(tx, i, script, hashcode)#mk_pubkey_scrip needs to be our custom scriptn
    sig = b.ecdsa_tx_sign(signing_tx, priv, hashcode)
    txobj = b.deserialize(tx)
    if t=="atomic_1":
        txobj["ins"][i]["script"] = b.serialize_script([sig])
    if t=="atomic_2":
        old_sig = txobj["ins"][i]["script"]
        txobj["ins"][i]["script"] = b.serialize_script([old_sig, sig, 1])
    else:
        txobj["ins"][i]["script"] = b.serialize_script([sig, pub])
    return b.serialize(txobj)
def atomic_sign_2(tx, i, priv, script):
    return sign(tx, i, priv, "atomic_2", script)
def atomic_sign_1(tx, i, priv, script):
    return sign(tx, i, priv, "atomic_1", script)
def txid(tx): return b.txhash(tx)
def atomic(peer_pub, wallet, to, send, receive, secret_hash):
    tx1=mk_spend(wallet, to, send)#puts your money into the channel.
    tx=b.deserialize(tx1)
    script="6382"+peer_pub+wallet["pub"]+"82ae67a9"+secret_hash+"87"+peer_pub+"ad68"
    tx['outs'][0]['script']=script
    tx=b.serialize(tx)

    txd=txid(tx)
    txd={'output':(txd+':1'), 'block_height':None, 'value':send, 'address':wallet['address']}
    refund_tx=mk_spend_txids(wallet, wallet["address"], send-fee, [txd])
    return {"refund": refund_tx, "channel": tx, "script":script}
    #print("refund tx: " +str(refund_tx))
    #tx2=atomic_sign_1(refund_tx, 0, wallet["priv"], script)
    #print("tx2: " +str(tx2))

"6382{pubkey a}{pubkey b}82ae67a9{H(x)}87{pubkey a}ad68"
#OP_IF
#// Refund for B
#2 <pubkeyA> <pubkeyB> 2 OP_CHECKMULTISIGVERIFY
#OP_ELSE
#// Ordinary claim for A
#OP_HASH160 <H(x)> OP_EQUAL <pubkeyA> OP_CHECKSIGVERIFY
#OP_ENDIF

"{sigb}{siga}81"
"{siga}{x}00"

#steps
#0 make transaction for loading money onto channel
#1 make refund transaction nlocked into the future
#2 load money into channel
#3 new owners claim funds

def test():
    x=new_wallet_mnemonic("definition+seen+production+cause")
    #send(x, "1B5kMyVu8DtXDvs5dqScrN98kA5RE6Ws3Q", 1)
    to = new_wallet_mnemonic("loading+money+onto+channel")
    #to="1B5kMyVu8DtXDvs5dqScrN98kA5RE6Ws3Q"
    #peer_pub="04b4810b2ddd78dd8f5cf1abdf547aa527bcfd45167aab0cad9e5e8062aa63e7ebc1fce2af55fe190f05533de581974e6b14fc481cd61a39a46eb7f0027f518ea8"
    receive=10
    send=100000
    secret_hash="db1bab70f6a3e320f0d13bf46216ca9dade18e381e48000baed5775fe07b3970"#hash of "brainwallet"
    a=atomic(to["pub"], x, to["address"], send, receive, secret_hash)
    #print("a: " +str(a))
    refund=a["refund"]
    channel=a["channel"]
    refund=atomic_sign_1(refund, 0, to["priv"], a["script"])
    for i in range(len(b.deserialize(channel)["ins"])):
        channel = sign(channel, i, x["priv"])
    refund=atomic_sign_2(refund, 0, x["priv"],  a["script"])
    print("channel: " +str(channel))
    print(b.pushtx(channel))
    print(b.pushtx(refund))
    

if __name__=="__main__":
    test()
