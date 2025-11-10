#!/bin/bash
# Run all performance benchmarks and generate reports

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=================================="
echo "Anny Body Fitter - Benchmark Suite"
echo "=================================="
echo ""

# Check dependencies
echo "Checking dependencies..."
python3 -c "import torch; import anny; import psutil; import numpy" 2>/dev/null || {
    echo "Error: Missing dependencies. Please install requirements."
    exit 1
}

echo "✓ Dependencies OK"
echo ""

# Create output directory
mkdir -p results
OUTPUT_DIR="results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Run performance profiler
echo "=================================="
echo "1. Running Performance Profiler"
echo "=================================="
python3 performance_profiler.py 2>&1 | tee "$OUTPUT_DIR/profiler.log"
cp benchmark_results.json "$OUTPUT_DIR/"
cp benchmark_summary.txt "$OUTPUT_DIR/"
echo ""

# Run bottleneck analyzer
echo "=================================="
echo "2. Running Bottleneck Analyzer"
echo "=================================="
python3 bottleneck_analyzer.py 2>&1 | tee "$OUTPUT_DIR/bottleneck.log"
echo ""

# Generate summary report
echo "=================================="
echo "3. Generating Summary Report"
echo "=================================="

cat > "$OUTPUT_DIR/README.md" << EOF
# Benchmark Results - $(date +%Y-%m-%d)

## System Information
- Date: $(date)
- Python: $(python3 --version)
- PyTorch: $(python3 -c "import torch; print(torch.__version__)")
- CUDA Available: $(python3 -c "import torch; print(torch.cuda.is_available())")
- GPU: $(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>/dev/null || echo "N/A")

## Files

- \`profiler.log\` - Full performance profiler output
- \`bottleneck.log\` - Bottleneck analysis output
- \`benchmark_results.json\` - Structured benchmark data
- \`benchmark_summary.txt\` - Performance summary

## Quick Summary

EOF

# Add quick summary from results
if [ -f benchmark_summary.txt ]; then
    echo '```' >> "$OUTPUT_DIR/README.md"
    tail -n 20 benchmark_summary.txt >> "$OUTPUT_DIR/README.md"
    echo '```' >> "$OUTPUT_DIR/README.md"
fi

echo "✓ Summary report generated"
echo ""

# Print results location
echo "=================================="
echo "Benchmark Complete!"
echo "=================================="
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Key files:"
echo "  - $OUTPUT_DIR/README.md (summary)"
echo "  - $OUTPUT_DIR/benchmark_summary.txt (detailed metrics)"
echo "  - $OUTPUT_DIR/benchmark_results.json (raw data)"
echo ""
echo "To view results:"
echo "  cat $OUTPUT_DIR/benchmark_summary.txt"
echo "  less $OUTPUT_DIR/profiler.log"
echo ""
