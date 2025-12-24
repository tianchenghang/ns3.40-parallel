import numpy as np
from collections import deque
from tcp_base import TcpEventBased


class TcpGemini(TcpEventBased):
    """
    Optimized Implementation of Gemini Fusion Module with Booster Logic.
    Includes ECN support and dynamic parameter tuning.
    """

    def __init__(self):
        super(TcpGemini, self).__init__()

        # --- Base Control Parameters ---
        # "Booster" will tune these dynamically based on obs
        self.base_alpha = 1.05  # Multiplicative increase factor
        self.base_gamma = 1.0  # Additive increase factor
        self.base_lam = 0.7  # Multiplicative decrease factor
        self.delta = 0.1  # RTT inflation threshold
        self.n = 10  # Window size for sampling

        # --- State Tracking ---
        self.history_len = 50
        self.throughput_window = deque(maxlen=self.history_len)
        self.rtt_window = deque(maxlen=self.history_len)

        # Tracking for Reward Calculation
        self.prev_bytes_acked = 0
        self.prev_time = 0

    def update_history(self, rtt_us, segments_acked, segment_size):
        if rtt_us <= 0:
            return
        # Calculate Throughput: Bytes / Seconds
        tpt = (segments_acked * segment_size) / (rtt_us / 1e6)
        self.throughput_window.append(tpt)
        self.rtt_window.append(rtt_us)

    def get_stats_window(self):
        """Get Max Throughput and Min/Max RTT over the last n samples."""
        if not self.throughput_window:
            return 0, 0, 0

        # Approximate 'n' RTTs by looking at last n*2 samples
        lookback = min(len(self.throughput_window), self.n * 2)
        r_slice = list(self.throughput_window)[-lookback:]
        t_slice = list(self.rtt_window)[-lookback:]

        return max(r_slice), min(t_slice), max(t_slice)

    def calculate_reward(self, throughput, rtt, min_rtt, segment_size, lost_detected):
        """
        Gemini Paper Eq (9): Reward = Throughput - sigma * Delay
        Here prefer Throughput (small sigma) as requested.
        """
        # sigma = 2.0  # Tunable parameter: preference for delay vs throughput
        sigma = 0.5  # Lower sigma favors throughput

        # Delay in ms
        delay_ms = (rtt - min_rtt) / 1000.0
        # Throughput in Mbps
        tpt_mbps = throughput / 1e6 * 8

        reward = tpt_mbps - (sigma * delay_ms)
        if lost_detected:
            reward -= 5.0  # Penalty for loss

        return reward

    def get_action(self, obs, reward, done, info):
        # --- 1. Parse observation: All 15 Parameters ---
        socketUuid = obs[0]
        envType = obs[1]
        simTime_us = obs[2]
        nodeId = obs[3]
        ssThresh = obs[4]
        cWnd = obs[5]
        segmentSize = obs[6]
        segmentsAcked = obs[7]
        bytesInFlight = obs[8]
        lastRtt_us = obs[9]
        minRtt_us = obs[10]
        calledFunc = obs[11]  # 0=Loss, 1=Ack
        caState = obs[12]
        caEvent = obs[13]
        ecnState = obs[14]  # 2 = ECN_CE_RCVD (Congestion Experienced)

        new_cWnd = cWnd
        new_ssThresh = ssThresh

        # Update History
        if lastRtt_us > 0:
            self.update_history(lastRtt_us, segmentsAcked, segmentSize)

        R_max, T_min, T_max = self.get_stats_window()

        # Calculate BDP (Bytes)
        # Use T_min from obs if available (global min), else local window min
        bdp = R_max * (minRtt_us / 1e6) if minRtt_us > 0 else cWnd

        # --- 2. Booster Logic: Dynamic Parameter Tuning ---
        # Instead of fixed alpha/lambda, adjust them based on rich state (ECN, RTT gradients)
        current_alpha = self.base_alpha
        current_lam = self.base_lam

        # Optimization: Aggressive if RTT is low (Network is empty)
        # Using 15 params: if lastRtt is close to minRtt, boost alpha
        if lastRtt_us > 0 and minRtt_us > 0:
            if lastRtt_us < minRtt_us * 1.1:
                current_alpha = 1.10  # More aggressive increase
            elif lastRtt_us > minRtt_us * 1.8:
                current_alpha = 1.01  # Conservative increase

        # Optimization: ECN Handling
        # If ECN CE received (ecnState == 2), should cut window but less than a full loss
        ecn_congestion = False
        if ecnState == 2:  # ECN_CE_RCVD
            ecn_congestion = True

        # --- 3. Gemini Fusion Logic ---

        congestion_signal = False

        # Condition 1: Packet Loss (Explicit)
        if calledFunc == 0:
            congestion_signal = True
            current_lam = 0.5  # Hard decrease for loss

        # Condition 2: ECN Trigger
        elif ecn_congestion:
            congestion_signal = True
            current_lam = 0.8  # Mild decrease for ECN

        # Condition 3: RTT Inflation (Gemini Eq 1)
        # T_{curr} - T_{min} > delta * (T_{max} - T_{min})
        elif T_max > T_min:
            if (lastRtt_us - T_min) > self.delta * (T_max - T_min):
                congestion_signal = True
                current_lam = 0.7  # Standard decrease

        # Execution
        if congestion_signal:
            # Congestion Recovery (Eq 3)
            # Use the dynamically tuned lambda
            new_cWnd = int(current_lam * cWnd)
            new_ssThresh = new_cWnd

        else:
            # Congestion Avoidance / Slow Start
            if cWnd < ssThresh:
                # Slow Start (Eq 2)
                target_ss = 2 * bdp
                # Ensure don't jump too wildly in NS3 simulation steps
                increase = segmentsAcked * segmentSize
                new_cWnd = min(cWnd + increase, target_ss)
            else:
                # Congestion Avoidance (Eq 4)
                # V_t = max(alpha * BDP, W) + gamma
                # Use dynamically tuned alpha
                term1 = current_alpha * bdp
                target_ca = max(term1, cWnd) + (self.base_gamma * segmentSize)
                new_cWnd = target_ca

        # Safety Bounds
        new_cWnd = max(2 * segmentSize, int(new_cWnd))
        new_ssThresh = max(2 * segmentSize, int(new_ssThresh))

        # --- 5. Calculate Reward for RL Feedback ---
        # Although not used by standard NS-3 flow, this return value
        # is what you would log or use if training a PPO agent.
        step_reward = self.calculate_reward(
            throughput=R_max,
            rtt=lastRtt_us,
            min_rtt=minRtt_us,
            segment_size=segmentSize,
            lost_detected=congestion_signal,
        )

        # Update internal state if needed for next step calculation
        self.prev_time = simTime_us

        return [new_ssThresh, new_cWnd]
