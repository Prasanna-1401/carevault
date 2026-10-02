import sys
import time
from pathlib import Path
from pycloudflared import try_cloudflare

DEPLOY_FILE = Path(__file__).resolve().parent / "deployment_url.txt"

def deploy():
    print("==================================================")
    print("DEPLOYING CAREVAULT AI TO PUBLIC CLOUDFLARE TUNNEL")
    print("==================================================")
    print("Connecting local server (port 8000) to Cloudflare Global Edge...")

    try:
        tunnel = try_cloudflare(port=8000)
        public_url = str(tunnel.tunnel)
        print("\n[SUCCESS] CareVault AI is DEPLOYED and LIVE at:")
        print("URL: " + public_url)
        print("==================================================")

        with open(DEPLOY_FILE, "w", encoding="utf-8") as f:
            f.write(public_url.strip())

        # Keep tunnel active
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nDeployment stopped.")
    except Exception as e:
        print(f"\n[ERROR] Cloudflare tunnel error: {e}")

if __name__ == "__main__":
    deploy()
