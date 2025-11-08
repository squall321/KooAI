#!/bin/bash
"""
Load Testing Runner Script

Convenience script for running different load test scenarios.
"""

set -e

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
HOST="${KOOAI_HOST:-http://localhost:8000}"
USERS=10
SPAWN_RATE=2
RUN_TIME="1m"
SCENARIO="mixed"

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --host HOST          Target host (default: http://localhost:8000)"
    echo "  -u, --users USERS        Number of concurrent users (default: 10)"
    echo "  -r, --spawn-rate RATE    Spawn rate (default: 2)"
    echo "  -t, --time TIME          Run time (default: 1m)"
    echo "  -s, --scenario SCENARIO  Test scenario (default: mixed)"
    echo "      --help               Show this help message"
    echo
    echo "Scenarios:"
    echo "  baseline    - Quick baseline test (10 users, 30s)"
    echo "  smoke       - Smoke test (5 users, 1m)"
    echo "  load        - Load test (50 users, 5m)"
    echo "  stress      - Stress test (100 users, 10m)"
    echo "  spike       - Spike test (200 users, 2m)"
    echo "  endurance   - Endurance test (30 users, 30m)"
    echo "  mixed       - Mixed workload (custom)"
    echo
    echo "Examples:"
    echo "  $0 --scenario smoke"
    echo "  $0 --users 100 --time 5m"
    echo "  $0 --host https://api.kooai.com --scenario stress"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -s|--scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Set scenario parameters
case $SCENARIO in
    baseline)
        USERS=10
        SPAWN_RATE=5
        RUN_TIME="30s"
        echo -e "${GREEN}Running baseline test...${NC}"
        ;;
    smoke)
        USERS=5
        SPAWN_RATE=1
        RUN_TIME="1m"
        echo -e "${GREEN}Running smoke test...${NC}"
        ;;
    load)
        USERS=50
        SPAWN_RATE=5
        RUN_TIME="5m"
        echo -e "${YELLOW}Running load test...${NC}"
        ;;
    stress)
        USERS=100
        SPAWN_RATE=10
        RUN_TIME="10m"
        echo -e "${RED}Running stress test...${NC}"
        ;;
    spike)
        USERS=200
        SPAWN_RATE=50
        RUN_TIME="2m"
        echo -e "${RED}Running spike test...${NC}"
        ;;
    endurance)
        USERS=30
        SPAWN_RATE=3
        RUN_TIME="30m"
        echo -e "${YELLOW}Running endurance test...${NC}"
        ;;
    mixed)
        echo -e "${GREEN}Running mixed workload test...${NC}"
        ;;
    *)
        echo -e "${RED}Unknown scenario: $SCENARIO${NC}"
        usage
        ;;
esac

# Print test parameters
echo
echo "=================================="
echo "  Load Test Configuration"
echo "=================================="
echo "Host:        $HOST"
echo "Users:       $USERS"
echo "Spawn Rate:  $SPAWN_RATE"
echo "Run Time:    $RUN_TIME"
echo "Scenario:    $SCENARIO"
echo "=================================="
echo

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${RED}Error: locust is not installed${NC}"
    echo "Install with: pip install locust"
    exit 1
fi

# Run locust
LOCUST_FILE="tests/load/locustfile.py"

if [ ! -f "$LOCUST_FILE" ]; then
    echo -e "${RED}Error: locustfile not found at $LOCUST_FILE${NC}"
    exit 1
fi

# Create results directory
RESULTS_DIR="load_test_results"
mkdir -p "$RESULTS_DIR"

# Timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/results_${SCENARIO}_${TIMESTAMP}.html"

echo -e "${GREEN}Running locust...${NC}"
echo "Results will be saved to: $RESULTS_FILE"
echo

# Run locust
locust \
    -f "$LOCUST_FILE" \
    --host="$HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --headless \
    --html="$RESULTS_FILE" \
    --csv="$RESULTS_DIR/stats_${SCENARIO}_${TIMESTAMP}"

echo
echo -e "${GREEN}Load test complete!${NC}"
echo "Results saved to: $RESULTS_FILE"
echo

# Print summary
if [ -f "$RESULTS_DIR/stats_${SCENARIO}_${TIMESTAMP}_stats.csv" ]; then
    echo "=================================="
    echo "  Quick Summary"
    echo "=================================="
    tail -n 1 "$RESULTS_DIR/stats_${SCENARIO}_${TIMESTAMP}_stats.csv" | \
        awk -F',' '{print "Total Requests: "$3"\nFailures: "$4"\nAvg Response: "$5"ms\nRPS: "$11}'
fi
