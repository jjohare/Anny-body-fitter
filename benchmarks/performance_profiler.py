#!/usr/bin/env python3
"""
Performance Profiler for Anny Body Fitter
Analyzes photo-to-3D-model pipeline performance and identifies bottlenecks
"""

import time
import torch
import psutil
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    operation: str
    duration_ms: float
    memory_mb: float
    gpu_memory_mb: float
    cpu_percent: float
    iterations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_duration_ms: float


class PerformanceProfiler:
    """Profile performance of Anny operations"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.process = psutil.Process()

    def _get_memory_usage(self) -> Tuple[float, float]:
        """Get current memory usage in MB"""
        cpu_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        gpu_mem = 0.0
        if torch.cuda.is_available():
            gpu_mem = torch.cuda.memory_allocated() / 1024 / 1024  # MB
        return cpu_mem, gpu_mem

    def _get_cpu_percent(self) -> float:
        """Get CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)

    def benchmark_operation(
        self,
        operation_name: str,
        operation_func: callable,
        iterations: int = 10,
        warmup_iterations: int = 2
    ) -> BenchmarkResult:
        """
        Benchmark a single operation

        Args:
            operation_name: Name of the operation
            operation_func: Function to benchmark
            iterations: Number of iterations to run
            warmup_iterations: Number of warmup runs

        Returns:
            BenchmarkResult with timing and resource usage
        """
        print(f"\n{'='*60}")
        print(f"Benchmarking: {operation_name}")
        print(f"{'='*60}")

        # Warmup
        for _ in range(warmup_iterations):
            operation_func()

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        # Benchmark
        durations = []
        cpu_percents = []
        mem_usages = []
        gpu_mem_usages = []

        for i in range(iterations):
            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()

            start_time = time.perf_counter()
            operation_func()

            if torch.cuda.is_available():
                torch.cuda.synchronize()

            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000  # Convert to ms

            cpu_mem, gpu_mem = self._get_memory_usage()
            cpu_pct = self._get_cpu_percent()

            durations.append(duration)
            mem_usages.append(cpu_mem)
            gpu_mem_usages.append(gpu_mem)
            cpu_percents.append(cpu_pct)

            print(f"Iteration {i+1}/{iterations}: {duration:.2f}ms | "
                  f"CPU: {cpu_pct:.1f}% | RAM: {cpu_mem:.1f}MB | "
                  f"GPU: {gpu_mem:.1f}MB")

        result = BenchmarkResult(
            operation=operation_name,
            duration_ms=np.mean(durations),
            memory_mb=np.mean(mem_usages),
            gpu_memory_mb=np.mean(gpu_mem_usages),
            cpu_percent=np.mean(cpu_percents),
            iterations=iterations,
            avg_duration_ms=np.mean(durations),
            min_duration_ms=np.min(durations),
            max_duration_ms=np.max(durations),
            std_duration_ms=np.std(durations)
        )

        print(f"\n{operation_name} Results:")
        print(f"  Avg: {result.avg_duration_ms:.2f}ms ± {result.std_duration_ms:.2f}ms")
        print(f"  Min: {result.min_duration_ms:.2f}ms")
        print(f"  Max: {result.max_duration_ms:.2f}ms")
        print(f"  Memory: {result.memory_mb:.1f}MB CPU, {result.gpu_memory_mb:.1f}MB GPU")

        self.results.append(result)
        return result

    def save_results(self, filepath: Path):
        """Save benchmark results to JSON"""
        results_dict = {
            "device": str(self.device),
            "cuda_available": torch.cuda.is_available(),
            "results": [asdict(r) for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"\nResults saved to: {filepath}")

    def generate_summary(self) -> str:
        """Generate human-readable summary of benchmarks"""
        lines = [
            "\n" + "="*80,
            "PERFORMANCE BENCHMARK SUMMARY",
            "="*80,
            f"Device: {self.device}",
            f"CUDA Available: {torch.cuda.is_available()}",
            ""
        ]

        # Sort by duration
        sorted_results = sorted(self.results, key=lambda x: x.avg_duration_ms, reverse=True)

        lines.append("Operations by Duration (slowest first):")
        lines.append("-" * 80)
        lines.append(f"{'Operation':<40} {'Avg (ms)':<12} {'Memory (MB)':<15} {'CPU %':<10}")
        lines.append("-" * 80)

        for r in sorted_results:
            lines.append(
                f"{r.operation:<40} {r.avg_duration_ms:>10.2f}  "
                f"{r.memory_mb:>8.1f} / {r.gpu_memory_mb:>4.1f}  "
                f"{r.cpu_percent:>8.1f}"
            )

        lines.append("")
        lines.append("Bottleneck Analysis:")
        lines.append("-" * 80)

        total_time = sum(r.avg_duration_ms for r in self.results)
        for r in sorted_results[:5]:  # Top 5 bottlenecks
            percentage = (r.avg_duration_ms / total_time) * 100
            lines.append(f"  {r.operation}: {percentage:.1f}% of total time")

        lines.append("\n" + "="*80)

        return "\n".join(lines)


def run_model_benchmarks():
    """Run comprehensive benchmarks on Anny model operations"""
    import anny

    profiler = PerformanceProfiler()

    print("\n" + "="*80)
    print("ANNY BODY FITTER PERFORMANCE BENCHMARKS")
    print("="*80)

    # 1. Model Loading
    def load_fullbody_model():
        return anny.create_fullbody_model(
            rig="default",
            eyes=True,
            tongue=False,
            local_changes=True
        )

    profiler.benchmark_operation(
        "Model Loading (Fullbody)",
        load_fullbody_model,
        iterations=5
    )

    # Load model for subsequent tests
    model = load_fullbody_model()
    model = model.to(profiler.device)

    # 2. Forward Pass (Neutral Pose)
    def forward_pass_neutral():
        with torch.no_grad():
            output = model(
                pose_parameters=None,
                phenotype_kwargs={k: 0.5 for k in model.phenotype_labels},
                local_changes_kwargs={k: 0.0 for k in model.local_change_labels}
            )
        return output

    profiler.benchmark_operation(
        "Forward Pass (Neutral Pose)",
        forward_pass_neutral,
        iterations=20
    )

    # 3. Forward Pass (Random Pose)
    import roma

    def forward_pass_random_pose():
        bones_rotvec = torch.randn((len(model.bone_labels), 3)) * 0.3
        bones_rotmat = roma.rotvec_to_rotmat(bones_rotvec)
        pose_parameters = roma.Rigid(
            bones_rotmat,
            torch.zeros((len(bones_rotmat), 3))
        )[None].to_homogeneous().to(profiler.device)

        with torch.no_grad():
            output = model(
                pose_parameters=pose_parameters,
                phenotype_kwargs={k: 0.5 for k in model.phenotype_labels},
                local_changes_kwargs={k: 0.0 for k in model.local_change_labels}
            )
        return output

    profiler.benchmark_operation(
        "Forward Pass (Random Pose)",
        forward_pass_random_pose,
        iterations=20
    )

    # 4. Batch Processing (Batch Size 4)
    def forward_pass_batch4():
        batch_size = 4
        bones_rotvec = torch.randn((batch_size, len(model.bone_labels), 3)) * 0.3
        bones_rotmat = roma.rotvec_to_rotmat(bones_rotvec)
        pose_parameters = roma.Rigid(
            bones_rotmat,
            torch.zeros((batch_size, len(bones_rotmat[0]), 3))
        ).to_homogeneous().to(profiler.device)

        with torch.no_grad():
            output = model(
                pose_parameters=pose_parameters,
                phenotype_kwargs={k: torch.full((batch_size,), 0.5) for k in model.phenotype_labels},
                local_changes_kwargs={k: torch.zeros(batch_size) for k in model.local_change_labels}
            )
        return output

    profiler.benchmark_operation(
        "Forward Pass (Batch Size 4)",
        forward_pass_batch4,
        iterations=10
    )

    # 5. Parameter Regression (Single Subject)
    from anny.parameters_regressor import ParametersRegressor

    # Create target mesh
    output_target = forward_pass_neutral()
    vertices_target = output_target['vertices'].to(profiler.device)

    def parameter_regression():
        regressor = ParametersRegressor(
            model,
            max_n_iters=3,  # Reduced for benchmarking
            n_points=2000,  # Reduced for benchmarking
            verbose=False
        )
        pose_params, phenotype_kwargs, v_hat = regressor(
            vertices_target,
            optimize_phenotypes=True
        )
        return pose_params, phenotype_kwargs, v_hat

    profiler.benchmark_operation(
        "Parameter Regression (3 iterations)",
        parameter_regression,
        iterations=5
    )

    # 6. Full Parameter Regression (Production Settings)
    def parameter_regression_full():
        regressor = ParametersRegressor(
            model,
            max_n_iters=5,  # Production default
            n_points=5000,  # Production default
            verbose=False
        )
        pose_params, phenotype_kwargs, v_hat = regressor(
            vertices_target,
            optimize_phenotypes=True
        )
        return pose_params, phenotype_kwargs, v_hat

    profiler.benchmark_operation(
        "Parameter Regression (5 iterations, 5k points)",
        parameter_regression_full,
        iterations=3
    )

    # 7. Mesh Export
    def export_mesh():
        output = forward_pass_neutral()
        vertices = output["vertices"].cpu().numpy()
        faces = model.faces.cpu().numpy()
        return vertices, faces

    profiler.benchmark_operation(
        "Mesh Export to NumPy",
        export_mesh,
        iterations=20
    )

    # Save results
    output_dir = Path(__file__).parent
    profiler.save_results(output_dir / "benchmark_results.json")

    # Print summary
    summary = profiler.generate_summary()
    print(summary)

    # Save summary
    with open(output_dir / "benchmark_summary.txt", 'w') as f:
        f.write(summary)

    return profiler


if __name__ == "__main__":
    profiler = run_model_benchmarks()
    print("\nBenchmarks complete!")
