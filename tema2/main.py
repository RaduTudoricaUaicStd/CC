import http.server
import socketserver
from re import compile
from json import dumps, loads
from threading import Thread, Lock
from queue import Queue
from time import time, sleep
from handlers import *

request_handlers = {
	"GET":{
		"/series/[a-zA-Z0-9]+/episodes/[a-zA-Z0-9]+": get_episode,
		"/series/[a-zA-Z0-9]+/episodes": get_collection_episodes,
		"/series/[a-zA-Z0-9]+": get_series,
		"/series": get_collection_series,
	},
	"POST":{
		"/series/[a-zA-Z0-9]+/episodes/[a-zA-Z0-9]+": post_episode,
		"/series/[a-zA-Z0-9]+/episodes": post_collection_episodes,
		"/series/[a-zA-Z0-9]+": post_series,
		"/series": post_collection_series,
	},
	"PUT":{
		"/series/[a-zA-Z0-9]+/episodes/[a-zA-Z0-9]+": put_episode,
		"/series/[a-zA-Z0-9]+/episodes": put_collection_episodes,
		"/series/[a-zA-Z0-9]+": put_series,
		"/series": put_collection_series,
	},
	"DELETE":{
		"/series/[a-zA-Z0-9]+/episodes/[a-zA-Z0-9]+": delete_episode,
		"/series/[a-zA-Z0-9]+/episodes": delete_collection_episodes,
		"/series/[a-zA-Z0-9]+": delete_series,
		"/series": delete_collection_series,
	}
}

log_queue = Queue()
log_lock = Lock()

def logger():
	while True:
		log = log_queue.get()
		try:
			with log_lock:
				data = loads(open("logs").read())
		except:
			data = []
		data.append(log)
		with log_lock:
			open("logs", 'w').write(dumps(data))


t = Thread(target=logger, args = tuple())
t.daemon = True
t.start()


def parse_get_parameters(path):
	params = {}
	if not "?" in path:
		return params

	query = path[path.index("?")+1:]
	for kv_pair in query.split("&"):
		if "=" in kv_pair:
			key, value = kv_pair.split("=", 1)
			params[key.lower()] = value
		else:
			params[kv_pair.lower()] = None
	return params

class HTTPHandler(http.server.SimpleHTTPRequestHandler):
	def on_req_end(self, method, start, resp):
		latency = time() - start
		log_queue.put({
				"time": time(),
				"latency": latency,
				"resp": resp,
				"req": self.path,
				"method": method
			})
		self.send_response(resp["code"])
		self.send_header("Content-type", "application/json")
		if "headers" in resp:
			for key, header in resp["headers"].items():
				self.send_header(key, header)
		self.end_headers()
		if not resp["data"] is None:
			self.wfile.write(dumps(resp["data"]).encode('utf-8'))

	def on_request(self, method):
		start = time()
		if not method in request_handlers:
			self.on_req_end(method, start, {
				"code": 405,
				"data": {
					"status": False,
					"error": "method not allowed"
				}
			})
			return

		for pattern, function in request_handlers[method].items():
			regex = compile(pattern)
			if len(regex.findall(self.path)) > 0:
				try:
					self.on_req_end(method, start, function(self))
					return
				except Exception as e:
					self.on_req_end(method, start, {
							"code": 500,
							"data": {
								"status": False,
								"error": str(e)
							}
						})
					print(e)
					return

		self.on_req_end(method, start, {
			"code": 404,
			"data": {
				"status": False,
				"error": "path not found"
			}
		})

	def do_GET(self):
		self.on_request("GET")

	def do_POST(self):
		self.on_request("POST")

	def do_PUT(self):
		self.on_request("PUT")

	def do_DELETE(self):
		self.on_request("DELETE")


http_server = socketserver.TCPServer(("127.0.0.1", 80), HTTPHandler)
http_server.serve_forever()