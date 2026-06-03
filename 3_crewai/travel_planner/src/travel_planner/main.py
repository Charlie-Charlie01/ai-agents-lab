#!/usr/bin/env python
import sys
import warnings
from travel_planner.crew import TravelPlanner

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the travel planner crew.
    """
    inputs = {
        'destination': 'Capetown, South Africa',
        'departure_city': 'Lagos, Nigeria',
        'check_in': '2026-07-01',
        'check_out': '2026-07-07',
        'budget': 'mid-range',
        'travelers': '2 adults',
        'interests': 'art, food, history, local culture',
    }

    result = TravelPlanner().crew().kickoff(inputs=inputs)

    print("\n\n=== TRAVEL PLAN ===\n\n")
    print(result.raw)


if __name__ == "__main__":
    run()