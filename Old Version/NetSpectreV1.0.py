import ipaddress
import subprocess
import platform
import socket
import re
from pathlib import Path
import threading
from queue import Queue

from concurrent.futures import ThreadPoolExecutor, as_completed



def main():
    print("")
    print("")
    print("   XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    print("   XX-----------------------------------------------------------XX")
    print("   XX-----------------------------------------------------------XX")
    print("   XX-------NNN------NNN------SSSSSSSSS------PPPPPPPPPPP--------XX")
    print("   XX-------NNNN-----NNN-----SS--------S-----PP--------PP-------XX")
    print("   XX-------NN-NN----NNN-----SS--------------PP--------PP-------XX")
    print("   XX-------NN--NN---NNN------SSSSSSSS-------PPPPPPPPPPP--------XX")
    print("   XX-------NN---NN--NNN--------------SS-----PP-----------------XX")
    print("   XX-------NN----NN-NNN-----S--------SS-----PP-----------------XX")
    print("   XX-------NN-----NNNNN------SSSSSSSSS------PP-----------------XX")
    print("   XX-----------------------------------------------------------XX")
    print("   XX------------------- NetSpectre v1.0 -----------------------XX")
    print("   XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    print("                                                                  ")
    print("                                                       -FurkanT   ")
    print("1 - Network Scanner")
    print("2 - Port Scanner (TCP)")
    print("3 - Exit")
    print("")
    print("")
    choice = input("Choose One : ").strip()

    if choice == "1":
        network_scanner()
    elif choice == "2":
        port_scanner()
    elif choice == "3":
        print("")
        print("See you...")
    else:
        print("Choose 1 , 2 or 3!")
        main()

def network_scanner() :
    def ping(ip):
        system = platform.system().lower()

        if system == "windows":
            command = ["ping", "-n", "1", "-w", "1000", str(ip)]  # -w: timeout 1000ms
        else:
            command = ["ping", "-c", "1", "-W", "1", str(ip)]  # -W: timeout 1s (Linux/macOS)

        try:
            subprocess.check_output(command, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_hostname(ip):
        try:
            hostname = socket.gethostbyaddr(str(ip))[0]
            return hostname
        except socket.herror:
            return "Hostname not found"

    def get_mac_address(ip):
        try:
            if platform.system().lower() == "windows":
                output = subprocess.check_output(f"arp -a {ip}", shell=True, encoding='utf-8')
                match = re.search(rf"{ip}\s+([a-f0-9\-:]+)", output, re.IGNORECASE)
            else:
                output = subprocess.check_output(f"arp {ip}", shell=True, encoding='utf-8')
                match = re.search(rf"{ip}.*?(([a-f0-9]{2}[:-]){5}[a-f0-9]{2})", output, re.IGNORECASE)

            if match:
                return match.group(1)
            else:
                return "MAC not found"
        except Exception as e:
            return f"Error: {e}"

    def scan_single_ip(ip, local_ip):
        if ping(ip):
            hostnameDevice = get_hostname(ip)
            mac = get_mac_address(str(ip))
            if str(ip).strip() == str(local_ip).strip():
                print(f"[+] Active: {ip} (Your device) \n----- Device : {hostnameDevice} \n----- MAC: {mac} ")
            else:
                print(f"[+] Active: {ip} \n----- Device : {hostnameDevice} \n----- MAC: {mac}")
            return str(ip)
        return None

    def network_scan(network_range, max_threads=100):
        print(f"Network range: {network_range} \nScanning started...")
        active_hosts = []
        local_hostname = socket.gethostname()
        local_ip = socket.gethostbyname(local_hostname)

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for ip in ipaddress.IPv4Network(network_range, strict=False):
                futures.append(executor.submit(scan_single_ip, ip, local_ip))

            for future in as_completed(futures):
                result = future.result()
                if result:
                    active_hosts.append(result)

        print(f"\nTotal {len(active_hosts)} active device found.")
        save_choice = input("\nDo you want to save the results? (y/n): ").strip().lower()

        if save_choice == 'y':
            # Masaüstü yolu al
            desktop_path = Path.home() / "Desktop"
            desktop_path.mkdir(parents=True, exist_ok=True)

            file_path = desktop_path / "network_scan_result.txt"

            with open(file_path, "w", encoding="utf-8") as f:
                for ip in active_hosts:
                    hostnameDevice = get_hostname(ip)
                    mac = get_mac_address(str(ip))
                    f.write(f"IP : {ip} \n----- Device : {hostnameDevice} \n----- MAC: {mac} \n\n\n")

            print(f"\n✅ Results saved to: {file_path}")

        else:
            print("")
        print("")
        input("Press Enter to return to the main menu...")
        main()

    while True:
        network = input("Enter the network range (e.g., 192.168.1.0/24) or type 'b' to return: ").strip()

        if network.lower() == "b":
            main()
            return

        try:
            # Bu satır geçerli mi diye kontrol eder
            ipaddress.IPv4Network(network, strict=False)
            break  # geçerliyse döngüden çık
        except ValueError:
            print("❌ Invalid network format. Please try again.\n")

    network_scan(network)


def port_scanner():
    print_lock = threading.Lock()
    open_ports = []
    def scan_port(ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                with print_lock:

                    print(f"[+] Port {port} is open - {service}")
                    open_ports.append((port, service))

            sock.close()
        except:
            pass

    def threader(ip, queue):
        while True:
            worker = queue.get()
            scan_port(ip, worker)
            queue.task_done()

    while True:
        target = input("Enter the target IP address (e.g., 192.168.1.1) or type 'b' to return: ").strip()

        if target.lower() == "b":
            main()
            return

        try:
            socket.inet_aton(target)  # IP adresini kontrol eder
            break  # geçerli IP ise döngüden çık
        except socket.error:
            print("❌ Invalid IP address! Please try again.\n")

    while True:
        port_range = input("Enter port range (e.g., 1-1024): ").strip()

        if '-' not in port_range:
            print("❌ Invalid range format. Please try again.\n")
            continue

        try:
            start_port, end_port = map(int, port_range.split('-'))
            if start_port < 0 or end_port > 65535 or start_port > end_port:
                print("❌ Invalid port numbers. Ports must be between 0 and 65535, and start <= end.\n")
                continue
            break  # Geçerli aralıksa döngüden çık
        except ValueError:
            print("❌ Invalid range numbers. Please enter numeric values.\n")

    print(f"\n[*] Starting scan on {target} from port {start_port} to {end_port}...\n")

    queue = Queue()

    for _ in range(100):
        t = threading.Thread(target=threader, args=(target, queue))
        t.daemon = True
        t.start()

    for port in range(start_port, end_port + 1):
        queue.put(port)

    queue.join()

    print("\n✅ Scan completed.")

    save_choice = input("Do you want to save the results to a file? (y/n): ").strip().lower()

    if save_choice == 'y':
        desktop_path = Path.home() / "Desktop"
        if not desktop_path.exists():
            desktop_path = Path.cwd()  # Masaüstü yoksa mevcut klasöre kaydet

        file_path = desktop_path / "port_scan_results.txt"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Port Scan Results for {target}\n\n")
                for port, service in sorted(open_ports):
                    f.write(f"Port {port} is open - {service}\n")
            print(f"\n✅ Results saved to: {file_path}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")
    else:
        print("Results were not saved.")

    input("\nPress Enter to return to the main menu...")
    main()



if __name__ == "__main__":
    main()