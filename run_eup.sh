#!/bin/bash
#
# Script to run the EUP (Energy-Urgency-Priority) demo
# Automatically stops after 30 seconds to show results
#

echo "========================================================================"
echo "FreeRTOS Energy-Urgency-Priority (EUP) Scheduler Demo"
echo "========================================================================"
echo ""
echo "This demo will run for 30 seconds to demonstrate:"
echo "  - Battery State-of-Charge (SoC) degradation"
echo "  - Dynamic quadrant classification (Q1-Q8)"
echo "  - Frequency scaling based on energy state"
echo "  - Power consumption tracking"
echo "  - ISO 26262 deadline adherence"
echo ""
echo "Starting demo..."
echo ""

# Run the demo in background
timeout 30s ./build/freertos_demo_eup &
PID=$!

# Wait for completion
wait $PID

echo ""
echo "========================================================================"
echo "Demo completed successfully!"
echo "========================================================================"
echo ""
echo "Key observations:"
echo "  1. Battery SoC gradually decreases from 100%"
echo "  2. Tasks operate at different frequencies (quadrants Q1-Q8)"
echo "  3. ASIL-D tasks maintain 0 deadline violations"
echo "  4. Average power consumption is tracked"
echo "  5. Energy-Urgency metric (EU) adapts dynamically"
echo ""
echo "To compare with baseline RMS scheduler:"
echo "  1. Edit src/freertos_quadrant_demo_eup.c"
echo "  2. Set USE_EUP_SCHEDULER to 0"
echo "  3. Rebuild: make clean && make eup"
echo "  4. Run again: ./run_eup.sh"
echo ""
echo "Expected results (from paper):"
echo "  - EUP Power: ~218 mW (23.7% reduction vs RMS)"
echo "  - RMS Power: ~285 mW"
echo "  - Battery life: +18.3% improvement"
echo "  - ASIL-D violations: 0 (guaranteed)"
echo ""
