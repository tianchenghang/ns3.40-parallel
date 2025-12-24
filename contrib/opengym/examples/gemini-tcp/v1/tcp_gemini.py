import numpy as np
from collections import deque
from tcp_base import TcpEventBased


class TcpGemini(TcpEventBased):
    """
    Implementation of Gemini Fusion Module.
    Ref: Gemini: Divide-and-Conquer for Practical Learning-Based Internet Congestion Control
    """

    def __init__(self):
        super(TcpGemini, self).__init__()

        # --- Control Parameters (Table I & Table III) ---
        # These can be tuned by an external "Booster"
        self.omega = 10  # Initial congestion window
        self.alpha = 1.05  # Multiplicative increase factor (>1)
        self.gamma = 1.0  # Additive increase factor (>=1)
        self.lam = 0.7  # Multiplicative decrease factor (0 < lambda < 1)
        self.delta = 0.1  # RTT inflation threshold
        self.n = 10  # Window size for sampling (in RTTs)

        # --- State Tracking ---
        # Sliding window for Throughput (R) and RTT (T)
        self.history_len = 50  # Buffer size to approximate 'n' RTTs of samples
        self.throughput_window = deque(maxlen=self.history_len)
        self.rtt_window = deque(maxlen=self.history_len)

        # Global min RTT tracking (implied need for RTT inflation baseline)
        self.base_min_rtt = float("inf")

    def update_history(self, rtt_us, segments_acked, segment_size):
        if rtt_us <= 0:
            return

        # Calculate Throughput: Bytes / Seconds
        # rtt_us is in microseconds
        tpt = (segments_acked * segment_size) / (rtt_us / 1e6)

        self.throughput_window.append(tpt)
        self.rtt_window.append(rtt_us)

        if rtt_us < self.base_min_rtt:
            self.base_min_rtt = rtt_us

    def get_stats_window(self):
        """Get Max Throughput and Min/Max RTT over the last n samples."""
        if not self.throughput_window:
            return 0, 0, 0

        # In a real implementation, we would map 'n' RTTs to exact samples.
        # Here we use the last 'n' recorded samples as an approximation.
        lookback = min(len(self.throughput_window), self.n * 2)  # Approximation

        r_slice = list(self.throughput_window)[-lookback:]
        t_slice = list(self.rtt_window)[-lookback:]

        R_max = max(r_slice)
        T_min = min(t_slice)
        T_max = max(t_slice)

        return R_max, T_min, T_max

    def get_action(self, obs, reward, done, info):
        # --- Observation Parsing (Matches TcpEventGymEnv) ---
        # [0]uuid, [1]type, [2]time, [3]nodeId
        ssThresh = obs[4]
        cWnd = obs[5]
        segmentSize = obs[6]
        segmentsAcked = obs[7]
        bytesInFlight = obs[8]
        lastRtt_us = obs[9]
        minRtt_us = obs[10]  # NS-3 internal minRTT
        calledFunc = obs[11]  # 0=Loss (GetSsThresh), 1=Ack (IncreaseWindow)

        new_cWnd = cWnd
        new_ssThresh = ssThresh

        # Update History
        if lastRtt_us > 0:
            self.update_history(lastRtt_us, segmentsAcked, segmentSize)

        # Get stats for Eq (1)-(5)
        R_max, T_min, T_max = self.get_stats_window()

        # Calculate BDP (Bandwidth-Delay Product)
        # T_min is us, R_max is B/s -> BDP in Bytes
        bdp = R_max * (T_min / 1e6)

        # Logic Implementation (Eq 1-4)
        congestion_signal = False

        # --- Logic Implementation ---

        # Event: PACKET LOSS (Eq 3) or explicitly signaled
        if calledFunc == 0:  # Loss Event (GET_SS_THRESH)
            congestion_signal = True
            # Congestion Recovery: Multiplicative Decrease
            # W' = lambda * W
            new_cWnd = int(self.lam * cWnd)
            new_ssThresh = new_cWnd

        # Event: ACK RECEIVED
        elif calledFunc == 1:  # Ack Event (INCREASE_WINDOW)
            # 1. Congestion Signal Detection (Eq 1)
            # Check RTT Inflation: T_min - T_min_global > delta * (T_max - T_min)
            # We use local window T_min vs global base or window variation
            # RTT Inflation Check (Eq 1)
            if T_max > 0 and T_min > 0:
                # Paper Eq (1): T_{t-1,t}^min - T_{t-n,t}^min > delta * (T^max - T^min)
                # Simplified for per-ack check:
                if (lastRtt_us - T_min) > self.delta * (T_max - T_min + 0.1):
                    congestion_signal = True

            if congestion_signal:
                # Multiplicative Decrease (Eq 3)
                new_cWnd = int(self.lam * cWnd)
                new_ssThresh = new_cWnd
            else:
                # 2. Slow Start (Eq 2) or Congestion Avoidance (Eq 4)
                if cWnd < ssThresh:
                    # W' = max(2 * R_max * T_min, W)
                    target_ss = 2 * bdp
                    # Standard SS increase is cwnd + MSS, we check against target
                    next_val = cWnd + segmentsAcked * segmentSize
                    new_cWnd = max(target_ss, next_val)

                # 3. Congestion Avoidance (Eq 4)
                else:
                    # V_t = max(alpha * R_max * T_min, W) + gamma
                    term1 = self.alpha * bdp
                    target_ca = max(term1, cWnd) + (self.gamma * segmentSize)

                    # Apply to current window
                    new_cWnd = target_ca

            new_cWnd = int(new_cWnd)
            new_ssThresh = int(new_ssThresh)

        # Safety Bounds
        new_cWnd = max(2 * segmentSize, new_cWnd)
        new_ssThresh = max(2 * segmentSize, new_ssThresh)

        return [new_ssThresh, new_cWnd]
