from requests import get
from os import environ
import http.server
import socketserver
from lib.query import send_dns_request, query_info_about_ip
from re import compile
from pdfkit import from_string as pdf_from_string, configuration as pdf_config
from hashlib import md5
from requests import post
from os.path import basename, isfile
from json import dumps, loads
from threading import Thread, Lock
from queue import Queue
from time import time, sleep
from base64 import b64encode

get_request_handlers = {}
ip_regex = compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
pdf_config = pdf_config(wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
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

ANONYMFILES_URL = "https://api.anonfiles.com/upload"

def upload_file(filename):
	with open(filename, 'rb') as file:
		return post(ANONYMFILES_URL, files = {"file":file}).text.encode('utf-8')

class HTTPHandler(http.server.SimpleHTTPRequestHandler):
	def on_req_end(self, start, resp):
		latency = time() - start
		log_queue.put({
				"time": time(),
				"latency": latency,
				"resp": resp,
				"req": self.path
			})


	def do_GET(self):
		start = time()
		for pattern, function in get_request_handlers.items():
			regex = compile(pattern)
			if len(regex.findall(self.path)) > 0:
				try:
					self.on_req_end(start, function(self))
					return
				except Exception as e:
					print(e)
					self.send_response(500)
					self.send_header("Content-type", "text/html")
					self.end_headers()
					self.wfile.write(dumps({
							"status": False,
							"error": str(e)
						}).encode('utf-8'))
					self.on_req_end(start, {
							"status": False,
							"error": str(e)
						})
					return

		self.send_response(404)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.on_req_end(start, {})

def run_query(server):
	html_page = """
		<!DOCTYPE html>
		<html>
			<body>
				%s
			</body>
		</html>

	"""
	result_template = """
			<p><h1>IP: %s</h1></p>
			<p><h3>Ports open: %s</h3></p>
			<p><h3>Resolutions: </h3></p>
			<p>
				<ol>
					%s
				</ol>
			</p>
			<p><h3>Downloaded samples: </h3></p>
			<p>
				<ol>
					%s
				</ol>
			</p>
			<p><h3>URLS:</h3></p>
			<p>
				<ol>
					%s
				</ol>
			</p>
	"""
	resolution_template = "<li>%s at %s</li>"
	sample_template = "<li>%s positives %s total %s</li>"
	url_info = "<li>%s positives %s total %s at %s</li>"

	params = parse_get_parameters(server.path)
	ips = []
	if "domain" in params:
		ips = send_dns_request(params["domain"])
	elif "ip" in params:
		ips = ip_regex.findall(params["ip"])
	else:
		server.send_response(400)
		server.send_header("Content-type", "text/json")
		server.end_headers()
		server.wfile.write(dumps({"status":False, "error":"No api data given"}).encode('utf-8'))
		return {"status":False, "error":"No api data given"}

	results = []
	for ip in ips:
		shodan, virustotal = query_info_about_ip(ip)
		if "ports" in shodan:
			ports = ", ".join([ str(port) for port in shodan["ports"] ])
		else:
			ports = ""
		if "resolutions" in virustotal:
			resolutions = "\n".join([
					resolution_template % (res['hostname'], res['last_resolved']) for res in virustotal["resolutions"]
				])
		else:
			resolutions = ""

		if "detected_downloaded_samples" in virustotal:
			samples = "\n".join([
				sample_template % (smp["sha256"], smp["positives"], smp["total"]) for smp in virustotal["detected_downloaded_samples"]
			])
		else:
			samples = ""

		if "detected_urls" in virustotal:
			urls = "\n".join([
					url_info % (url["url"], url["positives"], url["total"], url["scan_date"]) for url in virustotal["detected_urls"]
				])
		else:
			urls = ""

		results.append(result_template % (ip, ports, resolutions, samples, urls))
	html_page = html_page % ("<hr/>".join(results))
	report_pdf = "reports\\"+md5(html_page.encode('utf-8')).hexdigest()+".pdf"
	pdf_from_string(html_page, report_pdf, configuration = pdf_config)
	upload_resp = upload_file(report_pdf)
	server.send_response(200)
	server.send_header("Content-type", "text/json")
	server.end_headers()
	server.wfile.write(upload_resp)
	return upload_resp.decode('utf-8')

def serve_index(server):
	server.send_response(200)
	server.send_header("Content-type", "text/html")
	server.end_headers()
	with open("files\\index.html", 'rb') as file:
		server.wfile.write(file.read())

def serve_files(server):
	filename = "files\\"+basename(server.path)
	if not isfile(filename):
		self.send_response(404)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		return {}
	
	self.send_response(200)
	self.send_header("Content-type", "text/html")
	self.end_headers()

	with open(filename, 'rb') as file:
		self.wfile.write(file.read())
	return {}


def show_metrics(server):
	with log_lock:
		logs = loads(open("logs").read())
		data = {"mean_latency": sum([ log["latency"] for log in logs ])/len(logs), "total_requests": len(logs)}
		server.send_response(200)
		server.send_header("Content-type", "text/json")
		server.end_headers()
		server.wfile.write(dumps(data).encode("utf-8"))
		return data

get_request_handlers = {
	"/query": run_query,
	"/files/.*": serve_files,
	"/metrics": show_metrics,
	"/": serve_index
}



http_server = socketserver.TCPServer(("127.0.0.1", 80), HTTPHandler)
http_server.serve_forever()