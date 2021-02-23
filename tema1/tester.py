from requests import get
from threading import Thread, Lock
from sys import argv
from time import time

latency = 0
success = 0

latency_lock = Lock()
success_lock = Lock()

def do_work():
	global latency
	global success

	try:
		start = time()
		r = get("http://localhost/query", params = { "ip":"1.1.1.1" }).json()
		call_latency = time() - start
		with latency_lock:
			latency += call_latency
		if r["status"]:
			success += 1
	except Exception as e:
		print(e)
		return

threads = []

for n_batches in range(int(argv[1])):
	for n_threads in range(int(argv[2])):
		t = Thread(target = do_work, args = tuple())
		t.start()
		threads.append(t)
	
	for t in threads:
		t.join()

	print("[*] Batch number:", n_batches, ";", success, "requests with success out of", argv[2], "mean latency:", latency/success)
	success = 0
	latency = 0
	threads = []
