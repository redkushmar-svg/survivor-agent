import os
import sys
import time
import random
import threading
import requests
from flask import Flask, jsonify
from datetime import datetime
from dotenv import load_dotenv

# Solana & Jupiter SDKs for On-Chain Trading
from solders.keypair import Keypair
from jupiter_python_sdk.jupiter import Jupiter

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
        self.private_key = os.getenv("PRIVATE_KEY") # IMPORTANT: Load from env
        if self.private_key:
            self.keypair = Keypair.from_base58_string(self.private_key)
            self.jupiter = Jupiter(
                keypair=self.keypair,
                rpc_url="https://api.mainnet-beta.solana.com" # Using public RPC
            )
        else:
            self.jupiter = None

    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {message}", flush=True)

    def scan_for_arbitrage_opportunity(self) -> float:
        """
        Scans for a simple triangular arbitrage opportunity (SOL -> USDC -> SOL) using Jupiter.
        Returns the profit in USD if an opportunity is found.
        """
        if not self.jupiter:
            self.log("📉 DEX Scanner disabled: Private key not configured.")
            return 0.0

        try:
            self.log("🔍 Scanning DEXs for arbitrage opportunities (SOL -> USDC -> SOL)...")
            # Amount of SOL to trade (in lamports, e.g., 0.01 SOL)
            input_amount_lamports = int(0.01 * 10**9)

            # 1. Get quote for SOL -> USDC
            quote_sol_usdc = self.jupiter.quote(
                input_mint="So11111111111111111111111111111111111111112", # SOL
                output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC
                amount=input_amount_lamports,
                slippage=50 # 0.5%
            )
            usdc_out = quote_sol_usdc['outAmount']

            # 2. Get quote for USDC -> SOL
            quote_usdc_sol = self.jupiter.quote(
                input_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC
                output_mint="So11111111111111111111111111111111111111112", # SOL
                amount=int(usdc_out),
                slippage=50
            )
            sol_out = quote_usdc_sol['outAmount']

            # 3. Check for profit
            profit_lamports = sol_out - input_amount_lamports
            if profit_lamports > 0:
                # Convert profit to USD (assuming 1 SOL = $150)
                profit_usd = (profit_lamports / 10**9) * 150
                self.log(f"💰 Arbitrage opportunity found! Profit: {profit_lamports} Lamports (~${profit_usd:.4f} USD)")
                # In a real scenario, you would execute the trades here
                return round(profit_usd, 4)
            else:
                self.log("📉 No profitable arbitrage path found in this scan.")
                return 0.0

        except Exception as e:
            self.log(f"⚠️ Error during DEX scan: {e}")
            return 0.0

    def apply_burn_rate(self) -> None:
        cycle_cost = round(self.daily_burn / 24, 4) # Hourly burn rate
        self.balance = round(self.balance - cycle_cost, 4)
        self.log(f"🔥 Operating cost deducted: -${cycle_cost:.4f} | Remaining Balance: ${self.balance:.2f}")

    def kill_switch(self):
        self.is_alive = False
        self.log("💀 CRITICAL ALERT: Capital depleted to $0.00.")
        self.log("🛑 Kill-switch triggered. Terminating process...")

    def run_infinite_loop(self):
        self.log(f"🚀 Booting agent with starting balance: ${self.balance:.2f}")
        while self.is_alive:
            self.cycle_count += 1
            print("\n" + "="*50, flush=True)
            self.log(f"--- STARTING CYCLE #{self.cycle_count} ---")

            earned = self.scan_for_arbitrage_opportunity()
            self.balance = round(self.balance + earned, 4)
            self.apply_burn_rate()

            if self.balance <= 0:
                self.kill_switch()
                break
            elif self.balance < 2.0:
                self.log("⚠️ WARNING: Balance critical (<$2.00)! Entering Low-Power Mode.")
            else:
                self.log(f"✅ Healthy status. Runway: approx {round(self.balance / self.daily_burn, 1)} days.")

            time.sleep(3600) # Sleep for 1 hour

def start_agent_thread():
    agent = AutonomousAgent()
    agent.run_infinite_loop()

if __name__ == "__main__":
    threading.Thread(target=start_agent_thread, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
