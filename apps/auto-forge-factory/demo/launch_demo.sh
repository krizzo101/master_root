#!/bin/bash

# Auto-Forge Factory - Demonstration Launcher
# This script provides an easy way to launch the complete demonstration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_menu() {
    clear
    print_header "Auto-Forge Factory - Demonstration Launcher"

    echo ""
    echo "Choose a demonstration option:"
    echo ""
    echo "1. 🚀 Complete Automated Demonstration"
    echo "   - Runs the full end-to-end demonstration automatically"
    echo "   - Best for first-time users"
    echo ""
    echo "2. 🔧 Step-by-Step Shell Script"
    echo "   - Interactive shell script with individual steps"
    echo "   - Good for learning and understanding each phase"
    echo ""
    echo "3. 🐍 Python Client Demonstration"
    echo "   - Programmatic demonstration using Python"
    echo "   - Best for developers and API integration"
    echo ""
    echo "4. 🎯 Simple Demonstration"
    echo "   - Simplified demonstration without full implementation"
    echo "   - Works without starting the factory services"
    echo ""
    echo "5. 📚 View Documentation"
    echo "   - Read comprehensive demonstration guides"
    echo ""
    echo "6. 🏭 Start Factory Only"
    echo "   - Just start the Auto-Forge Factory services"
    echo ""
    echo "7. 🛑 Stop Factory"
    echo "   - Stop all Auto-Forge Factory services"
    echo ""
    echo "8. ❓ Help"
    echo "   - Show help and troubleshooting information"
    echo ""
    echo "0. 🚪 Exit"
    echo ""
}

run_complete_demo() {
    print_header "Running Complete Automated Demonstration"
    print_status "This will run the full end-to-end demonstration automatically."
    echo ""

    if [ ! -f "auto_forge_factory/demo/run_demonstration.py" ]; then
        print_error "Demonstration script not found!"
        print_error "Please ensure you're in the correct directory."
        return 1
    fi

    print_status "Starting complete demonstration..."
    echo ""

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        print_error "Please install Python 3 and try again."
        return 1
    fi

    # Run the complete demonstration
    python3 auto_forge_factory/demo/run_demonstration.py
}

run_shell_demo() {
    print_header "Running Step-by-Step Shell Script"
    print_status "This will run the interactive shell script demonstration."
    echo ""

    if [ ! -f "auto_forge_factory/demo/full_demo.sh" ]; then
        print_error "Shell script not found!"
        print_error "Please ensure you're in the correct directory."
        return 1
    fi

    print_status "Starting shell script demonstration..."
    echo ""

    # Make sure the script is executable
    chmod +x auto_forge_factory/demo/full_demo.sh

    # Run the shell script
    ./auto_forge_factory/demo/full_demo.sh
}

run_python_demo() {
    print_header "Running Python Client Demonstration"
    print_status "This will run the Python client demonstration."
    echo ""

    if [ ! -f "auto_forge_factory/demo/end_to_end_demo.py" ]; then
        print_error "Python demo script not found!"
        print_error "Please ensure you're in the correct directory."
        return 1
    fi

    print_status "Starting Python client demonstration..."
    echo ""

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        print_error "Please install Python 3 and try again."
        return 1
    fi

    # Run the Python demo
    python3 auto_forge_factory/demo/end_to_end_demo.py
}

run_simple_demo() {
    print_header "Running Simple Demonstration"
    print_status "This will run the simplified demonstration without requiring the full factory implementation."
    echo ""

    if [ ! -f "auto_forge_factory/demo/simple_demo.py" ]; then
        print_error "Simple demo script not found!"
        print_error "Please ensure you're in the correct directory."
        return 1
    fi

    print_status "Starting simple demonstration..."
    echo ""

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        print_error "Please install Python 3 and try again."
        return 1
    fi

    # Run the simple demo
    python3 auto_forge_factory/demo/simple_demo.py
}

show_documentation() {
    print_header "Documentation"
    echo ""
    echo "Available documentation:"
    echo ""
    echo "📖 Main README: auto_forge_factory/README.md"
    echo "📋 Demo README: auto_forge_factory/demo/README.md"
    echo "🔍 End-to-End Guide: auto_forge_factory/demo/END_TO_END_DEMONSTRATION.md"
    echo "📊 Summary: auto_forge_factory/DEMONSTRATION_SUMMARY.md"
    echo ""

    echo "Which document would you like to view?"
    echo "1. Main README"
    echo "2. Demo README"
    echo "3. End-to-End Guide"
    echo "4. Summary"
    echo "0. Back to main menu"
    echo ""

    read -p "Enter your choice: " doc_choice

    case $doc_choice in
        1)
            if [ -f "auto_forge_factory/README.md" ]; then
                less auto_forge_factory/README.md
            else
                print_error "Main README not found!"
            fi
            ;;
        2)
            if [ -f "auto_forge_factory/demo/README.md" ]; then
                less auto_forge_factory/demo/README.md
            else
                print_error "Demo README not found!"
            fi
            ;;
        3)
            if [ -f "auto_forge_factory/demo/END_TO_END_DEMONSTRATION.md" ]; then
                less auto_forge_factory/demo/END_TO_END_DEMONSTRATION.md
            else
                print_error "End-to-End Guide not found!"
            fi
            ;;
        4)
            if [ -f "auto_forge_factory/DEMONSTRATION_SUMMARY.md" ]; then
                less auto_forge_factory/DEMONSTRATION_SUMMARY.md
            else
                print_error "Summary not found!"
            fi
            ;;
        0)
            return
            ;;
        *)
            print_error "Invalid choice!"
            ;;
    esac
}

start_factory() {
    print_header "Starting Auto-Forge Factory"
    print_status "Starting the Auto-Forge Factory services..."
    echo ""

    if [ ! -f "auto_forge_factory/demo/full_demo.sh" ]; then
        print_error "Shell script not found!"
        print_error "Please ensure you're in the correct directory."
        return 1
    fi

    # Make sure the script is executable
    chmod +x auto_forge_factory/demo/full_demo.sh

    # Start the factory
    ./auto_forge_factory/demo/full_demo.sh --start-only

    echo ""
    print_status "Factory started! You can now:"
    echo "• Visit http://localhost:8000/docs for API documentation"
    echo "• Visit http://localhost:8000/health for health check"
    echo "• Visit http://localhost:3000 for Grafana dashboard (admin/admin)"
    echo ""
}

stop_factory() {
    print_header "Stopping Auto-Forge Factory"
    print_status "Stopping all Auto-Forge Factory services..."
    echo ""

    if [ ! -f "auto_forge_factory/demo/full_demo.sh" ]; then
        print_error "Shell script not found!"
        print_error "Please ensure you're in the correct directory."
        return 1
    fi

    # Make sure the script is executable
    chmod +x auto_forge_factory/demo/full_demo.sh

    # Stop the factory
    ./auto_forge_factory/demo/full_demo.sh --stop-only

    echo ""
    print_status "Factory stopped!"
    echo ""
}

show_help() {
    print_header "Help and Troubleshooting"
    echo ""
    echo "🚀 Auto-Forge Factory Demonstration"
    echo ""
    echo "This demonstration showcases autonomous software development using AI agents."
    echo ""
    echo "📋 Prerequisites:"
    echo "• Docker and Docker Compose"
    echo "• Python 3.11+"
    echo "• jq command-line tool"
    echo "• OpenAI API key (optional for demo)"
    echo ""
    echo "🔧 Common Issues:"
    echo ""
    echo "1. Factory won't start:"
    echo "   • Check Docker is running"
    echo "   • Verify ports 8000, 6379, 5432 are available"
    echo "   • Check Docker Compose installation"
    echo ""
    echo "2. Health check fails:"
    echo "   • Wait for services to fully start (30-60 seconds)"
    echo "   • Check service logs: docker-compose logs"
    echo "   • Verify environment variables"
    echo ""
    echo "3. Job fails to start:"
    echo "   • Check API key configuration"
    echo "   • Verify network connectivity"
    echo "   • Check service health status"
    echo ""
    echo "📚 Documentation:"
    echo "• Main README: auto_forge_factory/README.md"
    echo "• Demo Guide: auto_forge_factory/demo/README.md"
    echo "• API Docs: http://localhost:8000/docs (when running)"
    echo ""
    echo "🌐 Access Points (when running):"
    echo "• API Documentation: http://localhost:8000/docs"
    echo "• Factory Health: http://localhost:8000/health"
    echo "• Factory Status: http://localhost:8000/factory/status"
    echo "• All Jobs: http://localhost:8000/jobs"
    echo "• Prometheus: http://localhost:9090"
    echo "• Grafana: http://localhost:3000 (admin/admin)"
    echo ""

    read -p "Press Enter to continue..."
}

main() {
    while true; do
        show_menu
        read -p "Enter your choice: " choice

        case $choice in
            1)
                run_complete_demo
                ;;
            2)
                run_shell_demo
                ;;
            3)
                run_python_demo
                ;;
            4)
                run_simple_demo
                ;;
            5)
                show_documentation
                ;;
            6)
                start_factory
                ;;
            7)
                stop_factory
                ;;
            8)
                show_help
                ;;
            0)
                print_status "Thank you for using Auto-Forge Factory!"
                echo ""
                echo "🌟 The future of autonomous software development is here."
                exit 0
                ;;
            *)
                print_error "Invalid choice! Please try again."
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
}

# Check if we're in the right directory
if [ ! -d "auto_forge_factory" ]; then
    print_error "Auto-Forge Factory directory not found!"
    print_error "Please run this script from the project root directory."
    exit 1
fi

# Run the main menu
main
