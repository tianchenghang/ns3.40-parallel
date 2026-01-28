"""
Gemini TCP Congestion Control Algorithm - Throughput Optimized Implementation

A fusion-based congestion control approach combining:
1. Rate-based control (BBR-like) using Bandwidth-Delay Product (BDP) estimation
2. Loss-based control (CUBIC-like) for robustness under packet loss
3. ECN-aware congestion detection for proactive response
4. Adaptive parameter tuning for dynamic network conditions

Key Design Principles:
- Throughput-first: Aggressive window growth, conservative reduction
- Multi-signal fusion: Combine RTT, loss, and ECN signals for decisions
- Per-flow state: Independent tracking for multi-flow fairness

All 15 observation parameters from ns-3 TcpSocketState are utilized.
"""

import logging
import numpy as np
from collections import deque
from tcp_base import TcpEventBased

# Configure logging for debugging and analysis
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TcpGemini")
logger.setLevel(logging.INFO)  # Set to DEBUG for verbose output


class TcpGemini(TcpEventBased):
    """
    Gemini Fusion Congestion Control Module.

    Implements a hybrid rate-based and loss-based congestion control algorithm
    optimized for high throughput in datacenter and WAN environments.

    Algorithm Overview:
    - Slow Start: Exponential growth targeting 3x BDP
    - Congestion Avoidance: V_t = max(alpha * BDP, W) + gamma
    - Congestion Response: Multiplicative decrease with lambda factors

    Attributes:
        alpha_base (float): Base multiplicative increase factor
        gamma_base (float): Base additive increase (in segments per RTT)
        lambda_loss (float): Window retention ratio on packet loss
        lambda_ecn (float): Window retention ratio on ECN signal
        delta (float): RTT inflation threshold for congestion detection
    """

    # ==========================================================================
    # ECN State Constants (from ns-3 TcpSocketState::EcnState)
    # ==========================================================================
    ECN_DISABLED = 0  # ECN functionality disabled
    ECN_IDLE = 1  # ECN enabled, no congestion signals
    ECN_CE_RCVD = 2  # Congestion Experienced (CE) codepoint received
    ECN_SENDING_ECE = 3  # Sending ECN-Echo to notify sender
    ECN_ECE_RCVD = 4  # ECN-Echo received from receiver
    ECN_CWR_SENT = 5  # Congestion Window Reduced (CWR) flag sent

    # ==========================================================================
    # Congestion Algorithm State Constants (from ns-3 TcpSocketState::TcpCaState)
    # ==========================================================================
    CA_OPEN = 0  # Normal operation, no congestion
    CA_DISORDER = 1  # Duplicate ACKs received, potential reordering
    CA_CWR = 2  # Congestion Window Reduced state (ECN response)
    CA_RECOVERY = 3  # Fast Recovery after triple duplicate ACK
    CA_LOSS = 4  # Timeout-based loss recovery

    # ==========================================================================
    # Congestion Algorithm Event Constants (from ns-3 TcpSocketState::TcpCaEvent)
    # ==========================================================================
    CA_EVENT_TX_START = 0  # First transmission
    CA_EVENT_CWND_RESTART = 1  # Congestion window restart after idle
    CA_EVENT_COMPLETE_CWR = 2  # CWR phase completed
    CA_EVENT_LOSS = 3  # Packet loss detected
    CA_EVENT_ECN_NO_CE = 4  # ECN-capable packet without CE
    CA_EVENT_ECN_IS_CE = 5  # ECN-capable packet with CE marking
    CA_EVENT_DELAYED_ACK = 6  # Delayed ACK received
    CA_EVENT_NON_DELAYED_ACK = 7  # Non-delayed ACK received

    # ==========================================================================
    # Called Function Constants (identifies the callback context)
    # ==========================================================================
    FUNC_GET_SS_THRESH = 0  # GetSsThresh() called - indicates loss event
    FUNC_INCREASE_WINDOW = 1  # IncreaseWindow() called - normal ACK processing

    def __init__(self):
        """
        Initialize Gemini TCP with throughput-optimized parameters.

        Parameter tuning rationale:
        - Higher alpha values enable faster bandwidth probing
        - Higher lambda values preserve more window on congestion
        - Higher delta threshold reduces false-positive congestion detection
        """
        super(TcpGemini, self).__init__()

        logger.info("Initializing TcpGemini congestion control algorithm")

        # ======================================================================
        # Core Algorithm Parameters (Throughput Optimized)
        # ======================================================================

        # Alpha: Multiplicative increase factor for congestion avoidance
        # Controls how aggressively cwnd grows relative to BDP
        # Higher values = faster bandwidth utilization, risk of more loss
        self.alpha_base = 1.25  # Default alpha (25% above BDP target)
        self.alpha_min = 1.10  # Minimum alpha (10% above BDP)
        self.alpha_max = 1.50  # Maximum alpha (50% above BDP)

        # Gamma: Additive increase factor (segments per RTT)
        # Provides linear growth component in congestion avoidance
        # Higher values = faster steady-state growth
        self.gamma_base = 4.0  # Add 4 segments per RTT

        # Lambda: Multiplicative decrease factors (window retention ratios)
        # Control how much window is preserved on congestion events
        # Higher values = less aggressive backoff, faster recovery
        self.lambda_loss = 0.70  # Retain 70% on packet loss
        self.lambda_ecn = 0.92  # Retain 92% on ECN signal (proactive)
        self.lambda_rtt = 0.85  # Retain 85% on RTT inflation

        # Delta: RTT inflation threshold for congestion detection
        # Normalized RTT increase that triggers congestion response
        # Higher values = more tolerant of queuing delay
        self.delta = 0.50  # 50% normalized RTT inflation threshold

        # N: Sampling window size for statistics (in RTT counts)
        self.n_samples = 20

        # ======================================================================
        # State Management
        # ======================================================================

        # History buffer length for per-flow metrics
        self.history_len = 100

        # Per-flow state dictionary (keyed by socket UUID)
        # Enables independent congestion control for concurrent flows
        self.flow_states = {}

        # ======================================================================
        # Adaptive Learning Parameters
        # ======================================================================

        # Learning rate for online parameter adaptation
        self.learning_rate = 0.02

        # Exploration factor for throughput optimization
        self.exploration_factor = 0.08

        logger.info(
            f"Parameters initialized: alpha=[{self.alpha_min}, {self.alpha_base}, {self.alpha_max}], "
            f"gamma={self.gamma_base}, lambda_loss={self.lambda_loss}, "
            f"lambda_ecn={self.lambda_ecn}, delta={self.delta}"
        )

    def _get_flow_state(self, socket_uuid):
        """
        Retrieve or initialize per-flow state.

        Each flow maintains independent state for:
        - Historical metrics (throughput, RTT, cwnd, BDP)
        - ECN event tracking and rate estimation
        - Adaptive parameters (alpha, gamma)
        - Congestion event counters

        Args:
            socket_uuid: Unique identifier for the TCP socket

        Returns:
            dict: Flow state dictionary with all tracking variables
        """
        if socket_uuid not in self.flow_states:
            logger.debug(f"Creating new flow state for socket {socket_uuid}")

            self.flow_states[socket_uuid] = {
                # Historical metric buffers (circular queues)
                "throughput_history": deque(maxlen=self.history_len),
                "rtt_history": deque(maxlen=self.history_len),
                "cwnd_history": deque(maxlen=self.history_len),
                "bdp_history": deque(maxlen=self.history_len),
                # ECN event tracking
                "ecn_events": deque(maxlen=50),  # Recent ECN timestamps
                "last_ecn_time": 0,  # Last ECN event time (us)
                "ecn_rate": 0.0,  # ECN events per second
                # Performance metrics
                "max_throughput": 0,  # Peak observed throughput (B/s)
                "avg_throughput": 0,  # Exponential moving average
                "min_rtt_observed": float("inf"),  # Minimum RTT (us)
                "max_rtt_observed": 0,  # Maximum RTT (us)
                # Adaptive parameters (per-flow tuning)
                "alpha": self.alpha_base,  # Current alpha value
                "gamma": self.gamma_base,  # Current gamma value
                # State tracking
                "prev_cwnd": 0,  # Previous cwnd value
                "prev_time": 0,  # Previous observation time
                "prev_bytes_acked": 0,  # Previous bytes acked
                "consecutive_increases": 0,  # Successive increase count
                "consecutive_decreases": 0,  # Successive decrease count
                # Congestion event counters
                "loss_count": 0,  # Total packet loss events
                "ecn_count": 0,  # Total ECN events
                "last_loss_time": 0,  # Last loss event time (us)
            }

        return self.flow_states[socket_uuid]

    def _update_metrics(self, state, obs):
        """
        Update flow metrics from observation vector.

        Processes all 15 observation parameters to maintain:
        - RTT tracking (min, max, history)
        - Throughput estimation (instantaneous and EMA)
        - BDP calculation for rate-based control
        - ECN event rate for congestion detection

        Args:
            state: Per-flow state dictionary
            obs: Observation vector [15 parameters from ns-3]
        """
        # Extract relevant observation parameters
        simTime_us = obs[2]  # Current simulation time (microseconds)
        cWnd = obs[5]  # Current congestion window (bytes)
        segmentSize = obs[6]  # TCP segment size / MSS (bytes)
        segmentsAcked = obs[7]  # Number of segments acknowledged
        bytesInFlight = obs[8]  # Bytes currently in flight
        lastRtt_us = obs[9]  # Last measured RTT (microseconds)
        minRtt_us = obs[10]  # Minimum observed RTT (microseconds)
        ecnState = obs[14]  # Current ECN state

        # Update RTT statistics
        if lastRtt_us > 0:
            state["rtt_history"].append(lastRtt_us)
            state["min_rtt_observed"] = min(state["min_rtt_observed"], lastRtt_us)
            state["max_rtt_observed"] = max(state["max_rtt_observed"], lastRtt_us)

        # Calculate instantaneous throughput (bytes per second)
        # Throughput = (bytes_acked) / (RTT in seconds)
        if lastRtt_us > 0 and segmentsAcked > 0:
            throughput = (segmentsAcked * segmentSize) / (lastRtt_us / 1e6)
            state["throughput_history"].append(throughput)
            state["max_throughput"] = max(state["max_throughput"], throughput)

            # Update exponential moving average (EMA) throughput
            # EMA provides smooth estimate resistant to transient variations
            if state["avg_throughput"] == 0:
                state["avg_throughput"] = throughput
            else:
                # EMA formula: new_avg = 0.9 * old_avg + 0.1 * new_sample
                state["avg_throughput"] = (
                    0.9 * state["avg_throughput"] + 0.1 * throughput
                )

        # Track congestion window evolution
        state["cwnd_history"].append(cWnd)

        # Calculate and track Bandwidth-Delay Product (BDP)
        # BDP = max_throughput * min_RTT (optimal pipe size)
        if minRtt_us > 0 and state["max_throughput"] > 0:
            bdp = state["max_throughput"] * (minRtt_us / 1e6)
            state["bdp_history"].append(bdp)

        # ECN event tracking for congestion rate estimation
        if ecnState in [self.ECN_CE_RCVD, self.ECN_ECE_RCVD]:
            state["ecn_events"].append(simTime_us)
            state["last_ecn_time"] = simTime_us
            state["ecn_count"] += 1

            logger.debug(
                f"ECN event detected: state={ecnState}, "
                f"total_ecn_count={state['ecn_count']}"
            )

        # Calculate ECN rate (events per second in observation window)
        if len(state["ecn_events"]) >= 2:
            time_window = (state["ecn_events"][-1] - state["ecn_events"][0]) / 1e6
            if time_window > 0:
                state["ecn_rate"] = len(state["ecn_events"]) / time_window

        # Update state tracking variables
        state["prev_time"] = simTime_us
        state["prev_cwnd"] = cWnd

    def _get_window_stats(self, state):
        """
        Compute statistics over the recent sampling window.

        Calculates aggregated metrics for decision making:
        - Throughput: max and average over window
        - RTT: min, max, and average over window
        - BDP: average over window for target estimation

        Args:
            state: Per-flow state dictionary

        Returns:
            dict: Statistical summary with keys:
                - max_throughput, avg_throughput
                - min_rtt, max_rtt, avg_rtt
                - avg_bdp
        """
        # Use 2x n_samples for broader historical context
        n = self.n_samples * 2

        # Throughput statistics
        if len(state["throughput_history"]) > 0:
            tpt_slice = list(state["throughput_history"])[-n:]
            max_throughput = max(tpt_slice)
            avg_throughput = sum(tpt_slice) / len(tpt_slice)
        else:
            max_throughput = 0
            avg_throughput = 0

        # RTT statistics
        if len(state["rtt_history"]) > 0:
            rtt_slice = list(state["rtt_history"])[-n:]
            min_rtt = min(rtt_slice)
            max_rtt = max(rtt_slice)
            avg_rtt = sum(rtt_slice) / len(rtt_slice)
        else:
            min_rtt = 0
            max_rtt = 0
            avg_rtt = 0

        # BDP statistics
        if len(state["bdp_history"]) > 0:
            bdp_slice = list(state["bdp_history"])[-n:]
            avg_bdp = sum(bdp_slice) / len(bdp_slice)
        else:
            avg_bdp = 0

        return {
            "max_throughput": max_throughput,
            "avg_throughput": avg_throughput,
            "min_rtt": min_rtt,
            "max_rtt": max_rtt,
            "avg_rtt": avg_rtt,
            "avg_bdp": avg_bdp,
        }

    def _adapt_alpha(self, state, stats, obs):
        """
        Dynamically adapt the multiplicative increase factor (alpha).

        Alpha controls aggressiveness of bandwidth probing:
        - Increased when network shows capacity (low RTT inflation)
        - Decreased on congestion signals (ECN, loss, high RTT)

        Adaptation Strategy (Throughput Optimized):
        - Tolerant RTT thresholds to avoid premature backoff
        - Reward consecutive successful increases
        - Mild response to transient congestion signals

        Args:
            state: Per-flow state dictionary
            stats: Window statistics from _get_window_stats()
            obs: Current observation vector

        Returns:
            float: Adapted alpha value for current decision
        """
        lastRtt_us = obs[9]  # Current RTT measurement
        minRtt_us = obs[10]  # Baseline minimum RTT
        caState = obs[12]  # Congestion algorithm state
        ecnState = obs[14]  # ECN state

        alpha = state["alpha"]
        original_alpha = alpha

        # ======================================================================
        # Factor 1: RTT Inflation Ratio
        # Measures queuing delay relative to propagation delay
        # ======================================================================
        if minRtt_us > 0 and lastRtt_us > 0:
            rtt_ratio = lastRtt_us / minRtt_us

            if rtt_ratio < 1.5:
                # Low inflation: Network has available capacity
                # Increase alpha aggressively to probe for more bandwidth
                alpha = min(alpha + 0.05, self.alpha_max)
                state["consecutive_increases"] += 1

            elif rtt_ratio < 2.0:
                # Moderate inflation: Some queuing, but still growing
                # Continue increasing but more conservatively
                alpha = min(alpha + 0.02, self.alpha_max)

            elif rtt_ratio > 3.0:
                # High inflation: Significant queuing delay
                # Reduce alpha to slow bandwidth probing
                alpha = max(alpha - 0.01, self.alpha_min)
                state["consecutive_increases"] = 0

            # Note: RTT ratio 1.5-3.0 maintains current alpha (neutral zone)

        # ======================================================================
        # Factor 2: ECN Feedback Response
        # ECN provides early congestion notification before loss
        # ======================================================================
        if ecnState in [self.ECN_CE_RCVD, self.ECN_ECE_RCVD]:
            # Mild reduction - ECN is early warning, not severe congestion
            alpha = max(alpha - 0.01, self.alpha_min)
            # Don't reset consecutive_increases - allow continued growth

        # ======================================================================
        # Factor 3: Congestion Algorithm State
        # Only respond to severe congestion states
        # ======================================================================
        if caState == self.CA_LOSS:
            # Timeout-based loss indicates severe congestion
            alpha = max(alpha - 0.01, self.alpha_min)
            state["consecutive_increases"] = 0

        # Note: CA_CWR and CA_RECOVERY are not penalized to maintain throughput

        # ======================================================================
        # Factor 4: Throughput Trend Reward
        # Reward stable growth with increased aggressiveness
        # ======================================================================
        if state["consecutive_increases"] > 3:
            # Stable growth pattern - boost alpha for faster convergence
            alpha = min(alpha + 0.03, self.alpha_max)

        # ======================================================================
        # Factor 5: ECN Rate Limiting
        # High ECN rate indicates persistent congestion
        # ======================================================================
        if state["ecn_rate"] > 50:
            # More than 50 ECN events/second indicates serious congestion
            alpha = max(alpha - 0.01, self.alpha_min)

        state["alpha"] = alpha

        # Log significant alpha changes
        if abs(alpha - original_alpha) > 0.02:
            logger.debug(
                f"Alpha adapted: {original_alpha:.3f} -> {alpha:.3f}, "
                f"consecutive_increases={state['consecutive_increases']}"
            )

        return alpha

    def _detect_congestion(self, obs, state, stats):
        """
        Multi-signal congestion detection optimized for throughput.

        Detection Philosophy:
        - Only respond to definitive congestion signals
        - Ignore transient or ambiguous indicators
        - Prefer false negatives (miss congestion) over false positives

        Signal Priority (highest to lowest):
        1. Explicit packet loss (calledFunc == GetSsThresh)
        2. High-frequency ECN events
        3. CA_LOSS state (timeout-based recovery)

        Removed signals (too sensitive for high-throughput):
        - Single ECN events, ECN_ECE_RCVD
        - CA_CWR, CA_RECOVERY states
        - RTT inflation detection

        Args:
            obs: Current observation vector
            state: Per-flow state dictionary
            stats: Window statistics

        Returns:
            tuple: (is_congested: bool, congestion_type: str, severity: float)
        """
        calledFunc = obs[11]  # Callback context identifier
        caState = obs[12]  # Congestion algorithm state
        caEvent = obs[13]  # Congestion algorithm event
        ecnState = obs[14]  # ECN state

        # ======================================================================
        # Signal 1: Explicit Packet Loss (Highest Priority)
        # GetSsThresh callback indicates loss-based cwnd reduction needed
        # ======================================================================
        if calledFunc == self.FUNC_GET_SS_THRESH:
            state["loss_count"] += 1
            state["last_loss_time"] = obs[2]

            logger.info(
                f"Packet loss detected: total_losses={state['loss_count']}, "
                f"cwnd={obs[5]}, bytesInFlight={obs[8]}"
            )

            return True, "loss", 0.7  # Moderate severity to preserve window

        # ======================================================================
        # Signal 2: ECN Congestion Experienced
        # Only respond to high-frequency ECN (sustained congestion)
        # ======================================================================
        if ecnState == self.ECN_CE_RCVD or caEvent == self.CA_EVENT_ECN_IS_CE:
            if state["ecn_rate"] > 30:
                # High ECN rate indicates persistent queue buildup
                logger.info(
                    f"High ECN rate detected: rate={state['ecn_rate']:.1f}/s, "
                    f"triggering congestion response"
                )
                return True, "ecn", 0.3  # Low severity - proactive response

            # Low-frequency ECN: log but don't trigger response
            logger.debug(
                f"ECN event ignored (low rate): rate={state['ecn_rate']:.1f}/s"
            )
            return False, None, 0.0

        # ======================================================================
        # Signal 3: CA_LOSS State
        # Timeout-based recovery indicates severe path degradation
        # ======================================================================
        if caState == self.CA_LOSS:
            logger.info(f"CA_LOSS state detected: entering timeout recovery")
            return True, "ca_loss", 0.6

        # ======================================================================
        # No Congestion Detected
        # Removed responses to preserve throughput:
        # - ECN_ECE_RCVD: Too sensitive
        # - CA_CWR: Normal ECN response, not additional signal
        # - CA_RECOVERY: Fast recovery handles this
        # - RTT inflation: Major throughput killer
        # ======================================================================

        return False, None, 0.0

    def _calculate_target_cwnd(
        self, obs, state, stats, is_congested, cong_type, severity
    ):
        """
        Calculate target congestion window using Gemini fusion logic.

        Algorithm:
        - Congestion Response: new_cwnd = lambda * cwnd
        - Slow Start: Exponential growth toward 3 * BDP
        - Congestion Avoidance: V_t = max(alpha * BDP, cwnd) + gamma

        Throughput Optimization:
        - Aggressive slow start (2-3x standard increase)
        - Large additive increase in congestion avoidance
        - High window caps (8 * BDP)
        - Utilization-aware boost when under-subscribed

        Args:
            obs: Current observation vector
            state: Per-flow state dictionary
            stats: Window statistics
            is_congested: Congestion detection result
            cong_type: Type of congestion signal
            severity: Congestion severity (0.0 - 1.0)

        Returns:
            tuple: (new_ssThresh: int, new_cwnd: int)
        """
        ssThresh = obs[4]  # Current slow start threshold
        cWnd = obs[5]  # Current congestion window
        segmentSize = obs[6]  # TCP segment size (MSS)
        segmentsAcked = obs[7]  # Segments acknowledged this ACK
        bytesInFlight = obs[8]  # Bytes currently unacknowledged
        minRtt_us = obs[10]  # Minimum RTT for BDP calculation

        # ======================================================================
        # Calculate Bandwidth-Delay Product (BDP)
        # BDP represents the optimal amount of data in flight
        # ======================================================================
        if stats["max_throughput"] > 0 and minRtt_us > 0:
            # BDP = bandwidth * delay
            bdp = stats["max_throughput"] * (minRtt_us / 1e6)
        else:
            # Fallback: aggressive default when BDP unknown
            bdp = cWnd * 2

        # Get adaptive alpha for this decision
        alpha = self._adapt_alpha(state, stats, obs)

        if is_congested:
            # ==================================================================
            # CONGESTION RESPONSE: Multiplicative Decrease
            # Goal: Reduce window while preserving as much throughput as possible
            # ==================================================================

            if cong_type == "loss":
                # Packet loss: Standard multiplicative decrease
                lam = self.lambda_loss  # 0.70 - retain 70%
                state["consecutive_decreases"] += 1

            elif cong_type == "ecn":
                # ECN: Mild decrease - early warning, not severe
                lam = self.lambda_ecn  # 0.92 - retain 92%

            elif cong_type == "ca_loss":
                # Timeout recovery: Moderate decrease
                lam = 0.75  # Retain 75%

            else:
                # Unknown congestion type: Conservative decrease
                lam = 0.90  # Retain 90%

            new_cwnd = int(lam * cWnd)

            # Set ssThresh higher to allow faster recovery
            # Standard would be new_cwnd, we use max(new_cwnd, 0.75*cWnd)
            new_ssThresh = max(new_cwnd, int(0.75 * cWnd))

            state["consecutive_increases"] = 0

            logger.info(
                f"Congestion response [{cong_type}]: "
                f"cwnd {cWnd} -> {new_cwnd} (lambda={lam:.2f}), "
                f"ssThresh -> {new_ssThresh}"
            )

        else:
            # ==================================================================
            # NO CONGESTION: Window Increase
            # Goal: Aggressively grow window to maximize throughput
            # ==================================================================

            state["consecutive_decreases"] = 0

            if cWnd < ssThresh:
                # ==============================================================
                # SLOW START: Exponential Growth
                # Target: Quickly reach operating point near BDP
                # ==============================================================

                # Target 3x BDP to ensure we probe beyond optimal
                target_ss = 3 * bdp

                # Aggressive increase: 2 segments per ACK (vs standard 1)
                increase = 2 * segmentsAcked * segmentSize

                new_cwnd = min(cWnd + increase, int(target_ss))

                # Extra aggressive when far below BDP
                if cWnd < bdp * 0.3:
                    # Triple the increase rate when severely under-utilized
                    new_cwnd = min(cWnd + 3 * increase, int(target_ss))

                logger.debug(
                    f"Slow start: cwnd {cWnd} -> {new_cwnd}, "
                    f"target={int(target_ss)}, bdp={int(bdp)}"
                )

            else:
                # ==============================================================
                # CONGESTION AVOIDANCE: Controlled Growth
                # Gemini formula: V_t = max(alpha * BDP, W) + gamma
                # ==============================================================

                # Term 1: Rate-based target (alpha * BDP)
                term1 = alpha * bdp

                # Term 2: Current window (loss-based floor)
                term2 = cWnd

                # Gamma: Additive increase component (bytes)
                gamma_bytes = state["gamma"] * segmentSize

                # Fusion: Take maximum of rate-based and loss-based, add gamma
                target_ca = max(term1, term2) + gamma_bytes

                new_cwnd = int(target_ca)

                # ==============================================================
                # Utilization-Aware Boost
                # Increase more aggressively when pipe is under-utilized
                # ==============================================================
                if bytesInFlight > 0 and cWnd > 0:
                    utilization = bytesInFlight / cWnd

                    if utilization < 0.8:
                        # Under-utilized: Add 2 segments
                        new_cwnd = int(new_cwnd + 2 * segmentSize)

                    if utilization < 0.5:
                        # Severely under-utilized: Add 4 more segments
                        new_cwnd = int(new_cwnd + 4 * segmentSize)

                        logger.debug(
                            f"Low utilization boost: util={utilization:.2f}, "
                            f"extra increase applied"
                        )

                logger.debug(
                    f"Congestion avoidance: cwnd {cWnd} -> {new_cwnd}, "
                    f"alpha={alpha:.3f}, bdp={int(bdp)}, gamma={gamma_bytes}"
                )

            # ssThresh unchanged during increase phase
            new_ssThresh = ssThresh

        # ======================================================================
        # Safety Bounds
        # Prevent extreme values while allowing high throughput
        # ======================================================================

        # Minimum cwnd: 4 segments (ensures forward progress)
        min_cwnd = 4 * segmentSize

        # Maximum cwnd: 8x BDP or 100 segments (whichever is larger)
        # High cap enables full utilization of high-BDP paths
        if bdp > 0:
            max_cwnd = max(8 * bdp, 100 * segmentSize)
        else:
            max_cwnd = cWnd * 4

        new_cwnd = max(min_cwnd, min(new_cwnd, int(max_cwnd)))
        new_ssThresh = max(min_cwnd, new_ssThresh)

        return new_ssThresh, new_cwnd

    def get_action(self, obs, reward, done, info):
        """
        Main entry point: Process observation and compute congestion control action.

        This method is called by the ns-3 OpenGym environment on each
        congestion control event (ACK received or loss detected).

        Observation Vector (15 parameters):
        [0]  socketUuid    - Unique socket identifier
        [1]  envType       - Environment type (0=event-based)
        [2]  simTime_us    - Simulation time in microseconds
        [3]  nodeId        - Node identifier
        [4]  ssThresh      - Slow start threshold (bytes)
        [5]  cWnd          - Congestion window (bytes)
        [6]  segmentSize   - TCP segment size / MSS (bytes)
        [7]  segmentsAcked - Number of segments acknowledged
        [8]  bytesInFlight - Unacknowledged bytes in network
        [9]  lastRtt_us    - Last RTT measurement (microseconds)
        [10] minRtt_us     - Minimum observed RTT (microseconds)
        [11] calledFunc    - Callback type (0=GetSsThresh, 1=IncreaseWindow)
        [12] caState       - Congestion algorithm state
        [13] caEvent       - Congestion algorithm event
        [14] ecnState      - ECN state

        Args:
            obs: Observation vector (numpy array, length 15)
            reward: Reward from previous action (unused in this implementation)
            done: Episode termination flag
            info: Additional information dictionary

        Returns:
            list: [new_ssThresh, new_cWnd] - Updated congestion control parameters
        """
        # ======================================================================
        # Parse Observation Vector
        # ======================================================================
        socketUuid = obs[0]  # Flow identifier
        envType = obs[1]  # Environment type
        simTime_us = obs[2]  # Current simulation time
        nodeId = obs[3]  # Node ID
        ssThresh = obs[4]  # Current ssThresh
        cWnd = obs[5]  # Current cwnd
        segmentSize = obs[6]  # MSS
        segmentsAcked = obs[7]  # ACKed segments
        bytesInFlight = obs[8]  # In-flight bytes
        lastRtt_us = obs[9]  # Last RTT
        minRtt_us = obs[10]  # Min RTT
        calledFunc = obs[11]  # Callback type
        caState = obs[12]  # CA state
        caEvent = obs[13]  # CA event
        ecnState = obs[14]  # ECN state

        # ======================================================================
        # Get Per-Flow State
        # ======================================================================
        state = self._get_flow_state(socketUuid)

        # ======================================================================
        # Update Flow Metrics
        # ======================================================================
        self._update_metrics(state, obs)

        # ======================================================================
        # Compute Window Statistics
        # ======================================================================
        stats = self._get_window_stats(state)

        # ======================================================================
        # Detect Congestion
        # ======================================================================
        is_congested, cong_type, severity = self._detect_congestion(obs, state, stats)

        # ======================================================================
        # Calculate Target Congestion Window
        # ======================================================================
        new_ssThresh, new_cWnd = self._calculate_target_cwnd(
            obs, state, stats, is_congested, cong_type, severity
        )

        # Log periodic status for monitoring
        if int(simTime_us / 1e6) % 1 == 0 and state["prev_time"] > 0:
            time_diff = simTime_us - state["prev_time"]
            if time_diff > 500000:  # Log every 0.5 seconds
                logger.debug(
                    f"Flow {socketUuid}: cwnd={new_cWnd}, ssThresh={new_ssThresh}, "
                    f"rtt={lastRtt_us}us, throughput={stats['avg_throughput'] / 1e6:.2f}MB/s, "
                    f"alpha={state['alpha']:.3f}"
                )

        return [new_ssThresh, new_cWnd]
