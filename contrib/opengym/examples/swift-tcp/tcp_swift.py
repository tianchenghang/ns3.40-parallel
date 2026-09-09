# Copyright 2026 hangtiancheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Swift TCP Congestion Control Algorithm - Optimized Implementation (v2.1)

Optimization priority:
  1. Maximize throughput (primary)
  2. Minimize transmission delay (secondary)
  3. Minimize loss/retransmission rate (tertiary)
  4. Inter-flow fairness (quaternary)

Core design (v2, informed by logs/error.txt audit):
  - Windowed max-filter delivery-rate BDP estimate (BBR-style)
  - Aggressive slow start with HyStart-like RTT-inflation exit
  - Delay-aware CA window: V_t = alpha(rtt_ratio) * BDP + gamma * MSS
  - Differentiated response: Loss > Timeout > ECN (proactive, mild)
  - Utilization booster suppressed when queue is filling (rtt_ratio > 1.3)
  - Consecutive-decrease floor + post-decrease freeze to avoid over-reduction
  - WAN-friendly alpha scheduler (thresholds scale with min_rtt)

v2.1 changes (2026-05-21, informed by logs/plots*/summary.csv audit):
  - WAN under-utilization fix (wan_longhaul -86% throughput vs Cubic):
      * bw_window_len 20 -> 40 (stabilize BDP estimate on long-RTT paths)
      * HyStart RTT-inflation threshold scales with min_rtt
        (1.25 for DC <=1 ms; 1.30 for 1-5 ms; 1.40 for WAN >5 ms)
      * CA pull-up converges in <=16 ACK events instead of one MSS per ACK
        (step = max(gamma*MSS, MSS, gap//16))
  - Shallow-buffer queue inflation fix (dc_100m +130%, wifi_n +76% delay):
      * alpha_max 1.45 -> 1.30 (cap chronic queue build-up at 1.30x BDP)
      * alpha_base 1.15 -> 1.10 (smaller starting bias)
      * alpha_min 0.95 -> 0.85 (deeper drain headroom for wireless)
      * Drain rate excess//4 -> excess//2 (twice as fast queue drain)
      * Utilization booster degrades on long-RTT (>5 ms) wireless paths:
        +2*MSS -> +1*MSS, suppress booster when utilization >=0.5
      * Alpha ramp-up step 0.03 -> 0.02 on >5 ms paths

v3.0 changes (2026-08-20, review findings C1-C4):
  - C1 CRITICAL: delivery rate is now measured as cumulative ACKed bytes
    over a sliding time window (>= 2*min_rtt).  The old per-ACK formula
    segmentsAcked*segSize/lastRtt under-estimated bandwidth by roughly the
    number of ACKs per RTT, collapsing the BDP estimate; cwnd then pinned
    at the 200*MSS safety floor, capping WAN throughput at 200*MSS/RTT
    (wan_longhaul 45 Mbps, cross_dc_wan 237 Mbps -- both match that
    ceiling exactly).
  - C3: ECE/CWR-triggered GetSsThresh callbacks are classified as "ecn"
    (beta=0.75) instead of falling through to the generic "loss" branch.
  - C4: reward adaptation is baseline-relative (fast EMA vs slow EMA)
    instead of fixed thresholds; the per-ACK reward is >= +0.5 on nearly
    every ACK, so the old "ema > 0.5" test was a constant +0.01 ratchet.
  - Freeze semantics: the consecutive-decrease counter is no longer reset
    while the post-decrease freeze is active.
"""

import logging
from collections import deque
from tcp_base import TcpEventBased

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TcpSwift")
logger.setLevel(logging.WARNING)


class TcpSwift(TcpEventBased):
    # ECN State Constants
    ECN_DISABLED = 0
    ECN_IDLE = 1
    ECN_CE_RCVD = 2
    ECN_SENDING_ECE = 3
    ECN_ECE_RCVD = 4
    ECN_CWR_SENT = 5

    # CA State Constants
    CA_OPEN = 0
    CA_DISORDER = 1
    CA_CWR = 2
    CA_RECOVERY = 3
    CA_LOSS = 4

    # CA Event Constants
    CA_EVENT_TX_START = 0
    CA_EVENT_CWND_RESTART = 1
    CA_EVENT_COMPLETE_CWR = 2
    CA_EVENT_LOSS = 3
    CA_EVENT_ECN_NO_CE = 4
    CA_EVENT_ECN_IS_CE = 5

    # Called Function Constants
    FUNC_GET_SS_THRESH = 0
    FUNC_INCREASE_WINDOW = 1

    def __init__(self):
        super(TcpSwift, self).__init__()

        # --- Core parameters (throughput + delay balanced) ---
        # v2.1: alpha_max lowered (1.45 -> 1.30) to cap chronic queue build-up
        # observed in dc_100m / wifi_n / lte_poor / nr_5g_edge.
        # alpha_min lowered (0.95 -> 0.85) gives deeper drain headroom on
        # wireless / cellular paths whose buffer-bloat is the dominant issue.
        self.alpha_base = 1.10  # Target cwnd = alpha * BDP (was 1.15)
        self.alpha_min = 0.85  # Allow under-shoot for delay recovery
        self.alpha_max = 1.30  # was 1.45 — too aggressive for shallow buffers

        # Additive increase term (applied once per ACK event, NOT per segment)
        self.gamma = 1.0  # was 2.0; per-ACK MSS additive in CA

        # Multiplicative decrease factors (window retention ratios)
        # Ordering re-calibrated based on severity: timeout worst, loss moderate,
        # ECN mild but NOT as tolerant as before (was 0.85 -> queue built up).
        self.beta_loss = 0.70  # Retain 70% on packet loss
        self.beta_ecn = 0.75  # Retain 75% on ECN (was 0.85; too tolerant)
        self.beta_timeout = 0.50

        # Consecutive decrease protection
        self.max_consecutive_decreases = 3

        # Post-decrease freeze: hold cwnd for N ACK-events to let queue drain
        self.post_decrease_freeze_events = 4

        # BDP estimation window
        # v2.1: bw_window_len 20 -> 40 stabilizes BDP estimate on long-RTT WAN
        # where each ACK takes 25-300 ms and a 20-sample window may decay
        # before the bottleneck is fully sampled (wan_longhaul / satellite).
        self.bw_window_len = 40
        self.rtt_window_len = 40

        # HyStart-style slow-start exit: fraction of min_rtt that counts as
        # "queueing detected".  v2.1 makes this min_rtt-aware (see
        # _hystart_threshold) so that WAN paths don't exit too early.
        self.hystart_rtt_inflation = 1.25

        # Per-flow state
        self.flow_states = {}

        # Reward-based adaptation: fast EMA compared against a slow baseline
        # EMA. The per-ACK reward is >= +0.5 on nearly every ACK, so fixed
        # thresholds degenerated into a constant +0.01 ratchet toward
        # alpha_max; only a relative signal carries information.
        self.reward_ema = 0.0
        self.reward_alpha = 0.15
        self.reward_baseline = 0.0
        self.reward_baseline_alpha = 0.02
        self.reward_initialized = False

    # ------------------------------------------------------------------
    # Per-flow state
    # ------------------------------------------------------------------
    def _get_flow_state(self, socket_uuid):
        if socket_uuid not in self.flow_states:
            self.flow_states[socket_uuid] = {
                # Bandwidth estimation (windowed max-filter over rate samples)
                "bw_samples": deque(maxlen=self.bw_window_len),
                "max_bw": 0.0,
                # Delivery-rate sampling: (simTime_us, cumulative acked bytes)
                "ack_samples": deque(maxlen=4096),
                "acked_bytes_total": 0,
                # RTT tracking
                "rtt_samples": deque(maxlen=self.rtt_window_len),
                "min_rtt_us": float("inf"),
                # BDP
                "bdp": 0.0,
                # Adaptive alpha (per-flow)
                "alpha": self.alpha_base,
                # Congestion counters
                "consecutive_decreases": 0,
                "consecutive_increases": 0,
                "loss_count": 0,
                "ecn_count": 0,
                "last_decrease_time_us": 0,
                # Post-decrease freeze counter (in ACK events)
                "freeze_acks_remaining": 0,
                # State tracking
                "prev_cwnd": 0,
                "prev_time_us": 0,
                # Throughput tracking for reward adaptation
                "throughput_ema": 0.0,
                # Phase tracking
                "in_slow_start": True,
                # HyStart: monotonic rise of RTT during slow start
                "ss_min_rtt_sample": float("inf"),
            }
        return self.flow_states[socket_uuid]

    # ------------------------------------------------------------------
    # Bandwidth / RTT / BDP estimation
    # ------------------------------------------------------------------
    def _update_bandwidth(self, state, obs):
        simTime_us = obs[2]
        segmentSize = obs[6]
        segmentsAcked = obs[7]
        lastRtt_us = obs[9]
        minRtt_us = obs[10]

        # Update min RTT (prefer kernel-reported minRtt when valid)
        if lastRtt_us > 0:
            state["rtt_samples"].append(lastRtt_us)
            if lastRtt_us < state["min_rtt_us"]:
                state["min_rtt_us"] = lastRtt_us
            # HyStart: track minimum RTT within current slow-start episode
            if state["in_slow_start"] and lastRtt_us < state["ss_min_rtt_sample"]:
                state["ss_min_rtt_sample"] = lastRtt_us

        if 0 < minRtt_us < state["min_rtt_us"]:
            state["min_rtt_us"] = minRtt_us

        # Delivery rate: cumulative ACKed bytes over a sliding time window.
        # The window spans >= 2*min_rtt so the rate reflects the ACK clock
        # (bottleneck drain rate) rather than a single ACK's payload, which
        # under-estimated bandwidth by ~the number of ACKs per RTT.
        if segmentsAcked > 0 and segmentSize > 0:
            state["acked_bytes_total"] += segmentsAcked * segmentSize
            samples = state["ack_samples"]
            samples.append((simTime_us, state["acked_bytes_total"]))

            if state["min_rtt_us"] < float("inf"):
                window_us = min(max(2 * state["min_rtt_us"], 5_000), 1_000_000)
            else:
                window_us = 5_000
            while len(samples) >= 2 and simTime_us - samples[0][0] > window_us:
                samples.popleft()

            span_us = simTime_us - samples[0][0]
            delivered = state["acked_bytes_total"] - samples[0][1]
            if len(samples) >= 2 and span_us > 0 and delivered > 0:
                delivery_rate = delivered / (span_us / 1e6)  # bytes/s
                state["bw_samples"].append(delivery_rate)
                state["max_bw"] = max(state["bw_samples"])
                # Throughput EMA
                if state["throughput_ema"] == 0:
                    state["throughput_ema"] = delivery_rate
                else:
                    state["throughput_ema"] = (
                        0.9 * state["throughput_ema"] + 0.1 * delivery_rate
                    )

        # BDP = max_bw * min_rtt (bytes)
        if state["max_bw"] > 0 and state["min_rtt_us"] < float("inf"):
            state["bdp"] = state["max_bw"] * (state["min_rtt_us"] / 1e6)

    def _get_bdp(self, state, cWnd):
        if state["bdp"] > 0:
            return state["bdp"]
        return max(cWnd, 1)

    # ------------------------------------------------------------------
    # HyStart slow-start exit threshold (min_rtt-aware, v2.1)
    # ------------------------------------------------------------------
    def _hystart_threshold(self, state):
        """Scale RTT-inflation tolerance with min_rtt so WAN does not exit
        slow-start prematurely.  DC keeps the original 1.25x; WAN goes up to
        1.40x.  Empirically motivated by wan_longhaul (-86% throughput) where
        the fixed 1.25x exit fired during the first BDP filling burst."""
        if state["min_rtt_us"] >= float("inf") or state["min_rtt_us"] <= 0:
            return self.hystart_rtt_inflation
        min_rtt_ms = state["min_rtt_us"] / 1000.0
        if min_rtt_ms <= 1.0:
            return 1.25
        if min_rtt_ms <= 5.0:
            return 1.30
        return 1.40

    # ------------------------------------------------------------------
    # Alpha adaptation (WAN-aware, delay-aware)
    # ------------------------------------------------------------------
    def _adapt_alpha(self, state, obs, reward):
        lastRtt_us = obs[9]
        alpha = state["alpha"]

        # Factor 1: RTT-ratio feedback with WAN-friendly scaling.
        # Rationale (logs/error.txt #6): fixed 1.3/2.0/3.0 thresholds shrink
        # alpha too aggressively on WAN where absolute jitter is larger.
        # Scale the ratio thresholds with min_rtt: a 5 ms link tolerates a
        # much larger relative inflation than a 50 us link before it
        # actually indicates bottleneck queuing.
        if lastRtt_us > 0 and 0 < state["min_rtt_us"] < float("inf"):
            min_rtt_ms = state["min_rtt_us"] / 1000.0
            # Slack grows with sqrt(min_rtt_ms) — DC (tight) vs WAN (loose)
            slack = 0.3 + 0.15 * max(0.0, min_rtt_ms - 1.0) ** 0.5
            rtt_ratio = lastRtt_us / state["min_rtt_us"]
            low_th = 1.0 + slack
            mid_th = 1.0 + 2.0 * slack
            high_th = 1.0 + 4.0 * slack

            if rtt_ratio < low_th:
                # Minimal queuing -> increase aggressiveness.  v2.1: smaller
                # ramp-up on long-RTT (>5 ms) wireless/WAN where overshoot is
                # punished by deep queues (lte_poor / wifi_legacy).
                ramp = 0.02 if min_rtt_ms > 5.0 else 0.03
                alpha = min(alpha + ramp, self.alpha_max)
                state["consecutive_increases"] += 1
            elif rtt_ratio < mid_th:
                alpha = min(alpha + 0.01, self.alpha_max)
            elif rtt_ratio > high_th:
                # Heavy queuing -> reduce (but not below alpha_min).
                # v2.1: faster contraction (-0.03) on long-RTT paths to drain
                # bloat quickly on dc_100m / wifi_n / nr_5g_edge.
                step = 0.03 if min_rtt_ms > 5.0 else 0.02
                alpha = max(alpha - step, self.alpha_min)
                state["consecutive_increases"] = 0

        # Factor 2: Reward signal from C++ env, judged RELATIVE to its own
        # slow baseline. Absolute thresholds carried no information because
        # the per-ACK reward is almost always positive.
        if reward is not None:
            r = float(reward)
            if not self.reward_initialized:
                self.reward_ema = r
                self.reward_baseline = r
                self.reward_initialized = True
            else:
                self.reward_ema = (
                    1 - self.reward_alpha
                ) * self.reward_ema + self.reward_alpha * r
                self.reward_baseline = (
                    1 - self.reward_baseline_alpha
                ) * self.reward_baseline + self.reward_baseline_alpha * r
            margin = max(0.25, 0.1 * abs(self.reward_baseline))
            if self.reward_ema > self.reward_baseline + margin:
                alpha = min(alpha + 0.01, self.alpha_max)
            elif self.reward_ema < self.reward_baseline - 4.0 * margin:
                alpha = max(alpha - 0.01, self.alpha_min)

        # Factor 3: Stable growth bonus
        if state["consecutive_increases"] > 8:
            alpha = min(alpha + 0.01, self.alpha_max)

        state["alpha"] = alpha
        return alpha

    # ------------------------------------------------------------------
    # Congestion detection
    # ------------------------------------------------------------------
    def _detect_congestion(self, obs, state):
        calledFunc = obs[11]
        caState = obs[12]
        ecnState = obs[14]

        # Signal 1: GetSsThresh called -- the stack is reducing the window.
        # Distinguish WHY before treating it as loss: an ECE-triggered CWR
        # entry also calls GetSsThresh and must get the ECN response
        # (beta=0.75), not the loss response (beta=0.70).
        if calledFunc == self.FUNC_GET_SS_THRESH:
            if caState == self.CA_LOSS:
                state["loss_count"] += 1
                return True, "timeout"
            if (
                ecnState in (self.ECN_CE_RCVD, self.ECN_ECE_RCVD)
                or caState == self.CA_CWR
            ):
                state["ecn_count"] += 1
                return True, "ecn"
            state["loss_count"] += 1
            return True, "loss"

        # Signal 2: ECN CE received during IncreaseWindow
        if ecnState in (self.ECN_CE_RCVD, self.ECN_ECE_RCVD):
            state["ecn_count"] += 1
            return True, "ecn"

        return False, None

    # ------------------------------------------------------------------
    # Congestion response
    # ------------------------------------------------------------------
    def _congestion_response(self, obs, state, cong_type):
        cWnd = obs[5]
        segmentSize = obs[6]
        simTime_us = obs[2]
        bdp = self._get_bdp(state, cWnd)
        min_cwnd = max(4 * segmentSize, 1)

        state["consecutive_decreases"] += 1
        state["consecutive_increases"] = 0

        # Post-decrease freeze: suppress growth for several subsequent ACKs
        state["freeze_acks_remaining"] = self.post_decrease_freeze_events

        # Floor: too many consecutive reductions -> hold current window
        if state["consecutive_decreases"] > self.max_consecutive_decreases:
            new_cwnd = max(cWnd, min_cwnd)
            new_ssThresh = new_cwnd
            return new_ssThresh, new_cwnd

        if cong_type == "timeout":
            beta = self.beta_timeout
            # Re-enter slow start on timeout (Reno-like semantics)
            state["in_slow_start"] = True
            state["ss_min_rtt_sample"] = float("inf")
        elif cong_type == "ecn":
            beta = self.beta_ecn
        else:  # "loss"
            beta = self.beta_loss

        new_cwnd = max(int(beta * cWnd), min_cwnd)

        # ssThresh: use beta * max(cWnd, BDP) — don't reward queue inflation
        # by setting ssThresh above BDP+.
        ref_for_ssthresh = min(cWnd, int(max(bdp, min_cwnd)))
        new_ssThresh = max(int(beta * ref_for_ssthresh), min_cwnd)
        # But never below new_cwnd (so CA can still probe slowly above)
        new_ssThresh = max(new_ssThresh, new_cwnd)

        state["last_decrease_time_us"] = simTime_us
        return new_ssThresh, new_cwnd

    # ------------------------------------------------------------------
    # Window increase (slow start / congestion avoidance)
    # ------------------------------------------------------------------
    def _increase_window(self, obs, state, alpha):
        ssThresh = obs[4]
        cWnd = obs[5]
        segmentSize = obs[6]
        segmentsAcked = obs[7]
        bytesInFlight = obs[8]
        lastRtt_us = obs[9]
        bdp = self._get_bdp(state, cWnd)

        if segmentSize <= 0:
            segmentSize = 1448

        # Post-decrease freeze: hold cwnd for a few ACKs to let the queue drain
        if state["freeze_acks_remaining"] > 0:
            state["freeze_acks_remaining"] -= 1
            return ssThresh, cWnd

        # Reset consecutive-decrease counter only when we actually grow
        state["consecutive_decreases"] = 0

        # ---------- Slow start (with HyStart-style RTT-inflation exit) ----------
        if cWnd < ssThresh and state["in_slow_start"]:
            # HyStart exit: if current RTT > threshold * min_rtt in slow-start,
            # queueing is happening -> leave slow start.  v2.1: threshold is
            # min_rtt-aware (1.25 DC, 1.30 mid, 1.40 WAN) so wan_longhaul does
            # not exit on first BDP-filling burst.
            hystart_th = self._hystart_threshold(state)
            if (
                lastRtt_us > 0
                and state["ss_min_rtt_sample"] < float("inf")
                and lastRtt_us > hystart_th * state["ss_min_rtt_sample"]
            ):
                state["in_slow_start"] = False
                return max(ssThresh, cWnd), cWnd

            # Target: 2x BDP (avoid overshoot burst loss)
            target_ss = max(int(2.0 * bdp), 10 * segmentSize)

            # Standard exponential: +1 MSS per ACKed segment
            increase = segmentsAcked * segmentSize

            # Accelerate only when clearly below BDP AND RTT indicates no queue
            if bdp > 0 and cWnd < 0.3 * bdp:
                if (
                    state["min_rtt_us"] < float("inf")
                    and lastRtt_us > 0
                    and lastRtt_us < 1.2 * state["min_rtt_us"]
                ):
                    increase = 2 * segmentsAcked * segmentSize

            new_cwnd = min(cWnd + increase, target_ss)

            if new_cwnd >= target_ss:
                state["in_slow_start"] = False
                new_ssThresh = new_cwnd  # <- fix for previous dead-code bug
            else:
                new_ssThresh = ssThresh
            return new_ssThresh, new_cwnd

        # ---------- Congestion avoidance ----------
        state["in_slow_start"] = False

        # v2 Swift formula: target = alpha * BDP + gamma * MSS
        #   (CRITICAL FIX: cWnd no longer appears in max(); this was the root
        #    cause of monotonic queue inflation identified in error.txt #5.)
        target_rate = int(alpha * bdp) if bdp > 0 else cWnd
        gamma_bytes = int(self.gamma * segmentSize)

        # Base: move toward alpha*BDP, then add per-event gamma.
        # If current cWnd is close to target, grow at Reno pace (+MSS^2/cWnd).
        # If below target, pull up by one step toward target.
        # If above target, ease down by half of the excess per ACK (v2.1: was
        # quarter — too slow on shallow buffers, dc_100m delay was 2.3x Cubic).
        if target_rate > cWnd:
            # Pull up: v2.1 converges in <=16 ACK events instead of one MSS
            # per ACK.  On wan_longhaul a 138 Mbps cap was caused by the old
            # 1-MSS-per-ACK growth that took thousands of RTTs to fill BDP.
            gap = target_rate - cWnd
            step = max(gamma_bytes, segmentSize, gap // 16)
            new_cwnd = min(cWnd + step, target_rate + gamma_bytes)
        elif target_rate < cWnd:
            # Ease down (drain queue) — half of excess per ACK
            excess = cWnd - target_rate
            new_cwnd = max(cWnd - max(excess // 2, segmentSize), target_rate)
        else:
            # Reno-like additive increase when at target
            new_cwnd = cWnd + gamma_bytes

        # Utilization-aware boost — ONLY when queue is NOT building.
        # Root cause #7 in error.txt: the old double-counted +MSS and +2*MSS
        # booster inflated queues on wifi_n / dc_100m.  v2.1: degrade boost on
        # long-RTT (>5 ms) paths and suppress entirely above 0.5 utilization.
        if bytesInFlight > 0 and cWnd > 0 and lastRtt_us > 0:
            utilization = bytesInFlight / cWnd
            rtt_ok = (
                state["min_rtt_us"] < float("inf")
                and lastRtt_us < 1.3 * state["min_rtt_us"]
            )
            if rtt_ok:
                long_rtt = (
                    state["min_rtt_us"] < float("inf")
                    and state["min_rtt_us"] > 5_000  # 5 ms in microseconds
                )
                if utilization < 0.4:
                    new_cwnd += segmentSize if long_rtt else 2 * segmentSize
                elif utilization < 0.5 and not long_rtt:
                    new_cwnd += segmentSize

        new_ssThresh = ssThresh
        return new_ssThresh, new_cwnd

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def get_action(self, obs, reward, done, info):
        """
        Observation vector (15 params from ns-3):
        [0]  socketUuid, [1] envType, [2] simTime_us, [3] nodeId,

        # ------------ Observation space ------------
        [4]  ssThresh, [5] cWnd, [6] segmentSize, [7] segmentsAcked,
        [8]  bytesInFlight, [9] lastRtt_us, [10] minRtt_us,
        [11] calledFunc, [12] caState, [13] caEvent, [14] ecnState

        Returns: [new_ssThresh, new_cWnd]
        """
        socketUuid = obs[0]
        cWnd = obs[5]
        segmentSize = obs[6]

        state = self._get_flow_state(socketUuid)

        # Update bandwidth/RTT estimates
        self._update_bandwidth(state, obs)

        # Adapt alpha using reward + RTT signals
        alpha = self._adapt_alpha(state, obs, reward)

        # Detect congestion
        is_congested, cong_type = self._detect_congestion(obs, state)

        if is_congested:
            new_ssThresh, new_cWnd = self._congestion_response(obs, state, cong_type)
        else:
            new_ssThresh, new_cWnd = self._increase_window(obs, state, alpha)

        # === Safety bounds ===
        min_cwnd = max(4 * segmentSize, 1) if segmentSize > 0 else 4
        bdp = self._get_bdp(state, cWnd)

        # Max cwnd: tighter cap — 4x BDP instead of 10x (prevents runaway
        # build-up when BDP estimate is stale).  For low-BDP / unknown-BDP
        # paths, keep the 200*MSS floor.
        if bdp > 0 and segmentSize > 0:
            max_cwnd = max(int(4 * bdp), 200 * segmentSize)
        else:
            max_cwnd = max(cWnd * 4, 200 * segmentSize if segmentSize > 0 else cWnd * 4)

        new_cWnd = max(min_cwnd, min(new_cWnd, max_cwnd))
        new_ssThresh = max(min_cwnd, new_ssThresh)

        state["prev_cwnd"] = new_cWnd
        state["prev_time_us"] = obs[2]

        return [new_ssThresh, new_cWnd]
