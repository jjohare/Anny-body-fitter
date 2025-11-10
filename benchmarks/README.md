# Anny Body Fitter - Performance Benchmarks

This directory contains comprehensive performance benchmarking and bottleneck analysis tools for the Anny Body Fitter photo-to-3D-model pipeline.

## Quick Start

```bash
# Run all benchmarks
./run_all_benchmarks.sh

# Or run individually
python performance_profiler.py
python bottleneck_analyzer.py
```

## Benchmark Scripts

### 1. `performance_profiler.py`
Comprehensive performance profiler that measures:
- Model loading time
- Forward pass latency (single and batch)
- Parameter regression performance
- Mesh export speed
- Memory usage (CPU and GPU)
- CPU utilization

**Output:**
- `benchmark_results.json` - Structured results
- `benchmark_summary.txt` - Human-readable summary

**Example usage:**
```bash
python performance_profiler.py
```

### 2. `bottleneck_analyzer.py`
Detailed bottleneck analysis using cProfile and manual timing:
- Forward pass breakdown
- Parameter regression component analysis
- Jacobian computation profiling
- Joint-wise registration timing
- Memory usage patterns by batch size

**Example usage:**
```bash
python bottleneck_analyzer.py
```

### 3. `run_all_benchmarks.sh`
Automated benchmark suite that:
- Runs all benchmark scripts
- Generates timestamped reports
- Creates summary documentation
- Stores results in organized directories

**Example usage:**
```bash
./run_all_benchmarks.sh
```

## Performance Goals

The benchmarks evaluate performance against these targets:

| Metric | Target | Current Status |
|--------|--------|----------------|
| Photo processing | < 5s per image | ✅ Achievable |
| Model fitting | < 10s single subject | ⚠️ 5-8s (optimization needed) |
| API response time | < 100ms non-processing | ⚠️ Requires async queue |
| Concurrent users | 10+ supported | ❌ Requires infrastructure |

## Understanding Results

### Benchmark Output

The `benchmark_summary.txt` contains:

```
PERFORMANCE BENCHMARK SUMMARY
====================================
Device: cuda / cpu
Operations by Duration (slowest first):
  Operation                               Avg (ms)  Memory (MB)  CPU %
  Parameter Regression (5 iter, 5k pts)  5234.56   1024.5 / 450.2  85.3
  ...
```

### Key Metrics

- **Avg (ms)**: Average execution time in milliseconds
- **Memory (MB)**: CPU RAM / GPU VRAM usage
- **CPU %**: CPU utilization percentage
- **Std**: Standard deviation (consistency indicator)

### Bottleneck Indicators

🔴 **Critical (>50% of total time):**
- Jacobian computation in parameter regression
- Needs immediate optimization

🟡 **Moderate (10-50% of total time):**
- Joint-wise registration
- Forward pass skinning
- Should optimize for production

🟢 **Minor (<10% of total time):**
- Mesh export
- Initialization
- Acceptable performance

## Interpreting Results

### Good Performance Indicators
✅ **Forward pass < 50ms** - Model inference is fast
✅ **Batch speedup near linear** - Good parallelization
✅ **Low std deviation** - Consistent performance
✅ **CPU usage < 80%** - Room for concurrency

### Performance Issues
❌ **Regression > 10s** - Needs optimization
❌ **High memory usage** - Risk of OOM errors
❌ **CPU usage > 95%** - CPU bottleneck
❌ **High std deviation** - Unstable performance

## Optimization Recommendations

Based on benchmark results, prioritize:

1. **If Jacobian > 500ms per iteration:**
   - Implement batched perturbations
   - Consider analytical gradients
   - Reduce parameter count

2. **If Forward pass > 100ms:**
   - Enable GPU acceleration (warp-lang)
   - Check batch processing
   - Profile skinning operations

3. **If Memory usage high:**
   - Enable model caching
   - Optimize batch sizes
   - Consider model quantization

4. **If API latency high:**
   - Implement async queue (Celery/RQ)
   - Add response caching
   - Enable connection pooling

## Advanced Usage

### Custom Benchmarks

```python
from performance_profiler import PerformanceProfiler

profiler = PerformanceProfiler()

def my_operation():
    # Your code here
    pass

result = profiler.benchmark_operation(
    "My Custom Operation",
    my_operation,
    iterations=20
)

profiler.save_results("custom_results.json")
```

### Memory Profiling

```python
from bottleneck_analyzer import BottleneckAnalyzer

analyzer = BottleneckAnalyzer()
analyzer.analyze_memory_usage()
```

### Component Timing

```python
analyzer = BottleneckAnalyzer()

with analyzer.timer("Custom Component"):
    # Your code here
    pass

analyzer.print_timing_breakdown()
```

## Results Directory Structure

```
benchmarks/
├── results/
│   └── 20251110_143000/
│       ├── README.md              # Summary report
│       ├── benchmark_results.json # Raw data
│       ├── benchmark_summary.txt  # Performance metrics
│       ├── profiler.log           # Full profiler output
│       └── bottleneck.log         # Bottleneck analysis
├── performance_profiler.py
├── bottleneck_analyzer.py
└── run_all_benchmarks.sh
```

## Continuous Monitoring

### Setup Automated Benchmarks

```bash
# Add to CI/CD pipeline
./run_all_benchmarks.sh

# Compare against baseline
python compare_benchmarks.py \
  --baseline results/baseline/benchmark_results.json \
  --current results/latest/benchmark_results.json
```

### Regression Detection

Monitor for performance regressions:
- >10% increase in average time
- >20% increase in P95 latency
- >50% increase in memory usage

## Troubleshooting

### CUDA Out of Memory
```bash
# Reduce batch size or enable model caching
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Slow Benchmarks
```bash
# Reduce iterations for quick tests
python performance_profiler.py --iterations 3
```

### Missing Dependencies
```bash
pip install torch psutil numpy
```

## References

- Performance Report: `../docs/performance-report.md`
- Optimization Guide: `../docs/optimization-guide.md`
- API Documentation: `../docs/api-reference.md`

## Contributing

To add new benchmarks:

1. Create new benchmark script in this directory
2. Follow naming convention: `benchmark_*.py`
3. Use `PerformanceProfiler` or `BottleneckAnalyzer` classes
4. Update `run_all_benchmarks.sh` to include new script
5. Document in this README

## Support

For issues or questions:
- GitHub Issues: [Anny Body Fitter Issues](https://github.com/naver/anny/issues)
- Documentation: [Performance Report](../docs/performance-report.md)
