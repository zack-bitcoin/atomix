import socket
import errno
import collections
import re

REQUEST = re.compile(
    '^(?P<method>OPTIONS|GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT) '
    '/(?P<path>.*?) '
    '(?P<version>HTTP/1\.1)\r\n'
)
MULTILINE = re.compile(r'\r\n\s+')
HEADERS = re.compile(r'(?P<name>[\w\-]*?):\s+(?P<value>.*?)\r\n')

def reader(client):
    '''
    Attempts to parse an HTTP message from client into a JSON object.
    '''
    ## Requests should totatally fit within the recv buffer
    size = client.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    ## Sometimes the client isn't really ready to be read,
    ## even though epoll says it is. So this just repeatedly
    ## tries to read stuff until it works or breaks.
    while True:
        try:
            message = client.recv(size)
        except socket.error as e:
            err = e.args[0]
            if err not in [errno.EAGAIN,errno.EWOULDBLOCK]:
                logging.exception(e)
                return 0
        else:
            break

    #if message.strip()=="":
    #    return {"type":"keepalive", "value":None}
    ## This checks for a proper request line and parses it
    ## at the same time. If there is no proper request line,
    ## an error is returned.
    request_check = REQUEST.search(message)
    if request_check is None:
        return 400

    ## This makes sure there is an end to the headers in the
    ## request. If there isn't, and error is returned!
    header_end = message.find("\r\n\r\n")
    if header_end == -1:
        return 400

    ## Next, any headers spanning multiple lines are turned
    ## into headers spanning one line only. 
    def repl(match):
        a, b = match.span()
        if b <= header_end:
            return ","
        else:
            return message[a:b]
    message = MULTILINE.sub(repl, message)

    request = collections.defaultdict(dict,request_check.groupdict())
    request["type"] = "request"
    last_match_end = request_check.span()[1]
    for match in HEADERS.finditer(message):
        match_start, match_end = match.span()
        ## It is bad to have junk between headers!
        if match_start != last_match_end:
            return 400
        ## don't look past the end of the headers
        if match.span()[1] <= header_end+2:
            request['headers'].update([match.groups()])
            last_match_end = match_end
        else:
            break

    ## Anything left over is just added to the result.
    ## This might be empty!!!
    request['entity'] = message[header_end+4:]
    return request

