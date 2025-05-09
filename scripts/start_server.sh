#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting server setup and testing...${NC}\n"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if ! command_exists python; then
    echo -e "${RED}Python is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check for pip
if ! command_exists pip; then
    echo -e "${RED}pip is not installed. Please install pip.${NC}"
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ "$OSTYPE" = "msys" ] || [ "$OSTYPE" = "win32" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt

# Run the test server script
echo -e "${YELLOW}Running server tests...${NC}"
python test_server.py

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Starting server...${NC}"
    
    # Start Celery worker in background if Celery is installed
    if pip show celery >/dev/null 2>&1; then
        echo -e "${YELLOW}Starting Celery worker...${NC}"
        celery -A django_social_login_allauth worker --loglevel=info &
        CELERY_PID=$!
    fi
    
    # Start Django development server
    echo -e "${YELLOW}Starting Django development server...${NC}"
    python manage.py runserver
    
    # If Celery was started, clean up on exit
    if [ -n "$CELERY_PID" ]; then
        trap "kill $CELERY_PID" EXIT
    fi
else
    echo -e "${RED}Server tests failed. Please fix the issues before starting the server.${NC}"
    exit 1
fi 