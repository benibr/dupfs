# Variables
PYTHON = python
PROGRAM = dupfs.py
TESTS = tests.py

# Default target
all: run

# Run the program
run:
	mkdir -p ./primary ./secondary ./mountpoint
	$(PYTHON) $(PROGRAM) --primary ./primary/ --secondary ./secondary/ --mountpoint ./mountpoint/

clean:
	rm -rf ./primary/* ./secondary/* ./mountpoint/*
	rm -rf ./__pycache__/
