# FreeRTOS Energy-Urgency-Priority (EUP) Scheduler Demo

Reference implementation of the **Energy-Urgency-Priority (EUP)** scheduling framework for battery-aware real-time control in Electric Vehicle ECUs, implemented on the **FreeRTOS POSIX (Linux) port**.

## Associated Publication

> **Azad Mohammed Shaik**, *"Energy-Urgency-Priority Scheduling Framework: Battery-Aware Real-Time Control for Electric Vehicle ECUs,"* International Conference on Emerging Trends in Engineering, Computing and Business Excellence (IC-ECBE 2026), March 2026.

## Overview

EUP extends fixed-priority RTOS scheduling with battery State-of-Charge (SoC) awareness and Dynamic Voltage and Frequency Scaling (DVFS):
- Tracks real-time battery SoC depletion across Normal, Moderate, Critical, and Emergency energy states
- Classifies tasks dynamically across 3D Energy-Urgency-Priority octants (Q1–Q8)
- Scales operating frequency for lower-criticality tasks while preserving **zero deadline violations for ASIL-D safety-critical tasks**

## Repository Structure

- `src/freertos_quadrant_demo_eup.c` — FreeRTOS POSIX implementation of the EUP scheduler and RMS baseline toggle (`USE_EUP_SCHEDULER`)
- `src/FreeRTOSConfig_linux.h` & `src/FreeRTOSConfig.h` — FreeRTOS POSIX configuration
- `run_eup.sh` — 30-second demonstration runner
- `generate_graphs.py`, `generate_new_graphs_from_tables.py`, `fix_and_generate_all_graphs.py` — Matplotlib plotting scripts for paper figures
- `Makefile` — Build automation including FreeRTOS-Kernel fetch

## Quick Start (Linux / WSL)

### Prerequisites
- `gcc`, `make`, `git`, POSIX `pthread` / `librt`
- Optional (for plotting): Python 3 with `matplotlib`, `numpy`, `pandas`

### Build & Run
```bash
# 1. Fetch FreeRTOS-Kernel V11.1.0
make fetch-freertos

# 2. Build the EUP demo
make eup

# 3. Run the 30-second demo
chmod +x run_eup.sh
./run_eup.sh
```

To compare against the baseline RMS scheduler, set `#define USE_EUP_SCHEDULER 0` in `src/freertos_quadrant_demo_eup.c`, then run `make clean && make eup && ./run_eup.sh`.

## Citation

```bibtex
@inproceedings{shaik2026eup,
  author    = {Shaik, Azad Mohammed},
  title     = {Energy-Urgency-Priority Scheduling Framework: Battery-Aware Real-Time Control for Electric Vehicle ECUs},
  booktitle = {Proceedings of the International Conference on Emerging Trends in Engineering, Computing and Business Excellence (IC-ECBE 2026)},
  year      = {2026},
  month     = {March}
}
```

## License

This project is released under the [MIT License](LICENSE). FreeRTOS-Kernel is fetched separately under its upstream MIT license.
