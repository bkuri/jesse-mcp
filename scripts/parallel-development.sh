#!/bin/bash

# Parallel Development Execution Script
# Launches multiple agents simultaneously for rapid strategy development

set -e

# Configuration
PRD_FILE="$HOME/source/jesse-mcp/strategies/PRD_v1.0.0.md"
STRATEGIES_DIR="$HOME/source/jesse-mcp/strategies"
SHARED_STATE_DIR="$HOME/source/jesse-mcp/shared-state"
LOG_DIR="$HOME/source/jesse-mcp/logs"

# Create necessary directories
mkdir -p "$SHARED_STATE_DIR" "$LOG_DIR"

# Function to launch agent with specific profile
launch_agent() {
    local agent_name="$1"
    local profile="$2" 
    local prompt="$3"
    
    echo "🚀 Launching $agent_name with profile: $profile"
    echo "📝 Prompt: $prompt"
    
    # Launch in background with specific model (agent/temperature not supported in run mode)
    opencode run "$prompt" \
        -m zai-coding-plan/glm-4.5-flash \
        > "$LOG_DIR/${agent_name}_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    
    local pid=$!
    echo "📋 Agent $agent_name started with PID: $pid"
    
    # Store PID for management
    echo "$pid" > "$SHARED_STATE_DIR/${agent_name}.pid"
}

# Function to get temperature for profile
get_temperature_for_profile() {
    local profile="$1"
    case "$profile" in
        "prd_executor") echo "0.2" ;;
        "strategy_explorer") echo "0.8" ;;
        "prd_iterator") echo "0.7" ;;
        "suspension_analyzer") echo "0.3" ;;
        *) echo "0.2" ;;  # default conservative
    esac
}

# Function to monitor all agents
monitor_agents() {
    echo "📊 Monitoring agent progress..."
    
    while true; do
        echo "🔄 $(date): Checking agent status..."
        
        # Check if all agents are still running
        running_agents=0
        for agent_file in "$SHARED_STATE_DIR"/*.pid; do
            if [[ -f "$agent_file" ]]; then
                pid=$(cat "$agent_file")
                if kill -0 "$pid" 2>/dev/null; then
                    ((running_agents++))
                else
                    echo "⚠️ Agent $(basename "$agent_file" .pid) is no longer running"
                    rm "$agent_file"
                fi
            fi
        done
        
        echo "✅ Active agents: $running_agents/3"
        
        # If no agents running, break
        if [[ $running_agents -eq 0 ]]; then
            echo "🏁 All agents completed"
            break
        fi
        
        sleep 30  # Check every 30 seconds
    done
}

# Function to stop all agents
stop_agents() {
    echo "🛑 Stopping all agents..."
    
    for agent_file in "$SHARED_STATE_DIR"/*.pid; do
        if [[ -f "$agent_file" ]]; then
            pid=$(cat "$agent_file")
            echo "🛑 Stopping agent $(basename "$agent_file" .pid) (PID: $pid)"
            kill "$pid" 2>/dev/null
            rm "$agent_file"
        fi
    done
    
    echo "✅ All agents stopped"
}

# Function to show agent status
show_status() {
    echo "📊 Agent Status Report"
    echo "=================="
    
    for agent_file in "$SHARED_STATE_DIR"/*.pid; do
        if [[ -f "$agent_file" ]]; then
            pid=$(cat "$agent_file")
            agent_name=$(basename "$agent_file" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                echo "✅ $agent_name: RUNNING (PID: $pid)"
                
                # Show recent log entries
                if [[ -f "$LOG_DIR/${agent_name}_$(date +%Y%m%d).log" ]]; then
                    echo "📝 Recent logs:"
                    tail -5 "$LOG_DIR/${agent_name}_$(date +%Y%m%d).log" | sed 's/^/   /'
                fi
            else
                echo "❌ $agent_name: STOPPED"
            fi
        else
            echo "⚪ No PID file found"
        fi
    done
    
    echo "=================="
}

# Main execution logic
case "${1:-help}" in
    "start")
        echo "🚀 Starting parallel development session..."
        echo "📋 PRD: $PRD_FILE"
        
        # Launch Agent A: Strategy Development
        launch_agent "agent-a-strategy-dev" "prd_executor" \
            "Execute Agent A section from PRD_v1.0.0.md. Focus on strategy development, optimization, and validation. Follow all specifications exactly. Use strategy_* tools, optimize, and walk_forward. Temperature 0.2 for precise execution."
        
        # Launch Agent B: Backtesting & Analysis  
        launch_agent "agent-b-backtest-analysis" "prd_iterator" \
            "Execute Agent B section from PRD_v1.0.0.md. Focus on comprehensive backtesting, performance analysis, and statistical validation. Use backtest, backtest_batch, analyze_results, correlation_matrix. Temperature 0.7 for analytical iteration."
        
        # Launch Agent C: Risk Management
        launch_agent "agent-c-risk-management" "suspension_analyzer" \
            "Execute Agent C section from PRD_v1.0.0.md. Focus on risk analysis, portfolio optimization, and safety validation. Use monte_carlo_*, risk_report, risk_analyze_portfolio. Temperature 0.3 for conservative analysis."
        
        echo "📊 All agents launched. Monitoring progress..."
        monitor_agents
        ;;
        
    "stop")
        stop_agents
        ;;
        
    "status")
        show_status
        ;;
        
    "help"|*)
        echo "🛠️ Parallel Development Execution Script"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  start    - Launch all agents for parallel development"
        echo "  stop     - Stop all running agents"
        echo "  status   - Show current agent status"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start    # Launch Agent A, B, and C"
        echo "  $0 status   # Check if agents are running"
        echo ""
        echo "Configuration:"
        echo "  PRD: $PRD_FILE"
        echo "  Strategies: $STRATEGIES_DIR"
        echo "  Shared State: $SHARED_STATE_DIR"
        echo "  Logs: $LOG_DIR"
        ;;
esac