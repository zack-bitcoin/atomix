import socket
import errno
import json
import select
import time
import logging

TIMEOUT = 0.1

def make_json_safe(thing):
    if isinstance(thing, (int, float, bool, str, type(None), unicode)):
        return thing
    elif isinstance(thing, list):
        return map(make_json_safe, thing)
    elif isinstance(thing, dict):
        return dict(
            map(lambda a,b: (str(a), make_json_safe(b)), *zip(*thing.items())))
    else:
        return str(thing)

def dump(a_dict):
    return json.dumps(make_json_safe(a_dict), sort_keys=True, indent=4)

class Client(object):
    def __init__(self, sock, addr):
        self.sock = sock
        self.sock.setblocking(False)
        self.addr = addr
        self.data = None

def new_client(sock, addr):
    sock.setblocking(False)
    return {"sock":sock, "addr":addr, "data":None}

def get_clients(listener, mapping):
    if select.select([listener],[],[],TIMEOUT):
        while True:
            try:
                sock, addr = listener.accept()
            except socket.error as exc:
                if exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise
                else:
                    break
            else:
                mapping[sock.fileno()] = new_client(sock, addr)

def clients_with_messages(mapping):
    if not mapping:
        time.sleep(TIMEOUT)
    else:
        for fileno in select.select(mapping, [], [], TIMEOUT)[0]:
            yield mapping[fileno]

def server_loop(listener, reader, sender, handler):
    logger = logging.getLogger(__name__)
    handle = logging.FileHandler('yashttpd.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(level)s\n%(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
    handle.setFormatter(formatter)
    #handle.setLevel(logging.INFO)
    handle.setLevel(logging.ERROR)
    logger.addHandler(handle)
    logger.info("Starting Server")
    listener.setblocking(False)
    sockets_to_read = {}
    while True:
        get_clients(listener, sockets_to_read)
        for client in clients_with_messages(sockets_to_read):
            logger.info('read message from '+str(client["addr"]))
            client["data"] = reader(client["sock"])
            logger.info(dump(client["data"]))
        for client in sockets_to_read.values():
            if isinstance(client["data"], dict):
                logger.info('processing message from '+str(client["addr"]))
                client["data"] = handler(client["data"])
        for fileno, client in sockets_to_read.items():
            if client["data"] is None:
                continue
            else:
                logger.info('sending response to '+str(client["addr"]))
                if isinstance(client["data"], int):
                    logger.debug('ERROR CODE: '+str(client["data"]))
                else:
                    logger.info(dump(client["data"]))
                #print("client: " +str(client))
                sender(client["sock"], client["data"])
                client["sock"].close()
                sockets_to_read.pop(fileno)
