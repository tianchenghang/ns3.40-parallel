.DEFAULT_GOAL=help

.PHONY: chore
chore: ## Regular code maintenance
	git add -A
	git commit -m "chore: Regular code maintenance"
	git push origin main

.PHONY: feat
feat: ## Introduce new features
	git add -A
	git commit -m "feat: Introduce new features"
	git push origin main

.PHONY: fix
fix: ## Fix some bugs
	git add -A
	git commit -m "fix: Fix some bugs"
	git push origin main

.PHONY: style
style: ## Update styling
	git add -A
	git commit -m "style: Update styling"
	git push origin main

.PHONY: refactor
refactor: ## Refactor code
	git add -A
	git commit -m "refactor: Refactor code"
	git push origin main

.PHONY: test
test: ## Create/Update testing
	git add -A
	git commit -m "test: Create/Update testing"
	git push origin main

.PHONY: docs
docs: ## Create/Update documentation
	git add -A
	git commit -m "docs: Create/Update docs"
	git push origin main

.PHONY: perf
perf: ## Performance optimization
	git add -A
	git commit -m "perf: Performance optimization"
	git push origin main

.PHONY: init
init: ## Initial commit
	rm -rf ./.git
	git init
	git remote add origin git@github.com:tianchenghang/ns3.40-parallel.git
	git add -A
	git commit -m "Initial commit"
	git push -f origin main --set-upstream

.PHONY: clean
clean: ## Remove ./build ./dist ./lib ./target ./.idea and caches
	rm -rf ./build ./dist ./lib ./target \
	./.idea ./.cache ./.mypy_cache ./.ruff_cache

.PHONY: format
format: build ## Format code
	prettier --write ./ # JavaScript, TypeScript, Markdown
	(cd ./build && ninja format) || echo 'clang-format not found'

.PHONY: build
build: ## Run cmake, tsc and go build
	@echo "Make clang++/g++ binary files, output ./build"
	rm -rf ./build
	cmake -S . -B ./build
	cmake --build ./build

	@echo "Make tsc compiled JS files, output: ./dist"
	rm -rf ./dist
	pnpm build # tsc

.PHONY: help
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	cut -d ":" -f1- |                                        \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
