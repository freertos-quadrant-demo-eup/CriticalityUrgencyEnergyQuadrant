#!/usr/bin/env python3
"""
Fixed script to generate all graphs properly from tables
Ensures all graphs are generated correctly with proper formatting
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec
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
# Figure 12: Task Utilization Chart (FIXED)
# ============================================================================
def plot_task_utilization():
    """From Table: Task Set Characteristics - FIXED VERSION"""
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
    ax1.set_ylim([0, 0.16])
    
    # Add value labels on bars
    for i, (bar, util) in enumerate(zip(bars, utilizations)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                f'{util:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Right: Period vs WCET scatter
    bubble_sizes = [u * 50000 for u in utilizations]
    scatter = ax2.scatter(periods, wcets, s=bubble_sizes, 
                        c=asil_colors, alpha=0.6, edgecolors='black', linewidths=1.5)
    ax2.set_xlabel('Period Ti (ms)', fontweight='bold')
    ax2.set_ylabel('WCET Ci (ms)', fontweight='bold')
    ax2.set_title('(b) Period vs WCET (size = utilization)', fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle=':')
    ax2.set_xlim([0, 550])
    ax2.set_ylim([0, 18])
    
    # Add task labels
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
    plt.savefig('Fig12_Task_Utilization.pdf', bbox_inches='tight', dpi=300)
    plt.savefig('Fig12_Task_Utilization.png', bbox_inches='tight', dpi=300)
    print("✓ Generated Figure 12: Task Utilization Chart")
    plt.close()

# ============================================================================
# Import and run all other graph functions
# ============================================================================
def main():
    """Generate all graphs"""
    print("=" * 70)
    print("Generating All Graphs from Tables")
    print("=" * 70)
    print()
    
    # Import the main graph generation functions
    try:
        from generate_new_graphs_from_tables import (
            plot_frequency_power_voltage,
            plot_power_comparison_bars,
            plot_asil_compliance,
            plot_execution_comparison,
            plot_statistical_analysis,
            plot_energy_threshold,
            plot_scheduler_radar
        )
        
        # Generate all graphs
        plot_frequency_power_voltage()
        plot_task_utilization()  # Use fixed version
        plot_power_comparison_bars()
        plot_asil_compliance()
        plot_execution_comparison()
        plot_statistical_analysis()
        plot_energy_threshold()
        plot_scheduler_radar()
        
        print()
        print("=" * 70)
        print("✓ All graphs generated successfully!")
        print("=" * 70)
        
    except ImportError as e:
        print(f"Error importing functions: {e}")
        print("Running standalone version...")
        plot_task_utilization()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()




