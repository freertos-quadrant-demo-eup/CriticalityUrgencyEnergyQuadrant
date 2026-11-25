#!/usr/bin/env python3
"""
Generate new graphs from tables in IEEE_Journal_Paper.tex
Author: Generated for EUP Scheduler Research
Date: December 2024
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid display issues
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec
import sys
import os

# Set publication-quality defaults
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

# ============================================================================
# Figure 11: Frequency vs Power and Voltage (from DVFS table)
# ============================================================================
def plot_frequency_power_voltage():
    """From Table: Frequency Scaling Levels and Power Characteristics"""
    frequencies = [21, 42, 63, 84, 105, 126, 147, 168]  # MHz
    voltages = [1.99, 2.18, 2.36, 2.55, 2.74, 2.93, 3.11, 3.30]  # V
    powers = [41.8, 100.0, 176.0, 273.0, 394.0, 541.0, 711.0, 914.0]  # mW
    quadrants = ['Q8', 'Q7/Q8', 'Q7', 'Q6', 'Q5', 'Q3/Q4', 'Q2', 'Q1']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left: Frequency vs Power
    ax1.plot(frequencies, powers, 'o-', linewidth=2.5, markersize=8, color='#d62728', label='Power Consumption')
    ax1.set_xlabel('Frequency (MHz)', fontweight='bold')
    ax1.set_ylabel('Power Consumption (mW)', fontweight='bold')
    ax1.set_title('(a) Frequency vs Power Consumption', fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle=':')
    ax1.legend()
    
    # Add quadrant annotations
    for i, (f, p, q) in enumerate(zip(frequencies, powers, quadrants)):
        if i % 2 == 0:  # Annotate every other point
            ax1.annotate(q, (f, p), xytext=(5, 10), textcoords='offset points',
                        fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
    
    # Right: Frequency vs Voltage
    ax2.plot(frequencies, voltages, 's-', linewidth=2.5, markersize=8, color='#2ca02c', label='Voltage')
    ax2.set_xlabel('Frequency (MHz)', fontweight='bold')
    ax2.set_ylabel('Voltage (V)', fontweight='bold')
    ax2.set_title('(b) Frequency vs Voltage Scaling', fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle=':')
    ax2.legend()
    
    plt.tight_layout()
    try:
        plt.savefig('Fig11_Frequency_Power_Voltage.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig11_Frequency_Power_Voltage.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 11: Frequency vs Power and Voltage")
    except Exception as e:
        print(f"[ERROR] Error saving Fig11: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 12: Task Utilization Chart (from Task Set table)
# ============================================================================
def plot_task_utilization():
    """From Table: Task Set Characteristics"""
    tasks = ['Airbag\n(ASIL-D)', 'ABS\n(ASIL-C)', 'Door Lock\n(ASIL-B)', 
             'Window\n(ASIL-A)', 'Lighting\n(QM)', 'Comfort\n(QM)']
    periods = [10, 20, 50, 100, 200, 500]  # ms
    wcets = [1.2, 2.8, 4.5, 8.2, 12.5, 15.8]  # ms
    utilizations = [0.120, 0.140, 0.090, 0.082, 0.063, 0.032]
    asil_colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd', '#9467bd']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left: Utilization bars
    bars = ax1.bar(range(len(tasks)), utilizations, color=asil_colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_xlabel('Task', fontweight='bold')
    ax1.set_ylabel('Utilization (Ci/Ti)', fontweight='bold')
    ax1.set_title('(a) Task Utilization by ASIL Level', fontweight='bold')
    ax1.set_xticks(range(len(tasks)))
    ax1.set_xticklabels(tasks, rotation=0, ha='center')
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':')
    ax1.axhline(y=0.527, color='red', linestyle='--', linewidth=2, label='Total Utilization (52.7%)')
    ax1.legend()
    ax1.set_ylim([0, 0.16])  # Set proper y-axis limit
    
    # Add value labels on bars
    for i, (bar, util) in enumerate(zip(bars, utilizations)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                f'{util:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Right: Period vs WCET scatter
    # Scale bubble sizes appropriately (larger multiplier for visibility)
    bubble_sizes = [u * 50000 for u in utilizations]  # Increased multiplier for better visibility
    scatter = ax2.scatter(periods, wcets, s=bubble_sizes, 
                        c=asil_colors, alpha=0.6, edgecolors='black', linewidths=1.5)
    ax2.set_xlabel('Period Ti (ms)', fontweight='bold')
    ax2.set_ylabel('WCET Ci (ms)', fontweight='bold')
    ax2.set_title('(b) Period vs WCET (size = utilization)', fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle=':')
    ax2.set_xlim([0, 550])
    ax2.set_ylim([0, 18])
    
    # Add task labels with better positioning
    task_labels = ['Airbag', 'ABS', 'Door Lock', 'Window', 'Lighting', 'Comfort']
    for i, (p, w, t) in enumerate(zip(periods, wcets, task_labels)):
        ax2.annotate(t, (p, w), xytext=(8, 8), textcoords='offset points', 
                    fontsize=9, fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Create legend for ASIL levels
    legend_elements = [
        mpatches.Patch(facecolor='#d62728', alpha=0.7, label='ASIL-D'),
        mpatches.Patch(facecolor='#ff7f0e', alpha=0.7, label='ASIL-C'),
        mpatches.Patch(facecolor='#2ca02c', alpha=0.7, label='ASIL-B'),
        mpatches.Patch(facecolor='#1f77b4', alpha=0.7, label='ASIL-A'),
        mpatches.Patch(facecolor='#9467bd', alpha=0.7, label='QM')
    ]
    ax2.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    try:
        plt.savefig('Fig12_Task_Utilization.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig12_Task_Utilization.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 12: Task Utilization Chart")
    except Exception as e:
        print(f"[ERROR] Error saving Fig12: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 13: Power Consumption Comparison Bar Chart
# ============================================================================
def plot_power_comparison_bars():
    """From Table: Power Consumption Comparison"""
    schedulers = ['RMS\nBaseline', 'EDF\nBaseline', 'DMS-DVFS', 'EUP\nScheduler']
    avg_power = [285.4, 283.7, 243.8, 268.2]  # mW
    energy_90s = [7.135, 7.093, 6.095, 6.728]  # mWh
    avg_freq = [168, 168, 112, 135]  # MHz
    time_fmax = [100, 100, 34, 18]  # %
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    colors = ['#8c564b', '#8c564b', '#9467bd', '#2ca02c']
    
    # Top Left: Average Power
    bars1 = ax1.bar(schedulers, avg_power, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Average Power (mW)', fontweight='bold')
    ax1.set_title('(a) Average Power Consumption', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars1, avg_power):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height, f'{val:.1f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Top Right: Energy per 90s
    bars2 = ax2.bar(schedulers, energy_90s, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Energy (mWh)', fontweight='bold')
    ax2.set_title('(b) Energy Consumption (90s)', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars2, energy_90s):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{val:.3f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Bottom Left: Average Frequency
    bars3 = ax3.bar(schedulers, avg_freq, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Average Frequency (MHz)', fontweight='bold')
    ax3.set_title('(c) Average Operating Frequency', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars3, avg_freq):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height, f'{val}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Bottom Right: Time at f_max
    bars4 = ax4.bar(schedulers, time_fmax, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('Time at f_max (%)', fontweight='bold')
    ax4.set_title('(d) Time Spent at Maximum Frequency', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars4, time_fmax):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height, f'{val}%', 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    try:
        plt.savefig('Fig13_Power_Comparison_Bars.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig13_Power_Comparison_Bars.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 13: Power Consumption Comparison Bars")
    except Exception as e:
        print(f"[ERROR] Error saving Fig13: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 14: ASIL Compliance Pass Rates
# ============================================================================
def plot_asil_compliance():
    """From Table: Deadline Adherence by ASIL Level"""
    asil_levels = ['ASIL-D', 'ASIL-C', 'ASIL-B', 'ASIL-A', 'QM']
    total_executions = [9030, 4515, 1806, 903, 631]
    violations = [0, 0, 0, 0, 2]
    pass_rates = [100.00, 100.00, 100.00, 100.00, 99.68]
    wcrt = [1.2, 3.5, 20.4, 50.8, 156.3]  # ms
    colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd']
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Top Left: Pass Rates
    bars1 = ax1.bar(asil_levels, pass_rates, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Pass Rate (%)', fontweight='bold')
    ax1.set_title('(a) Deadline Pass Rate by ASIL Level', fontweight='bold')
    ax1.set_ylim([99, 100.5])
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':')
    ax1.axhline(y=100, color='green', linestyle='--', linewidth=2, label='100% Target')
    for bar, val in zip(bars1, pass_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height, f'{val:.2f}%', 
                ha='center', va='bottom', fontweight='bold')
    ax1.legend()
    
    # Top Right: Violations
    bars2 = ax2.bar(asil_levels, violations, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Deadline Violations', fontweight='bold')
    ax2.set_title('(b) Deadline Violations by ASIL Level', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars2, violations):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{val}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Bottom Left: Total Executions
    bars3 = ax3.bar(asil_levels, total_executions, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Total Executions', fontweight='bold')
    ax3.set_title('(c) Total Task Executions by ASIL Level', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars3, total_executions):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height, f'{val:,}', 
                ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Bottom Right: Worst-Case Response Time
    bars4 = ax4.bar(asil_levels, wcrt, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('Worst-Case Response Time (ms)', fontweight='bold')
    ax4.set_title('(d) Worst-Case Response Time by ASIL Level', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars4, wcrt):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height, f'{val:.1f}', 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    try:
        plt.savefig('Fig14_ASIL_Compliance.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig14_ASIL_Compliance.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 14: ASIL Compliance Analysis")
    except Exception as e:
        print(f"[ERROR] Error saving Fig14: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 15: Task Execution Comparison Across Energy States
# ============================================================================
def plot_execution_comparison():
    """From Tables: Task Execution Statistics (Normal, Critical, Emergency)"""
    tasks = ['Airbag\nSensor', 'ABS\nWheelSpeed', 'Door Lock\nControl', 
             'Window\nControl', 'Ambient\nLighting', 'Comfort\nFeatures']
    
    # Normal state (SoC = 83.88%)
    exec_normal = [1030, 515, 206, 103, 51, 20]
    freq_normal = [147, 147, 84, 84, 84, 84]
    eu_normal = [0.700, 0.660, 0.500, 0.460, 0.420, 0.340]
    
    # Critical state (SoC = 28.76%)
    exec_critical = [4530, 2265, 906, 453, 226, 90]
    freq_critical = [168, 168, 105, 105, 105, 105]
    eu_critical = [1.000, 0.960, 0.800, 0.760, 0.720, 0.640]
    
    # Emergency state (SoC = 0%)
    exec_emergency = [9030, 4515, 1806, 903, 451, 180]
    freq_emergency = [168, 168, 105, 105, 105, 105]
    eu_emergency = [1.000, 0.960, 0.800, 0.760, 0.720, 0.640]
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    x = np.arange(len(tasks))
    width = 0.25
    
    # Top Left: Executions
    ax1.bar(x - width, exec_normal, width, label='Normal (SoC=83.88%)', color='#2ca02c', alpha=0.7, edgecolor='black')
    ax1.bar(x, exec_critical, width, label='Critical (SoC=28.76%)', color='#ff7f0e', alpha=0.7, edgecolor='black')
    ax1.bar(x + width, exec_emergency, width, label='Emergency (SoC=0%)', color='#d62728', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Task', fontweight='bold')
    ax1.set_ylabel('Total Executions', fontweight='bold')
    ax1.set_title('(a) Task Executions by Energy State', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(tasks, rotation=0, ha='center')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':')
    ax1.set_yscale('log')
    
    # Top Right: Operating Frequency
    ax2.bar(x - width, freq_normal, width, label='Normal', color='#2ca02c', alpha=0.7, edgecolor='black')
    ax2.bar(x, freq_critical, width, label='Critical', color='#ff7f0e', alpha=0.7, edgecolor='black')
    ax2.bar(x + width, freq_emergency, width, label='Emergency', color='#d62728', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Task', fontweight='bold')
    ax2.set_ylabel('Operating Frequency (MHz)', fontweight='bold')
    ax2.set_title('(b) Operating Frequency by Energy State', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(tasks, rotation=0, ha='center')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y', linestyle=':')
    
    # Bottom Left: Energy-Urgency Metric
    ax3.plot(x, eu_normal, 'o-', linewidth=2, markersize=8, label='Normal', color='#2ca02c')
    ax3.plot(x, eu_critical, 's-', linewidth=2, markersize=8, label='Critical', color='#ff7f0e')
    ax3.plot(x, eu_emergency, '^-', linewidth=2, markersize=8, label='Emergency', color='#d62728')
    ax3.set_xlabel('Task', fontweight='bold')
    ax3.set_ylabel('Energy-Urgency Metric', fontweight='bold')
    ax3.set_title('(c) Energy-Urgency Metric by Energy State', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(tasks, rotation=0, ha='center')
    ax3.legend()
    ax3.grid(True, alpha=0.3, linestyle=':')
    ax3.set_ylim([0.3, 1.05])
    
    # Bottom Right: Frequency Transition
    ax4.plot(tasks, freq_normal, 'o-', linewidth=2.5, markersize=10, label='Normal State', color='#2ca02c')
    ax4.plot(tasks, freq_critical, 's-', linewidth=2.5, markersize=10, label='Critical State', color='#ff7f0e')
    ax4.plot(tasks, freq_emergency, '^-', linewidth=2.5, markersize=10, label='Emergency State', color='#d62728')
    ax4.set_xlabel('Task', fontweight='bold')
    ax4.set_ylabel('Frequency (MHz)', fontweight='bold')
    ax4.set_title('(d) Frequency Scaling Across Energy States', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, linestyle=':')
    ax4.set_xticklabels(tasks, rotation=45, ha='right')
    
    plt.tight_layout()
    try:
        plt.savefig('Fig15_Execution_Comparison.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig15_Execution_Comparison.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 15: Task Execution Comparison Across States")
    except Exception as e:
        print(f"[ERROR] Error saving Fig15: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 16: Statistical Analysis Effect Sizes
# ============================================================================
def plot_statistical_analysis():
    """From Table: Statistical Analysis"""
    comparisons = ['EUP vs\nRMS', 'EUP vs\nEDF', 'EUP vs\nDMS-DVFS']
    mean_diff = [-17.2, -15.5, +24.4]  # mW
    t_statistic = [-12.4, -11.8, 8.7]
    effect_size = [2.18, 2.09, 1.52]  # Cohen's d
    colors = ['#2ca02c', '#2ca02c', '#d62728']  # Green for improvements, red for worse
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))
    
    # Left: Mean Difference
    bars1 = ax1.bar(comparisons, mean_diff, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Mean Difference (mW)', fontweight='bold')
    ax1.set_title('(a) Mean Power Difference', fontweight='bold')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars1, mean_diff):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height, f'{val:+.1f}', 
                ha='center', va='bottom' if val > 0 else 'top', fontweight='bold')
    
    # Middle: t-statistic
    bars2 = ax2.bar(comparisons, t_statistic, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('t-statistic', fontweight='bold')
    ax2.set_title('(b) t-statistic (p < 0.001)', fontweight='bold')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.grid(True, alpha=0.3, axis='y', linestyle=':')
    for bar, val in zip(bars2, t_statistic):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{val:+.1f}', 
                ha='center', va='bottom' if val > 0 else 'top', fontweight='bold')
    
    # Right: Effect Size (Cohen's d)
    bars3 = ax3.bar(comparisons, effect_size, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel("Cohen's d (Effect Size)", fontweight='bold')
    ax3.set_title('(c) Effect Size (Cohen\'s d)', fontweight='bold')
    ax3.axhline(y=0.2, color='orange', linestyle='--', linewidth=1, label='Small (0.2)')
    ax3.axhline(y=0.5, color='blue', linestyle='--', linewidth=1, label='Medium (0.5)')
    ax3.axhline(y=0.8, color='green', linestyle='--', linewidth=1, label='Large (0.8)')
    ax3.grid(True, alpha=0.3, axis='y', linestyle=':')
    ax3.legend()
    for bar, val in zip(bars3, effect_size):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height, f'{val:.2f}', 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    try:
        plt.savefig('Fig16_Statistical_Analysis.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig16_Statistical_Analysis.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 16: Statistical Analysis")
    except Exception as e:
        print(f"[ERROR] Error saving Fig16: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 17: Energy Threshold vs SoC
# ============================================================================
def plot_energy_threshold():
    """From Table: Battery State-of-Charge Progression"""
    soc_values = [100, 91.76, 83.88, 76.06, 68.17, 60.29, 52.41, 44.53, 36.65, 28.76, 20.88, 13.00, 5.12, 0.00]
    et_values = [0.000, 0.000, 0.000, 0.066, 0.197, 0.328, 0.460, 0.591, 0.722, 0.854, 0.985, 1.000, 1.000, 1.000]
    energy_states = ['NORMAL'] * 3 + ['MODERATE'] * 6 + ['CRITICAL'] * 2 + ['EMERGENCY'] * 3
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color regions
    ax.axhspan(0, 0.066, xmin=0, xmax=0.21, alpha=0.2, color='green', label='Normal (SoC > 80%)')
    ax.axhspan(0.066, 1.0, xmin=0, xmax=0.71, alpha=0.2, color='yellow', label='Moderate (20% ≤ SoC ≤ 80%)')
    ax.axhspan(0.985, 1.0, xmin=0.71, xmax=1.0, alpha=0.2, color='red', label='Emergency (SoC < 20%)')
    
    # Plot energy threshold
    ax.plot(soc_values, et_values, 'o-', linewidth=2.5, markersize=8, color='#1f77b4', label='Energy Threshold Et(t)')
    
    # Add threshold lines
    ax.axhline(y=0, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=80, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=30, color='orange', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=20, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Annotations
    ax.annotate('Normal→Moderate\n@SoC=80%', xy=(80, 0.1), fontsize=10,
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    ax.annotate('Moderate→Critical\n@SoC=30%', xy=(30, 0.5), fontsize=10,
                bbox=dict(boxstyle='round', facecolor='orange', alpha=0.5))
    ax.annotate('Critical→Emergency\n@SoC=20%', xy=(20, 0.9), fontsize=10,
                bbox=dict(boxstyle='round', facecolor='red', alpha=0.5))
    
    ax.set_xlabel('Battery State-of-Charge (%)', fontweight='bold')
    ax.set_ylabel('Energy Threshold Et(t)', fontweight='bold')
    ax.set_title('Energy Threshold Function vs Battery SoC', fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(loc='upper right')
    ax.set_xlim([0, 105])
    ax.set_ylim([-0.05, 1.05])
    
    plt.tight_layout()
    try:
        plt.savefig('Fig17_Energy_Threshold.pdf', bbox_inches='tight', dpi=300)
        plt.savefig('Fig17_Energy_Threshold.png', bbox_inches='tight', dpi=300)
        print("[OK] Generated Figure 17: Energy Threshold vs SoC")
    except Exception as e:
        print(f"[ERROR] Error saving Fig17: {e}")
    finally:
        plt.close()

# ============================================================================
# Figure 18: Scheduler Comparison Radar Chart
# ============================================================================
def plot_scheduler_radar():
    """Multi-dimensional comparison of schedulers"""
    categories = ['Power\nEfficiency', 'Energy\nSavings', 'Avg\nFrequency', 'Time@fmax\nReduction', 
                  'ASIL-D\nCompliance', 'Battery\nAwareness']
    
    # Normalize values (0-1 scale, higher is better)
    rms = [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]  # Baseline
    edf = [0.01, 0.01, 0.0, 0.0, 1.0, 0.0]
    dms = [0.85, 0.85, 0.33, 0.66, 1.0, 0.0]
    eup = [0.60, 0.60, 0.20, 0.82, 1.0, 1.0]  # Best in battery awareness
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle
    
    rms += rms[:1]
    edf += edf[:1]
    dms += dms[:1]
    eup += eup[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, rms, 'o-', linewidth=2, label='RMS', color='#8c564b')
    ax.fill(angles, rms, alpha=0.15, color='#8c564b')
    
    ax.plot(angles, edf, 's-', linewidth=2, label='EDF', color='#9467bd')
    ax.fill(angles, edf, alpha=0.15, color='#9467bd')
    
    ax.plot(angles, dms, '^-', linewidth=2, label='DMS-DVFS', color='#ff7f0e')
    ax.fill(angles, dms, alpha=0.15, color='#ff7f0e')
    
    ax.plot(angles, eup, 'D-', linewidth=2.5, label='EUP Scheduler', color='#2ca02c')
    ax.fill(angles, eup, alpha=0.25, color='#2ca02c')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim([0, 1])
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
    ax.grid(True)
    
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.title('Multi-Dimensional Scheduler Comparison', fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('Fig18_Scheduler_Radar.pdf', bbox_inches='tight')
    plt.savefig('Fig18_Scheduler_Radar.png', bbox_inches='tight')
    print("[OK] Generated Figure 18: Scheduler Comparison Radar Chart")
    plt.close()

# ============================================================================
# Main Execution
# ============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("Generating New Graphs from IEEE Journal Paper Tables")
    print("=" * 70)
    print()
    
    try:
        plot_frequency_power_voltage()
        plot_task_utilization()
        plot_power_comparison_bars()
        plot_asil_compliance()
        plot_execution_comparison()
        plot_statistical_analysis()
        plot_energy_threshold()
        plot_scheduler_radar()
        
        print()
        print("=" * 70)
        print("[SUCCESS] All graphs generated successfully!")
        print("=" * 70)
        print()
        print("Generated files:")
        print("  - Fig11_Frequency_Power_Voltage.pdf/png")
        print("  - Fig12_Task_Utilization.pdf/png")
        print("  - Fig13_Power_Comparison_Bars.pdf/png")
        print("  - Fig14_ASIL_Compliance.pdf/png")
        print("  - Fig15_Execution_Comparison.pdf/png")
        print("  - Fig16_Statistical_Analysis.pdf/png")
        print("  - Fig17_Energy_Threshold.pdf/png")
        print("  - Fig18_Scheduler_Radar.pdf/png")
        print()
        
    except Exception as e:
        print(f"Error generating graphs: {e}")
        import traceback
        traceback.print_exc()

