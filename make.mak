.DEFAULT_GOAL=help
# =============================================================================
# Configuration
# =============================================================================
DURATION := 20
N_LEAF := 3
SIM_SEED := 42
PROTOCOLS := TcpGemini TcpNewReno TcpCubic TcpBbr
ENABLE_UDP_BURST := 0
GEMINI_LOG_DIR := ./logs/gemini
COMPARE_LOG_DIR := ./logs/comparison

# =============================================================================
# Git Targets
# =============================================================================
.PHONY: feat
feat: ## Introduce new features
	git add -A
	git commit -m "feat: Introduce new features"
	git push origin main

.PHONY: init
init: ## Initial commit
	rm -rf ./.git
	git init
	git remote add origin git@github.com:tianchenghang/ns3.40.git
	git add -A
	git commit -m "Initial commit"
	git push -f origin main --set-upstream

# =============================================================================
# Build & Clean
# =============================================================================
.PHONY: clean
clean: ## Remove ./build ./cmake-cache ./.lock-ns3* and caches
	rm -rf ./build ./cmake-cache \
	./.idea ./.cache ./.mypy_cache ./.ruff_cache ./.lock-ns3*

.PHONY: format
format: ## Format code
	find ./build-support ./contrib ./examples ./src ./scratch ./utils -name "*.h" \
	-o -name "*.c" \
	-o -name "*.hh" \
	-o -name "*.cc" \
	-o -name "*.hpp" \
	-o -name "*.cpp" \
	-o -name "*.h++" \
	-o -name "*.c++" \
	-o -name "*.hxx" \
	-o -name "*.cxx" | xargs clang-format -i
	ruff format ./
	prettier -w ./

.PHONY: build
build: ## Configure and build ns-3
	@conda activate ./.venv 2>/dev/null || source ./.venv/bin/activate 2>/dev/null || true
	@./ns3 configure --enable-mtp --enable-examples >/dev/null 2>&1
	@./ns3 build 2>/dev/null 2>&1
	@mkdir -p ./logs/gemini ./logs/gemini-udp ./logs/comparison ./logs/comparison-udp ./logs/summary ./logs/plots ./logs/plots-udp

.PHONY: setup
setup: build ## Setup and build ns-3

.PHONY: kill
kill: ## Kill all ns3 gemini processes
	pkill -f "ns3.40-gemini-t" && echo "Killed all ns3 gemini processes" || true

# =============================================================================
# Helper function for running simulations
# =============================================================================
define run_sim
	@$(MAKE) build --no-print-directory
	@mkdir -p $(7)
	@if [ -f "$(7)/$(2)_$(1).flowmonitor" ]; then \
		echo "[SKIP] $(2)_$(1) - flowmonitor already exists"; \
	else \
		echo "[INFO] Running: Protocol=$(1), Scenario=$(2)"; \
		echo "[INFO]   Access: $(3) @ $(5), Bottleneck: $(4) @ $(6)"; \
		START_TIME=$$(date +%s); \
		if [ "$(1)" = "TcpGemini" ]; then \
			./ns3 run "gemini-tcp \
			--transport_prot=$(1) \
			--access_bandwidth=$(3) \
			--bottleneck_bandwidth=$(4) \
			--access_delay=$(5) \
			--bottleneck_delay=$(6) \
			--duration=$(DURATION) \
			--nLeaf=$(N_LEAF) \
			--simSeed=$(SIM_SEED) \
			--enable_udp_burst=$(ENABLE_UDP_BURST) \
			--prefix_name=$(7)/$(2)_$(1)" 2>&1 | tee $(7)/$(2)_$(1)_ns3.log & \
			NS3_PID=$$!; \
			sleep 5; \
			for i in $$(seq 1 60); do \
				if ! kill -0 $$NS3_PID 2>/dev/null; then break; fi; \
					if grep -q "Waiting for Python" $(7)/$(2)_$(1)_ns3.log 2>/dev/null; then \
						python ./contrib/opengym/examples/gemini-tcp/test_gemini.py --start=0 --iterations=1 2>&1 | tee $(7)/$(2)_$(1)_agent.log; \
						break; \
					fi; \
				sleep 1; \
			done; \
			wait $$NS3_PID 2>/dev/null; \
			EXIT_CODE=$$?; \
			if [ $$EXIT_CODE -ne 0 ]; then \
				echo "[ERROR] Simulation failed: $(2)_$(1)"; \
				exit 1; \
			fi; \
		else \
			./ns3 run "gemini-tcp \
				--transport_prot=$(1) \
				--access_bandwidth=$(3) \
				--bottleneck_bandwidth=$(4) \
				--access_delay=$(5) \
				--bottleneck_delay=$(6) \
				--duration=$(DURATION) \
				--nLeaf=$(N_LEAF) \
				--simSeed=$(SIM_SEED) \
				--enable_udp_burst=$(ENABLE_UDP_BURST) \
				--prefix_name=$(7)/$(2)_$(1)" 2>&1 | tee $(7)/$(2)_$(1)_ns3.log; \
			EXIT_CODE=$$?; \
			if [ $$EXIT_CODE -ne 0 ]; then \
				echo "[ERROR] Simulation failed: $(2)_$(1)"; \
				exit 1; \
			fi; \
		fi; \
		END_TIME=$$(date +%s); \
		ELAPSED=$$((END_TIME - START_TIME)); \
		echo "[INFO] Completed: $(2) with $(1) in $${ELAPSED}s"; \
	fi
endef

.PHONY: compare
compare: ENABLE_UDP_BURST=0
compare: build ## Run comparison across multiple protocols (no UDP burst)
	@# intra_rack_10g
	$(call run_sim,TcpGemini,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison)
	$(call run_sim,TcpNewReno,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison)
	$(call run_sim,TcpCubic,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison)
	$(call run_sim,TcpBbr,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison)
	@# intra_rack_25g
	$(call run_sim,TcpGemini,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison)
	$(call run_sim,TcpNewReno,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison)
	$(call run_sim,TcpCubic,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison)
	$(call run_sim,TcpBbr,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison)
	@# leaf_spine_20g
	$(call run_sim,TcpGemini,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison)
	@# leaf_spine_50g
	$(call run_sim,TcpGemini,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison)
	@# oversub_4to1_10g
	$(call run_sim,TcpGemini,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison)
	@# oversub_4to1_40g
	$(call run_sim,TcpGemini,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison)
	@# oversub_2to1_25g
	$(call run_sim,TcpGemini,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison)
	@# oversub_2to1_50g
	$(call run_sim,TcpGemini,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison)
	@# congested_light
	$(call run_sim,TcpGemini,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison)
	@# congested_medium
	$(call run_sim,TcpGemini,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison)
	@# congested_heavy
	$(call run_sim,TcpGemini,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpNewReno,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpCubic,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison)
	$(call run_sim,TcpBbr,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison)
	@# cross_pod_10g
	$(call run_sim,TcpGemini,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison)
	$(call run_sim,TcpNewReno,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison)
	$(call run_sim,TcpCubic,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison)
	$(call run_sim,TcpBbr,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison)
	@# cross_pod_20g
	$(call run_sim,TcpGemini,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison)
	$(call run_sim,TcpNewReno,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison)
	$(call run_sim,TcpCubic,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison)
	$(call run_sim,TcpBbr,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison)
	@# cross_dc_wan
	$(call run_sim,TcpGemini,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison)
	$(call run_sim,TcpNewReno,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison)
	$(call run_sim,TcpCubic,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison)
	$(call run_sim,TcpBbr,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison)
	@# rdma_like_25g
	$(call run_sim,TcpGemini,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison)
	$(call run_sim,TcpNewReno,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison)
	$(call run_sim,TcpCubic,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison)
	$(call run_sim,TcpBbr,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison)
	@# rdma_like_50g
	$(call run_sim,TcpGemini,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison)
	$(call run_sim,TcpNewReno,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison)
	$(call run_sim,TcpCubic,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison)
	$(call run_sim,TcpBbr,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison)
	@# mixed_small_flow
	$(call run_sim,TcpGemini,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison)
	$(call run_sim,TcpNewReno,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison)
	$(call run_sim,TcpCubic,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison)
	$(call run_sim,TcpBbr,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison)
	@# mixed_large_flow
	$(call run_sim,TcpGemini,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison)
	$(call run_sim,TcpNewReno,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison)
	$(call run_sim,TcpCubic,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison)
	$(call run_sim,TcpBbr,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison)
	@# asymmetric_high
	$(call run_sim,TcpGemini,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison)
	$(call run_sim,TcpNewReno,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison)
	$(call run_sim,TcpCubic,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison)
	$(call run_sim,TcpBbr,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison)
	@# symmetric_low
	$(call run_sim,TcpGemini,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison)
	$(call run_sim,TcpNewReno,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison)
	$(call run_sim,TcpCubic,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison)
	$(call run_sim,TcpBbr,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison)

.PHONY: compare-udp
compare-udp: ENABLE_UDP_BURST=1
compare-udp: build ## Run comparison across multiple protocols (with UDP burst)
	@# intra_rack_10g
	$(call run_sim,TcpGemini,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,intra_rack_10g,25Gbps,10Gbps,1us,2us,./logs/comparison-udp)
	@# intra_rack_25g
	$(call run_sim,TcpGemini,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,intra_rack_25g,25Gbps,25Gbps,1us,2us,./logs/comparison-udp)
	@# leaf_spine_20g
	$(call run_sim,TcpGemini,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,leaf_spine_20g,50Gbps,20Gbps,2us,5us,./logs/comparison-udp)
	@# leaf_spine_50g
	$(call run_sim,TcpGemini,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,leaf_spine_50g,50Gbps,50Gbps,2us,5us,./logs/comparison-udp)
	@# oversub_4to1_10g
	$(call run_sim,TcpGemini,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,oversub_4to1_10g,10Gbps,2.5Gbps,2us,5us,./logs/comparison-udp)
	@# oversub_4to1_40g
	$(call run_sim,TcpGemini,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,oversub_4to1_40g,40Gbps,10Gbps,2us,5us,./logs/comparison-udp)
	@# oversub_2to1_25g
	$(call run_sim,TcpGemini,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,oversub_2to1_25g,25Gbps,12.5Gbps,2us,5us,./logs/comparison-udp)
	@# oversub_2to1_50g
	$(call run_sim,TcpGemini,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,oversub_2to1_50g,50Gbps,25Gbps,2us,5us,./logs/comparison-udp)
	@# congested_light
	$(call run_sim,TcpGemini,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,congested_light,10Gbps,5Gbps,2us,5us,./logs/comparison-udp)
	@# congested_medium
	$(call run_sim,TcpGemini,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,congested_medium,10Gbps,2Gbps,2us,5us,./logs/comparison-udp)
	@# congested_heavy
	$(call run_sim,TcpGemini,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,congested_heavy,10Gbps,1Gbps,2us,5us,./logs/comparison-udp)
	@# cross_pod_10g
	$(call run_sim,TcpGemini,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,cross_pod_10g,25Gbps,10Gbps,5us,50us,./logs/comparison-udp)
	@# cross_pod_20g
	$(call run_sim,TcpGemini,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,cross_pod_20g,50Gbps,20Gbps,5us,50us,./logs/comparison-udp)
	@# cross_dc_wan
	$(call run_sim,TcpGemini,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison-udp)
	$(call run_sim,TcpCubic,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison-udp)
	$(call run_sim,TcpBbr,cross_dc_wan,10Gbps,1Gbps,10us,5ms,./logs/comparison-udp)
	@# rdma_like_25g
	$(call run_sim,TcpGemini,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,rdma_like_25g,25Gbps,25Gbps,500ns,1us,./logs/comparison-udp)
	@# rdma_like_50g
	$(call run_sim,TcpGemini,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,rdma_like_50g,50Gbps,50Gbps,500ns,1us,./logs/comparison-udp)
	@# mixed_small_flow
	$(call run_sim,TcpGemini,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,mixed_small_flow,10Gbps,2Gbps,2us,10us,./logs/comparison-udp)
	@# mixed_large_flow
	$(call run_sim,TcpGemini,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,mixed_large_flow,50Gbps,12.5Gbps,2us,10us,./logs/comparison-udp)
	@# asymmetric_high
	$(call run_sim,TcpGemini,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,asymmetric_high,50Gbps,1Gbps,1us,10us,./logs/comparison-udp)
	@# symmetric_low
	$(call run_sim,TcpGemini,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison-udp)
	$(call run_sim,TcpNewReno,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison-udp)
	$(call run_sim,TcpCubic,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison-udp)
	$(call run_sim,TcpBbr,symmetric_low,1Gbps,1Gbps,5us,20us,./logs/comparison-udp)

.PHONY: draw
draw: ## Generate plots for non-UDP logs
	python draw.py

.PHONY: all
all: gemini compare ## Run all simulations (gemini + compare)

# =============================================================================
# Summary Report
# =============================================================================
.PHONY: summary
summary: ## Generate summary report from existing logs
	@echo "[INFO] Generating Summary Report"
	@mkdir -p ./logs/summary
	@TAG=$$(if [ "$(ENABLE_UDP_BURST)" = "1" ]; then echo udp; else echo tcp; fi); \
	OUT=./logs/summary/results_$${TAG}_$$(date '+%Y%m%d_%H%M%S').csv; \
	echo "Scenario,Protocol,AccessBW,BottleneckBW,AccessDelay,BottleneckDelay,Throughput_Mbps,LossRate_Pct,AvgRTT_ms" > $$OUT; \
	if [ "$(ENABLE_UDP_BURST)" = "1" ]; then \
		SEARCH_DIRS="./logs/gemini-udp ./logs/comparison-udp"; \
	else \
		SEARCH_DIRS="./logs/gemini ./logs/comparison"; \
	fi; \
	for dir in $$SEARCH_DIRS; do \
		for flowmon in $$dir/*.flowmonitor; do \
			if [ -f "$$flowmon" ]; then \
				basename=$$(basename "$$flowmon" .flowmonitor); \
				scenario=$$(echo "$$basename" | rev | cut -d'_' -f2- | rev); \
				protocol=$$(echo "$$basename" | rev | cut -d'_' -f1 | rev); \
				log_file="$${flowmon%.flowmonitor}_ns3.log"; \
				if [ -f "$$log_file" ]; then \
					throughput=$$(grep -oP 'Throughput: \K[0-9.]+' "$$log_file" 2>/dev/null | head -1 || echo "N/A"); \
					loss_rate=$$(grep -oP 'Loss Rate: \K[0-9.]+' "$$log_file" 2>/dev/null | head -1 || echo "N/A"); \
					access_bw=$$(grep -oP 'AccessBW:\s*\K[0-9.]+[A-Za-z]*' "$$log_file" 2>/dev/null | head -1 || echo "N/A"); \
					bottleneck_bw=$$(grep -oP 'BottleneckBW:\s*\K[0-9.]+[A-Za-z]*' "$$log_file" 2>/dev/null | head -1 || echo "N/A"); \
					echo "$$scenario,$$protocol,$$access_bw,$$bottleneck_bw,$$throughput,$$loss_rate," >> $$OUT; \
				fi; \
			fi; \
		done; \
	done; \
	echo "[INFO] Summary saved to $$OUT"

.PHONY: summary-udp
summary-udp: ENABLE_UDP_BURST=1
summary-udp: summary ## Generate UDP summary report

# =============================================================================
# Help
# =============================================================================
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	cut -d ":" -f1- | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
