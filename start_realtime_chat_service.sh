#!/bin/bash
# Real-time Chat Log Service Management Script
# Starts the complete PostgreSQL ingestion pipeline

set -e

echo "🚀 Starting Real-time Chat Log Service"
echo "======================================"

# Function to check if PostgreSQL is running
check_postgres() {
    echo "📊 Checking PostgreSQL status..."
    docker exec unified_context_postgres pg_isready -U opsvi -d unified_context
    if [ $? -eq 0 ]; then
        echo "✅ PostgreSQL is ready"
        return 0
    else
        echo "❌ PostgreSQL is not ready"
        return 1
    fi
}

# Function to start PostgreSQL if not running
start_postgres() {
    echo "🐘 Starting PostgreSQL..."
    cd /home/opsvi/master_root
    docker-compose -f docker-compose.postgres.yml up -d

    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if check_postgres; then
            break
        fi
        echo "   Attempt $i/30 - waiting 2 seconds..."
        sleep 2
    done

    if ! check_postgres; then
        echo "❌ Failed to start PostgreSQL after 60 seconds"
        exit 1
    fi
}

# Function to show current ingestion stats
show_stats() {
    echo "📈 Current PostgreSQL ingestion stats:"
    docker exec unified_context_postgres psql -U opsvi -d unified_context -c "
    SELECT
        COUNT(*) as total_items,
        COUNT(DISTINCT session_id) as sessions,
        COUNT(*) FILTER (WHERE entity_type = 'message') as messages,
        COUNT(*) FILTER (WHERE entity_type = 'tool_call') as tool_calls,
        COUNT(DISTINCT file_path) FILTER (WHERE file_path IS NOT NULL) as unique_files,
        MAX(ingested_at) as latest_ingestion
    FROM context_items;"
}

# Function to start the real-time service
start_service() {
    echo "⚡ Starting real-time chat ingestion service..."

    # Run in background mode
    python libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/realtime_ingestion/realtime_chat_service.py \
        --log-level INFO \
        --watch-dirs /home/opsvi/master_root /home/opsvi/.claude/session-exports &

    SERVICE_PID=$!
    echo "🔄 Service started with PID: $SERVICE_PID"

    # Save PID for later management
    echo $SERVICE_PID > /tmp/realtime_chat_service.pid

    echo "📝 Service is now running. Log file: realtime_chat_service.log"
    echo "🛑 To stop the service: kill $SERVICE_PID"
}

# Main execution
main() {
    # Check if PostgreSQL is running, start if needed
    if ! check_postgres; then
        start_postgres
    fi

    # Show current stats
    show_stats

    # Ask user if they want to start the real-time service
    echo ""
    echo "🤔 Would you like to start the real-time ingestion service?"
    echo "   This will monitor files for changes and ingest them automatically."
    read -p "   Start service? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_service

        echo ""
        echo "✅ Real-time chat log service is now running!"
        echo ""
        echo "📍 Monitoring directories:"
        echo "   • /home/opsvi/master_root"
        echo "   • /home/opsvi/.claude/session-exports"
        echo ""
        echo "🌐 Access points:"
        echo "   • PostgreSQL: localhost:5432 (database: unified_context)"
        echo "   • pgAdmin: http://localhost:5433 (admin@opsvi.local / admin)"
        echo "   • Chat Analytics Dashboard: http://localhost:5000"
        echo ""
        echo "📊 Real-time SQL queries you can now run:"
        echo "   • Recent activity: SELECT * FROM context_items WHERE timestamp > NOW() - INTERVAL '1 hour'"
        echo "   • File activity: SELECT file_path, COUNT(*) FROM file_activity GROUP BY file_path"
        echo "   • Session analysis: SELECT session_id, COUNT(*) FROM context_items GROUP BY session_id"
        echo ""
        echo "🔧 Management commands:"
        echo "   • Check service: ps aux | grep realtime_chat_service"
        echo "   • Stop service: kill \$(cat /tmp/realtime_chat_service.pid)"
        echo "   • View logs: tail -f realtime_chat_service.log"

    else
        echo "ℹ️  Service not started. PostgreSQL is ready for manual ingestion."
        echo "   Run the test command to process existing files:"
        echo "   python libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/realtime_ingestion/realtime_chat_service.py --test"
    fi

    echo ""
    echo "🎉 Setup complete! Your chat logs are now flowing into PostgreSQL in real-time."
}

# Run main function
main
