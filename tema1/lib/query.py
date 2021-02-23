from requests import get
from os import environ
from time import time
import socketserver
import http.server

SHODAN_KEY = environ["SHODAN_KEY"]
VT_KEY = environ["VT_KEY"]

BASE_SHODAN_URL = "https://api.shodan.io"
BASE_VT_URL = "https://www.virustotal.com/vtapi/v2"

shodan_cache = {}
vt_cache = {}

SHODAN_CACHE_TIMEOUT = 60
VT_CACHE_TIMEOUT = 60

def send_dns_request(domain):
	for i in range(5):
		try:
			req = get('https://cloudflare-dns.com/dns-query', headers = {
					'accept':'application/dns-json'
				}, params = {
					'name': domain
				})
			if not "Answer" in req.json().keys():
				continue
			
			ip_list = []
			for resp in req.json()["Answer"]:
				ip_list.append(resp["data"])
			
			return ip_list
		except:
			continue
	return None

def query_shodan(ip):
	if ip in shodan_cache:
		if (time() - shodan_cache[ip]["time"]) < SHODAN_CACHE_TIMEOUT:
			return shodan_cache[ip]["response"]
	shodan_response = get(BASE_SHODAN_URL+"/shodan/host/"+ip, params = { "key": SHODAN_KEY })
	shodan_cache[ip] = {
		"time": time(),
		"response": shodan_response.json()
	}
	return shodan_response.json()

def query_virustotal(ip):
	if ip in vt_cache:
		if (time() - vt_cache[ip]["time"]) < VT_CACHE_TIMEOUT:
			return vt_cache[ip]["response"]
	vt_response = get(BASE_VT_URL+"/ip-address/report", params = {"apikey": VT_KEY, "ip":ip})
	vt_cache[ip] = {
		"time": time(),
		"response": vt_response.json()
	}
	return vt_response.json()

def query_info_about_ip(ip):
	return query_shodan(ip), query_virustotal(ip)

