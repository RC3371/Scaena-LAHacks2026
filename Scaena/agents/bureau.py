import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import logging
from config_health import print_config_health
from agents.agent_runtime import Bureau
from agents.agent1_market_research import agent as agent1
from agents.agent2_pitching import agent as agent2
from agents.agent3_tracking import agent as agent3
from agents.agent4_followup import agent as agent4

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    bureau = Bureau()
    bureau.add(agent1)
    bureau.add(agent2)
    bureau.add(agent3)
    bureau.add(agent4)

    print(f"\nScaena Agent Bureau starting...")
    print(f"  Agent 1 (Market Research): {agent1.address}")
    print(f"  Agent 2 (Pitching):        {agent2.address}")
    print(f"  Agent 3 (Tracking):        {agent3.address}")
    print(f"  Agent 4 (Follow-Up):       {agent4.address}")
    simulation = not os.getenv("ASI1_API_KEY", "").strip()
    print(f"  Mode: {'SIMULATION (no ASI1_API_KEY)' if simulation else 'LIVE (ASI-1 Mini)'}\n")
    print_config_health("agents")

    bureau.run()
