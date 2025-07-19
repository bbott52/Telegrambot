import threading
import random
import time
import requests

# List of common User-Agents to simulate different devices/browsers
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0)",
    "Mozilla/5.0 (Linux; Android 9; Mi A1)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0)",
    "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL)"
]

def fake_visit(url, interval):
    def visit_loop():
        while True:
            headers = {
                "User-Agent": random.choice(user_agents)
            }
            try:
                response = requests.get(url, headers=headers, timeout=5)
                print(f"[✓] Visited: {url} - Status {response.status_code}")
            except Exception as e:
                print(f"[!] Error visiting {url}: {e}")
            time.sleep(interval)

    # Start the background thread for this link
    thread = threading.Thread(target=visit_loop)
    thread.daemon = True
    thread.start()