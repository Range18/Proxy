CHUNK_SIZE = 65536

# Colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Traffic limit exceeded
TRAFFIC_EXCEEDED_BODY = "<html><head><title>Traffic limit exceeded</title></head>"
"<body><h1>Traffic limit exceeded</h1>"
"<p>Your daily traffic quota is over.</p>"
"</body></html>".encode("utf-8")
