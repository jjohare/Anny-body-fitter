#!/usr/bin/env python3
"""
Bottleneck Analyzer for Anny Body Fitter
Identifies and analyzes performance bottlenecks in the processing pipeline
"""

import torch
import time
import cProfile
import pstats
import io
from pathlib import Path
import sys
from typing import Dict, List, Tuple
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class BottleneckAnalyzer:
    """Analyze and identify performance bottlenecks"""

    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @contextmanager
    def timer(self, operation_name: str):
        """Context manager for timing operations"""
        start = time.perf_counter()
        try:
            yield
        finally:
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            if operation_name not in self.timings:
                self.timings[operation_name] = []
            self.timings[operation_name].append(elapsed)

    def profile_function(self, func, *args, **kwargs):
        """Profile a function with cProfile"""
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()

        # Get stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions

        return result, s.getvalue()

    def analyze_parameter_regressor(self):
        """Detailed analysis of ParametersRegressor bottlenecks"""
        import anny
        from anny.parameters_regressor import ParametersRegressor
        import roma

        print("\n" + "="*80)
        print("PARAMETERS REGRESSOR BOTTLENECK ANALYSIS")
        print("="*80)

        # Load model
        print("\nLoading model...")
        model = anny.create_fullbody_model(
            rig="default",
            eyes=True,
            tongue=False,
            local_changes=True
        )
        model = model.to(self.device)

        # Create target
        print("Creating target mesh...")
        with torch.no_grad():
            output_target = model(
                pose_parameters=None,
                phenotype_kwargs={k: 0.5 for k in model.phenotype_labels},
                local_changes_kwargs={k: 0.0 for k in model.local_change_labels}
            )
        vertices_target = output_target['vertices']

        # Create regressor
        regressor = ParametersRegressor(
            model,
            max_n_iters=5,
            n_points=5000,
            verbose=True
        )

        print("\n" + "-"*80)
        print("Analyzing regression components...")
        print("-"*80)

        # Time each major component
        batch_size = vertices_target.shape[0]

        # 1. Initialization
        with self.timer("Initialization"):
            pose_params, phenotype_kwargs, local_changes_kwargs = \
                regressor._init_pose_macro_local(batch_size, {})

        # 2. Initial forward pass
        with self.timer("Initial Forward Pass"):
            output = model(
                pose_parameters=pose_params,
                phenotype_kwargs=phenotype_kwargs,
                local_changes_kwargs=local_changes_kwargs,
                pose_parameterization='root_relative_world'
            )
        v_ref = output['vertices'][:, regressor.unique_ids]
        b_ref = output['bone_poses']

        # 3. Jacobian computation
        print("\nTiming Jacobian computation...")
        with self.timer("Jacobian Computation"):
            J = regressor._compute_macro_jacobian(
                pose_params,
                local_changes_kwargs,
                regressor.idx,
                phenotype_kwargs
            )
        print(f"Jacobian shape: {J.shape}")

        # 4. Joint-wise registration
        print("\nTiming joint-wise registration...")
        with self.timer("Joint-wise Registration"):
            pose_new, v_hat = regressor._jointwise_registration_to_pose(
                v_ref, vertices_target, b_ref, phenotype_kwargs, local_changes_kwargs
            )

        # 5. Linear solve
        print("\nTiming linear solve...")
        A = J[..., [model.phenotype_labels.index(k) for k in model.phenotype_labels]]
        b = (vertices_target[:, regressor.idx] - v_hat[:, regressor.idx]).reshape(batch_size, -1)
        reg = torch.diag(regressor.reg_weights).to(self.device)[None]

        with self.timer("Linear Solve"):
            delta = torch.linalg.solve(
                A.transpose(2, 1) @ A + reg,
                (A.transpose(2, 1) @ b[:, :, None])[:, :, 0]
            )

        # 6. Full iteration
        print("\nTiming full iteration...")
        with self.timer("Full Iteration"):
            pose_new, v_hat = regressor._jointwise_registration_to_pose(
                v_ref, vertices_target, b_ref, phenotype_kwargs, local_changes_kwargs
            )

            J = regressor._compute_macro_jacobian(
                pose_new, local_changes_kwargs, regressor.idx, phenotype_kwargs
            )
            A = J[..., [model.phenotype_labels.index(k) for k in model.phenotype_labels]]
            b = (vertices_target[:, regressor.idx] - v_hat[:, regressor.idx]).reshape(batch_size, -1)
            delta = torch.linalg.solve(
                A.transpose(2, 1) @ A + reg,
                (A.transpose(2, 1) @ b[:, :, None])[:, :, 0]
            )

        # Print timing breakdown
        self.print_timing_breakdown()

        # Profile full regression
        print("\n" + "="*80)
        print("FULL REGRESSION PROFILING")
        print("="*80)

        def run_regression():
            return regressor(vertices_target, optimize_phenotypes=True)

        _, profile_output = self.profile_function(run_regression)
        print(profile_output)

    def analyze_forward_pass(self):
        """Detailed analysis of model forward pass"""
        import anny
        import roma

        print("\n" + "="*80)
        print("FORWARD PASS BOTTLENECK ANALYSIS")
        print("="*80)

        # Load model
        model = anny.create_fullbody_model()
        model = model.to(self.device)

        # Create inputs
        bones_rotvec = torch.randn((len(model.bone_labels), 3)) * 0.3
        bones_rotmat = roma.rotvec_to_rotmat(bones_rotvec)
        pose_parameters = roma.Rigid(
            bones_rotmat,
            torch.zeros((len(bones_rotmat), 3))
        )[None].to_homogeneous().to(self.device)

        phenotype_kwargs = {k: 0.5 for k in model.phenotype_labels}
        local_changes_kwargs = {k: 0.0 for k in model.local_change_labels}

        def forward_pass():
            with torch.no_grad():
                return model(
                    pose_parameters=pose_parameters,
                    phenotype_kwargs=phenotype_kwargs,
                    local_changes_kwargs=local_changes_kwargs
                )

        # Profile
        _, profile_output = self.profile_function(forward_pass)
        print(profile_output)

    def print_timing_breakdown(self):
        """Print breakdown of timing results"""
        print("\n" + "="*80)
        print("TIMING BREAKDOWN")
        print("="*80)

        total_time = sum(sum(times) for times in self.timings.values())

        # Sort by total time
        sorted_timings = sorted(
            self.timings.items(),
            key=lambda x: sum(x[1]),
            reverse=True
        )

        print(f"{'Operation':<40} {'Total (ms)':<12} {'Avg (ms)':<12} {'%':<8}")
        print("-"*80)

        for operation, times in sorted_timings:
            total = sum(times)
            avg = total / len(times)
            pct = (total / total_time) * 100
            print(f"{operation:<40} {total:>10.2f}  {avg:>10.2f}  {pct:>6.1f}%")

        print("-"*80)
        print(f"{'TOTAL':<40} {total_time:>10.2f}")

    def analyze_memory_usage(self):
        """Analyze memory usage patterns"""
        import anny
        import roma

        print("\n" + "="*80)
        print("MEMORY USAGE ANALYSIS")
        print("="*80)

        if not torch.cuda.is_available():
            print("CUDA not available, skipping GPU memory analysis")
            return

        # Clear cache
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

        # Load model
        initial_mem = torch.cuda.memory_allocated() / 1024 / 1024
        print(f"\nInitial GPU memory: {initial_mem:.2f} MB")

        model = anny.create_fullbody_model()
        model = model.to(self.device)

        model_mem = torch.cuda.memory_allocated() / 1024 / 1024
        print(f"After model load: {model_mem:.2f} MB (+{model_mem - initial_mem:.2f} MB)")

        # Forward pass
        bones_rotvec = torch.randn((len(model.bone_labels), 3)) * 0.3
        bones_rotmat = roma.rotvec_to_rotmat(bones_rotvec)
        pose_parameters = roma.Rigid(
            bones_rotmat,
            torch.zeros((len(bones_rotmat), 3))
        )[None].to_homogeneous().to(self.device)

        with torch.no_grad():
            output = model(
                pose_parameters=pose_parameters,
                phenotype_kwargs={k: 0.5 for k in model.phenotype_labels},
                local_changes_kwargs={k: 0.0 for k in model.local_change_labels}
            )

        forward_mem = torch.cuda.memory_allocated() / 1024 / 1024
        print(f"After forward pass: {forward_mem:.2f} MB (+{forward_mem - model_mem:.2f} MB)")

        # Peak memory
        peak_mem = torch.cuda.max_memory_allocated() / 1024 / 1024
        print(f"\nPeak GPU memory: {peak_mem:.2f} MB")

        # Batch processing
        batch_sizes = [1, 2, 4, 8]
        print("\n" + "-"*80)
        print("Memory usage by batch size:")
        print("-"*80)

        for bs in batch_sizes:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

            pose_params_batch = pose_parameters.repeat(bs, 1, 1, 1)
            phenotype_batch = {k: torch.full((bs,), 0.5) for k in model.phenotype_labels}
            local_batch = {k: torch.zeros(bs) for k in model.local_change_labels}

            with torch.no_grad():
                output = model(
                    pose_parameters=pose_params_batch,
                    phenotype_kwargs=phenotype_batch,
                    local_changes_kwargs=local_batch
                )

            batch_mem = torch.cuda.max_memory_allocated() / 1024 / 1024
            per_sample = batch_mem / bs
            print(f"Batch size {bs}: {batch_mem:.2f} MB total, {per_sample:.2f} MB per sample")


def main():
    """Run all bottleneck analyses"""
    analyzer = BottleneckAnalyzer()

    # Run analyses
    analyzer.analyze_forward_pass()
    analyzer.analyze_parameter_regressor()
    analyzer.analyze_memory_usage()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
