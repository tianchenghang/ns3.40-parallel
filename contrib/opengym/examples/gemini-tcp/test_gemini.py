#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from ns3gym import ns3env
from tcp_gemini import TcpGemini

__author__ = "tianchenghang"
__copyright__ = "Copyright (c) 2025, tianchenghang"
__version__ = "0.0.1"
__email__ = "161043261@qq.com"

parser = argparse.ArgumentParser(description="Start Gemini Simulation")
parser.add_argument(
    "--start", type=int, default=1, help="Start ns-3 simulation script 0/1, Default: 1"
)
parser.add_argument(
    "--iterations", type=int, default=1, help="Number of iterations, Default: 1"
)
parser.add_argument(
    "--verbose",
    action="store_true",
    default=False,
    help="Verbose, Default: False",
)

args = parser.parse_args()
startSim = bool(args.start)
iterationNum = int(args.iterations)
verbose = bool(args.verbose)
print(f"startSim: {startSim}, iterationNum: {iterationNum}, verbose: {verbose}")

port = 5555
simTime = 20  # Seconds
stepTime = 0.5
seed = 12
# Important: Ensure sim.cc is compiled and available in path or specified
simArgs = {"--duration": simTime, "--transport_prot": "TcpGemini"}
debug = True

# Create Environment
env = ns3env.Ns3Env(
    port=port,
    stepTime=stepTime,
    startSim=startSim,
    simSeed=seed,
    simArgs=simArgs,
    debug=debug,
)
env.reset()

ob_space = env.observation_space
ac_space = env.action_space

print("Observation space: ", ob_space)
print("Action space: ", ac_space)

# Map to store Gemini agents for multiple flows
gemini_agents = {}


def get_agent(obs):
    socketUuid = obs[0]
    if socketUuid not in gemini_agents:
        print(f"Creating Gemini Fusion Agent for Socket {socketUuid}")
        agent = TcpGemini()
        gemini_agents[socketUuid] = agent
    return gemini_agents[socketUuid]


try:
    currIt = 0
    while currIt < iterationNum:
        print(f"--- Iteration {currIt} Start ---")
        obs = env.reset()
        gemini_agents.clear()

        stepIdx = 0
        reward = 0
        done = False
        info = None

        if verbose:
            print("Start iteration: ", currIt)
            print("Step: ", stepIdx)
            print("---obs: ", obs)

        if obs is None:
            print("Warning: env.reset() returned None, simulation may have ended")
            break

        while True:
            stepIdx += 1
            agent = get_agent(obs)

            # Gemini Fusion: Calculate CWND/SSThresh based on observation (obs)
            action = agent.get_action(obs, reward, done, info)

            # Execute Action in NS-3
            obs, reward, done, info = env.step(action)
            if verbose:
                print("---action: ", action)
                print("Step: ", stepIdx)
                print("---obs, reward, done, info: ", obs, reward, done, info)

            if obs is None:
                print(
                    "Warning: env.step() returned None, simulation ended unexpectedly"
                )
                done = True

            if done:
                break

        currIt += 1

except KeyboardInterrupt:
    print("Ctrl-C -> Exit")
finally:
    env.close()
    print("Done")
