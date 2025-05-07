#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Running tests for Tipster Arena..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "installed_packages.txt" ]; then
    echo -e "${RED}Installing requirements...${NC}"
    pip install -r requirements.txt
    pip freeze > installed_packages.txt
fi

# Run tests with the new settings module
echo -e "${GREEN}Running tests...${NC}"
DJANGO_SETTINGS_MODULE=tests.config.settings python manage.py test "$@"

echo -e "${GREEN}Tests completed!${NC}" 