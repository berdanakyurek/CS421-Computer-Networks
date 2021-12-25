import sys
import socket
import threading

def file_write(text, url):
    f = open(url.split("/")[-1], "w")
    f.write(text)
    f.close()

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
    expected_len = -1
    respon = ""
    get = "a"
    while(get != ""):
        if expected_len == -1 and "\r\n\r\n" in respon:
            if not typ:
                #print("head shortcut")
                return respon
            rh = respon.split("\r\n\r\n",1)[0]
            if "200 OK" not in rh and "206 Partial Content" not in rh:
                print("problem")
                return respon
            for i in respon.split("\r\n\r\n")[0].split("\n"):
                if "Content-Length:" in i:
                    expected_len = int(i.split(":", 1)[1])
                    break
        if  "\r\n\r\n" in respon and len(respon.split("\r\n\r\n", 1)[1]) == expected_len:
            #print("Shortcut")
            break
        try:
            socket_to_index.settimeout(1)
            get = socket_to_index.recv(4096).decode("utf-8")
            socket_to_index.settimeout(None)
            respon += get
        except:
            #print("Timeout")
            #print()
            break

    return respon

def download(url, lower = -1, upper = -1, tmt = 0.1):

    index_response = send_request(url, True, lower, upper)

    header = index_response.split("\r\n\r\n", 1)[0]
    #print(header)

    if "200 OK" not in header and "206 Partial Content" not in header :
        return -1

    return index_response.split("\r\n\r\n", 1)[1]

def head(url):
    header_t = send_request(url, False)
    if "200 OK" not in header_t:
        return -1

    #print(header_t)
    for i in header_t.split("\n"):
        if "Content-Length:" in i:
            return int(i.split(":")[1])
    return 0

def thread_function(url, lower, upper, thread_no, arr):
    arr[thread_no] = -1
    while arr[thread_no] == -1:
        arr[thread_no] = download(url, lower, upper)
    # print("Thread %d downloaded %d bytes"%(thread_no, len(arr[thread_no])))




if len(sys.argv) != 3:
    print("Invalid Syntax!")
    print("Correct syntax:")
    print("python3 ParallelFileDownloader.py <index_file> <connection_count>")
    exit()
if int(sys.argv[2]) < 1:
    print("Connection count must be at least 1!")
    exit()

print("URL of the index file: %s"%sys.argv[1])
print("Number of parallel connections: %s"%sys.argv[2])
# rs = download("www.textfiles.com/games/arcana.txt", True)
# print(rs)
# exit() ###############
index_path = sys.argv[1]
connection_count = sys.argv[2]

#print(index_path, connection_count)

## send GET to index file


resp = download(index_path, -1, -1, 1)

if str(resp) == "-1":
    print("Index file not found")
    exit()

urls = resp.strip().split("\n")

print("Index file is downloaded")
print("There are %d files in the index" % len(urls))

cnt = 1
for url in urls:
    url_head = head(url)
    if url_head == -1:
        print("%d. %s is not found" % (cnt, url))
    elif url_head == 0:
        print("%d. %s (size = %s) is downloaded"%(cnt, url, url_head ))
        file_write("", url)
    else:
        #print(url_head)
        threads = []
        parts = []
        for i in range(int(connection_count)):
            parts.append("")
        size = 0
        n = url_head
        k = int(connection_count)
        print("%d. %s (size = %s) is downloaded"%(cnt, url, url_head ))
        print("File parts: ", end="")
        for i in range(int(connection_count)):
            bytes_to_download = 0
            if n % k == 0:
                bytes_to_download = n / k
            else:
                if i < n - (n//k)*k:
                    bytes_to_download = n//k+1
                else:
                    bytes_to_download = n //k
            # bytes to download constructed here
            #print("Thread %d, %d bytes to download" %(i, bytes_to_download))
            lower = 0
            if i == 0:
                lower = 0
            else:
                lower = upper + 1

            upper = lower + bytes_to_download - 1
            threads.append(threading.Thread(target=thread_function, args=(url, lower,upper, i, parts)))
            threads[-1].start()
            print("%d:%d(%d)"%(lower, upper, bytes_to_download), end="")
            if i != int(connection_count) - 1:
                print(", ", end="")
        print()
        for i in threads:
            i.join()

        # Array contains the data now
        result = ""
        for i in parts:
            result += i

        print(len(result), url_head)


        file_write(result, url)

    cnt += 1
#print(lst)
