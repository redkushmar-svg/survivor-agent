import os
import sys
import time
import random
import threading
import requests
from flask import Flask, jsonify
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- FLASK WEB SERVER FOR 24/7 KEEP-ALIVE ---
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "agent_name": os.getenv("AGENT_NAME", "SurvivorBot"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# --- AUTONOMOUS AGENT CORE CLASS ---
class AutonomousAgent:
    def __init__(self):
        self.name = os.getenv("AGENT_NAME", "SurvivorBot")
        self.balance = float(os.getenv("INITIAL_CAPITAL_USD", 10.0))
        self.daily_burn = float(os.getenv("DAILY_BURN_RATE_USD", 1.52))
        self.cycle_count = 0
        self.is_alive = True

    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {message}", flush=True)

    def execute_work_task(self) -> float:
        self.log("🔍 Scanning for earning opportunities (Content / Alpha / Micro-SaaS)...")
        time.sleep(1)
        # 60% probability of earning some revenue
        success = random.random() > 0.4
        if success:
            revenue = round(random.uniform(0.5, 3.0), 2)
            self.log(f"💰 Revenue generated: +${revenue:.2f}")
            return revenue
        else:
            self.log("📉 No revenue generated in this cycle.")
            return 0.0

    def apply_burn_rate(self) -> None:
        cycle_cost = round(self.daily_burn / 4, 2)
        self.balance = round(self.balance - cycle_cost, 2)
        self.log(f"🔥 Operating cost deducted: -${cycle_cost:.2f} | Remaining Balance: ${self.balance:.2f}")

    def kill_switch(self):
        self.is_alive = False
        self.log("💀 CRITICAL ALERT: Capital depleted to $0.00.")
        self.log("🛑 Kill-switch triggered. Terminating process...")

# --- PRODUCTION LAYER (REAL SYNC) ---
class ProductionAutonomousAgent(AutonomousAgent):
    def __init__(self):
        super().__init__()
        self.wallet_address = os.getenv("WALLET_ADDRESS", "simulated_or_solana_pubkey")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

    def fetch_real_balance(self) -> float:
        if self.wallet_address and self.wallet_address != "simulated_or_solana_pubkey":
            try:
                # Direct Solana RPC Sync
                url = "https://api.mainnet-beta.solana.com"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address]
                }
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    lamports = response.json().get("result", {}).get("value", 0)
                    sol_balance = lamports / 10**9
                    # Simulating USD equivalent (Assuming 1 SOL = $150 USD)
                    self.balance = round(sol_balance * 150.0, 2)
                    self.log(f"🔄 Synced Real Solana Balance: {sol_balance:.4f} SOL (~${self.balance:.2f} USD)")
            except Exception as e:
                self.log(f"⚠️ Error syncing on-chain balance: {e}. Falling back to simulation.")
        else:
            self.log(f"🔄 Running with Simulated Balance: ${self.balance:.2f} USD")
        return self.balance

    def run_infinite_loop(self):
        self.log(f"🚀 Booting agent with starting balance: ${self.balance:.2f}")
        while self.is_alive:
            self.cycle_count += 1
            print("\n" + "="*50, flush=True)
            self.log(f"--- STARTING CYCLE #{self.cycle_count} ---")
            
            # 1. Sync live balance from Solana Network
            self.fetch_real_balance()
            
            # 2. Run monetization logic
            earned = self.execute_work_task()
            
            # 3. Add earning and deduct operating cost
            self.balance = round(self.balance + earned, 2)
            self.apply_burn_rate()
            
            # 4. Critical Health checks
            if self.balance <= 0:
                self.kill_switch()
                break
            elif self.balance < 2.0:
                self.log("⚠️ WARNING: Balance critical (<$2.00)! Entering Low-Power Mode.")
            else:
                self.log(f"✅ Healthy status. Runway: approx {round(self.balance / self.daily_burn, 1)} days.")
            
            # 1 Hour sleep before next loop execution (To avoid API Rate limits)
            time.sleep(3600) 

def start_agent_thread():
    agent = ProductionAutonomousAgent()
    agent.fetch_real_balance()
    agent.run_infinite_loop()

if __name__ == "__main__":
    # Start Agent in a separate thread so Flask can keep answering pings
    threading.Thread(target=start_agent_thread, daemon=True).start()
    
    # Run Web Server
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
