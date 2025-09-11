#!/bin/bash
# Monitor logs from the BGP Anomaly Detection Lab

echo "📊 BGP Anomaly Detection Lab - Log Monitor"
echo "=========================================="

# Function to show log monitoring options
show_options() {
    echo ""
    echo "Log monitoring options:"
    echo "1.  Monitor all FRR logs (real-time)"
    echo "2.  Monitor BGP logs only"
    echo "3.  Monitor specific device logs"
    echo "4.  Show log file locations"
    echo "5.  Follow specific log file"
    echo "6.  Search for BGP events"
    echo "7.  Search for interface events"
    echo "8.  Search for error messages"
    echo "0.  Exit"
}

# Function to monitor all FRR logs
monitor_all_logs() {
    echo "📡 Monitoring all FRR logs (Ctrl+C to stop)..."
    echo "=============================================="
    find logs -name "*.log" -type f | xargs tail -f
}

# Function to monitor BGP logs only
monitor_bgp_logs() {
    echo "📡 Monitoring BGP logs (Ctrl+C to stop)..."
    echo "=========================================="
    find logs -name "bgpd.log" -type f | xargs tail -f
}

# Function to monitor specific device logs
monitor_device_logs() {
    echo "Available devices:"
    ls logs/ | grep -v fluent-bit
    echo ""
    read -p "Enter device name: " device
    
    if [ -d "logs/$device" ]; then
        echo "📡 Monitoring $device logs (Ctrl+C to stop)..."
        echo "=============================================="
        find logs/$device -name "*.log" -type f | xargs tail -f
    else
        echo "❌ Device $device not found."
    fi
}

# Function to show log file locations
show_log_locations() {
    echo "📁 Log file locations:"
    echo "====================="
    find logs -name "*.log" -type f | sort
}

# Function to follow specific log file
follow_log_file() {
    echo "Available log files:"
    find logs -name "*.log" -type f | sort
    echo ""
    read -p "Enter log file path: " logfile
    
    if [ -f "$logfile" ]; then
        echo "📡 Following $logfile (Ctrl+C to stop)..."
        echo "========================================="
        tail -f "$logfile"
    else
        echo "❌ Log file $logfile not found."
    fi
}

# Function to search for BGP events
search_bgp_events() {
    echo "🔍 Searching for BGP events..."
    echo "============================="
    grep -r "BGP" logs/ --include="*.log" | head -20
    echo ""
    echo "Showing first 20 BGP events. Use 'grep -r \"BGP\" logs/ --include=\"*.log\"' for more."
}

# Function to search for interface events
search_interface_events() {
    echo "🔍 Searching for interface events..."
    echo "==================================="
    grep -r "interface\|Interface" logs/ --include="*.log" | head -20
    echo ""
    echo "Showing first 20 interface events. Use 'grep -r \"interface\\|Interface\" logs/ --include=\"*.log\"' for more."
}

# Function to search for error messages
search_error_messages() {
    echo "🔍 Searching for error messages..."
    echo "================================="
    grep -r -i "error\|fail\|down\|critical" logs/ --include="*.log" | head -20
    echo ""
    echo "Showing first 20 error messages. Use 'grep -r -i \"error\\|fail\\|down\\|critical\" logs/ --include=\"*.log\"' for more."
}

# Main menu
while true; do
    show_options
    echo ""
    read -p "Select option (0-8): " choice
    
    case $choice in
        1)
            monitor_all_logs
            ;;
        2)
            monitor_bgp_logs
            ;;
        3)
            monitor_device_logs
            ;;
        4)
            show_log_locations
            ;;
        5)
            follow_log_file
            ;;
        6)
            search_bgp_events
            ;;
        7)
            search_interface_events
            ;;
        8)
            search_error_messages
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please select 0-8."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
