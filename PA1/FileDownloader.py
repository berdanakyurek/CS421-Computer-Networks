import sys
import socket

# typ=True: GET, else HEAD
def send_request(url, typ, lower = -1, upper = -1):
    host = url.split("/")[0]

    socket_to_index = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_index.connect((host, 80))

    index_path = url.split("/", 1)[1]

    typstr = "GET"

    if not typ:
        typstr = "HEAD"
    q = "%s /%s HTTP/1.1\r\nHost:%s\r\n" % (typstr, index_path, host)

    if lower != -1 and upper != -1:
        q += "Range: bytes=%d-%d\r\n" % (lower, upper)

    q += "\r\n"

    socket_to_index.send(q.encode())

    respon = socket_to_index.recv(4096).decode("utf-8")
    #print(respon)
    return respon

def download(url, lower = -1, upper = -1):

    index_response = send_request(url, True, lower, upper)

    header = index_response.split("\r\n\r\n", 1)[0]

    if "200 OK" not in header and "206 Partial Content" not in header :
        return -1

    return index_response.split("\r\n\r\n", 1)[1]

def head(url):
    header_t = send_request(url, False)
    if "200 OK" not in header_t:
        return -1

    for i in header_t.split("\n"):
        if "Content-Length:" in i:
            return int(i.split(":")[1])

def file_write(text, url):
    f = open(url.split("/")[-1], "w")
    f.write(text)
    f.close()

if len(sys.argv) != 3 and len(sys.argv) != 2 :
    print("Invalid number of arguments!")
    exit(1)

url = sys.argv[1]
print("URL of the index file:", url)
lower = -1
upper = -1

if len(sys.argv) == 3:
    try:
        lower = int(sys.argv[2].split("-")[0])
        upper = int(sys.argv[2].split("-")[1])
    except:
        print("Invalid argument.")
        exit(1)

print("Lower endpoint=", lower)
print("Upper endpoint=", upper)

response_str = download(url)

if str(response_str) == "-1":
    print("Index file not found")
    exit(1)

index_content = response_str.split("\n")[:-1]
print("Index file is downloaded")
print("There are %d files in the index" % len(index_content))

cnt = 1
for i in index_content:
    ihead = head(i)
    if ihead == -1:
        print("%d. %s is not found" % (cnt, i))
    elif lower == -1 or upper == -1:
        fileS = download(i)
        file_write(fileS, i)
        print("%d. %s is downloaded" % (cnt, i))
    elif ihead < lower:
        print("%d. %s File size(%d) < Lower endpoint(%d). File not downloaded." % (cnt, i, ihead, lower))
    else:
        fileS = download(i, lower, upper)
        file_write(fileS, i)
        print("%d. %s (range = %d-%d) is downloaded" % (cnt, i, lower, upper))
    cnt += 1
