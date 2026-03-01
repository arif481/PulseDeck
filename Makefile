.PHONY: run run-root install install-desktop uninstall lint clean help

PYTHON ?= python3
PREFIX ?= /usr/local
APP_ID  = com.pulsedeck.app

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

run: ## Run PulseDeck
	$(PYTHON) main.py

run-root: ## Run PulseDeck with root access (governor, SMART, kill)
	sudo $(PYTHON) main.py

install-desktop: ## Install .desktop entry for current user
	@mkdir -p ~/.local/share/applications
	@sed 's|Exec=.*|Exec=$(PYTHON) $(CURDIR)/main.py|' \
		data/$(APP_ID).desktop > ~/.local/share/applications/$(APP_ID).desktop
	@echo "Desktop entry installed to ~/.local/share/applications/$(APP_ID).desktop"

uninstall-desktop: ## Remove .desktop entry
	rm -f ~/.local/share/applications/$(APP_ID).desktop
	@echo "Desktop entry removed."

lint: ## Run basic Python syntax check on all source files
	$(PYTHON) -m py_compile main.py
	@find pulsedeck -name '*.py' -exec $(PYTHON) -m py_compile {} +
	@echo "All files OK"

clean: ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/
	@echo "Cleaned."
