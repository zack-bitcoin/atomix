import sys, socket, logging
from sender import sender
from reader import reader

# I want to add linux and bsd specific
# polling functions later, but windows
# version works everywhere
from windows import server_loop

def yashttpd(handler, host='0.0.0.0', port=80, connection_queue=100):
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(connection_queue)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_loop(server_socket, reader, sender, handler)

def redirect(url):
    return {'code':301, 'headers':{'Location':url}}

def set_type(response, typ):
    headers = response.get('headers', {})
    if type(headers) != dict:
        headers = {}
        logging.debug('You tried to use a non-dict for your header!')
    headers['Content-Type'] = typ
    response['headers'] = headers
