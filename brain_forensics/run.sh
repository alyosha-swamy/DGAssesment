#!/bin/bash

# Social Media Forensics Tool Runner

function print_help {
    echo "Social Media Forensics Tool"
    echo ""
    echo "Usage:"
    echo "  ./run.sh analyze <username> [options]    Run forensic analysis on a username"
    echo "  ./run.sh dashboard                       Launch the interactive dashboard"
    echo "  ./run.sh help                            Show this help message"
    echo ""
    echo "Options:"
    echo "  --platform <platform>                    Specify platform (twitter, facebook, instagram, linkedin)"
    echo "  --output <directory>                     Specify output directory for reports"
    echo ""
    echo "Examples:"
    echo "  ./run.sh analyze johndoe                 Analyze user 'johndoe' across all platforms"
    echo "  ./run.sh analyze johndoe --platform twitter  Analyze user on Twitter only"
    echo "  ./run.sh dashboard                       Launch the web dashboard"
}

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Parse command
if [ $# -eq 0 ]; then
    print_help
    exit 0
fi

command=$1
shift

case $command in
    analyze)
        if [ $# -eq 0 ]; then
            echo "Error: Username is required."
            print_help
            exit 1
        fi
        
        username=$1
        shift
        
        echo "Starting forensic analysis for user: $username"
        python3 main.py "$username" "$@"
        ;;
        
    dashboard)
        echo "Launching interactive dashboard..."
        python3 -m visualization.dashboard
        ;;
        
    help)
        print_help
        ;;
        
    *)
        echo "Error: Unknown command '$command'"
        print_help
        exit 1
        ;;
esac 