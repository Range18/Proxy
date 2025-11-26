from listener import Listener

ADDRESS = "127.0.0.1"
PORT = 8080

def main():
    proxy = Listener()
    proxy.listen(ADDRESS, PORT)
    while True:
        proxy.accept_connection()

if __name__ == "__main__":
    main()