/*
 * FreeRTOS Energy-Urgency-Priority (EUP) Scheduler Demonstration
 *
 * Implementation of the three-dimensional Energy-Urgency-Priority framework
 * for battery-aware real-time control in Electric Vehicle ECUs.
 *
 * Based on: "Energy-Urgency-Priority Task Scheduling: A Three-Dimensional
 * Framework for Battery-Aware Real-Time Control in Electric Vehicle ECUs"
 * by Azad Mohammed Shaik, Senior Member, IEEE
 *
 * This implementation adapts the STM32-based algorithm for FreeRTOS POSIX port
 * running on Linux, simulating:
 * - Battery State-of-Charge (SoC) degradation
 * - Dynamic Voltage and Frequency Scaling (DVFS)
 * - Energy-aware task scheduling
 * - ISO 26262 compliance (ASIL-D deadline guarantees)
 *
 * Adapted for Linux POSIX port by: Azad Mohammed Shaik
 * Date: December 22, 2024
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <math.h>
#include <time.h>

#include "FreeRTOSConfig_linux.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "timers.h"

/* ============================================================================
 * EUP FRAMEWORK CONFIGURATION
 * ============================================================================ */

// Enable/disable EUP scheduler (set to 0 for baseline RMS comparison)
#define USE_EUP_SCHEDULER    1

// Weighting coefficients for Energy-Urgency metric (wp + wu + we = 1.0)
#define WEIGHT_PRIORITY      0.4f   // wp
#define WEIGHT_URGENCY       0.3f   // wu
#define WEIGHT_ENERGY        0.3f   // we

// Battery simulation parameters
#define INITIAL_SOC          100.0f  // Initial State of Charge (%)
#define BATTERY_CAPACITY_KWH 75.0f   // Total battery capacity (kWh)
#define ECU_BASE_POWER_MW    50.0f   // Base ECU power consumption (mW)

// Battery drain acceleration for demonstration (multiplier for faster SoC decrease)
#define BATTERY_DRAIN_MULTIPLIER  15000000.0f  // Accelerate drain for demo purposes (~1% per second)

// Frequency scaling levels (simulated for Linux - 8 levels as per STM32)
#define FREQ_LEVEL_0         21      // 0.125 * fmax (21 MHz equivalent)
#define FREQ_LEVEL_1         42      // 0.25 * fmax
#define FREQ_LEVEL_2         63      // 0.375 * fmax
#define FREQ_LEVEL_3         84      // 0.50 * fmax
#define FREQ_LEVEL_4         105     // 0.625 * fmax
#define FREQ_LEVEL_5         126     // 0.75 * fmax
#define FREQ_LEVEL_6         147     // 0.875 * fmax
#define FREQ_LEVEL_7         168     // 1.0 * fmax (maximum)

// Voltage scaling parameters (V = Vmin + (Vmax - Vmin) * f/fmax)
#define VMIN                 1.8f    // Minimum voltage (V)
#define VMAX                 3.3f    // Maximum voltage (V)
#define ACTIVITY_FACTOR      0.15f   // Activity factor for power calculation

// ISO 26262 Safety margins
#define FREQUENCY_FLOOR_ASIL_D  0.5f  // Minimum 50% fmax for ASIL-D tasks

/* ============================================================================
 * TASK ASIL LEVELS (ISO 26262)
 * ============================================================================ */
typedef enum {
    ASIL_QM = 0,    // Quality Management (non-safety)
    ASIL_A,
    ASIL_B,
    ASIL_C,
    ASIL_D          // Highest safety integrity
} ASIL_Level_t;

/* ============================================================================
 * EUP QUADRANT CLASSIFICATION (Table I from paper)
 * ============================================================================ */
typedef enum {
    Q1 = 0,  // Pri=H, Urg=H, Eng=Critical    -> fmax,      No Preempt
    Q2,      // Pri=H, Urg=H, Eng=Normal      -> 0.9*fmax,  Limited Preempt
    Q3,      // Pri=H, Urg=L, Eng=Critical    -> 0.8*fmax,  Yes Preempt
    Q4,      // Pri=H, Urg=L, Eng=Normal      -> 0.7*fmax,  Yes Preempt
    Q5,      // Pri=L, Urg=H, Eng=Critical    -> 0.6*fmax,  Yes Preempt
    Q6,      // Pri=L, Urg=H, Eng=Normal      -> 0.5*fmax,  Yes Preempt
    Q7,      // Pri=L, Urg=L, Eng=Critical    -> 0.4*fmax,  Defer
    Q8       // Pri=L, Urg=L, Eng=Normal      -> 0.3*fmax,  Defer
} EUP_Quadrant_t;

/* ============================================================================
 * AUTOMOTIVE TASK IDENTIFIERS (Body Control Module - BCM)
 * Based on Table II from paper
 * ============================================================================ */
typedef enum {
    TASK_AIRBAG_SENSOR = 0,      // ASIL-D, 10ms,  1.2ms WCET
    TASK_ABS_WHEEL_SPEED,        // ASIL-C, 20ms,  2.8ms WCET
    TASK_DOOR_LOCK_CONTROL,      // ASIL-B, 50ms,  4.5ms WCET
    TASK_WINDOW_CONTROL,         // ASIL-A, 100ms, 8.2ms WCET
    TASK_AMBIENT_LIGHTING,       // QM,     200ms, 12.5ms WCET
    TASK_COMFORT_FEATURES,       // QM,     500ms, 15.8ms WCET
    NUM_TASKS
} TaskID_t;

/* ============================================================================
 * TASK PARAMETERS STRUCTURE
 * ============================================================================ */
typedef struct {
    char taskName[32];
    TaskID_t taskID;
    ASIL_Level_t asilLevel;
    TickType_t period;           // Ti (period)
    TickType_t deadline;         // Di (relative deadline)
    uint32_t wcetMs;             // Ci (WCET at fmax in ms)
    UBaseType_t staticPriority;  // Pi (base priority)
    float energyPerExec;         // Ei (energy per execution in µJ)

    // Runtime statistics
    uint32_t executionCount;
    uint32_t missedDeadlines;
    uint32_t totalExecutionTime;
    uint32_t maxExecutionTime;
    TickType_t lastExecutionTime;

    // EUP metrics
    float normalizedPriority;    // 0-1 scale
    float timeUrgency;           // Ui(t)
    float energyThreshold;       // Et(t)
    float energyUrgencyMetric;   // EUi(t)
    EUP_Quadrant_t currentQuadrant;
    uint32_t currentFrequency;
} TaskParams_t;

/* ============================================================================
 * BATTERY STATE STRUCTURE
 * ============================================================================ */
typedef struct {
    float soc;                    // State of Charge (%)
    float voltage;                // Battery voltage (V)
    float current;                // Discharge current (A)
    float temperature;            // Temperature (°C)
    uint32_t cycleCount;          // Number of charge/discharge cycles
    TickType_t lastUpdateTime;
} BatteryState_t;

/* ============================================================================
 * FREQUENCY SCALING STRUCTURE
 * ============================================================================ */
typedef struct {
    uint32_t frequencyMHz;
    float frequencyRatio;         // f / fmax
    float voltage;                // Operating voltage
    float powerFactor;            // Relative power consumption
} FrequencyLevel_t;

/* ============================================================================
 * GLOBAL VARIABLES
 * ============================================================================ */

// Task parameters (initialized based on Table II)
TaskParams_t taskParams[NUM_TASKS];
TaskHandle_t taskHandles[NUM_TASKS];

// Battery state
BatteryState_t battery;
SemaphoreHandle_t batterySemaphore;

// Frequency levels
FrequencyLevel_t frequencyLevels[8];
uint32_t currentSystemFrequency = FREQ_LEVEL_7;

// Statistics mutex
SemaphoreHandle_t statsMutex;

// System control
volatile int keepRunning = 1;

// Power consumption tracking
float totalEnergyConsumed = 0.0f;  // mWh
uint32_t powerMeasurementCount = 0;
float avgPowerConsumption = 0.0f;  // mW

/* ============================================================================
 * SIGNAL HANDLER
 * ============================================================================ */
void sigintHandler(int sig_num) {
    (void)sig_num;
    printf("\n\n[SHUTDOWN] Received Ctrl+C. Shutting down gracefully...\n");
    keepRunning = 0;
}

/* ============================================================================
 * UTILITY FUNCTIONS
 * ============================================================================ */

// Calculate voltage for a given frequency
float calculateVoltage(float freqRatio) {
    return VMIN + (VMAX - VMIN) * freqRatio;
}

// Calculate power consumption: P(f) = Pstatic + Ca * V^2 * f
float calculatePower(float freqMHz, float voltage) {
    float Pstatic = ECU_BASE_POWER_MW * 0.3f;  // 30% static power
    float Pdynamic = ACTIVITY_FACTOR * voltage * voltage * freqMHz;
    return Pstatic + Pdynamic;
}

// Initialize frequency levels
void initializeFrequencyLevels() {
    uint32_t frequencies[] = {
        FREQ_LEVEL_0, FREQ_LEVEL_1, FREQ_LEVEL_2, FREQ_LEVEL_3,
        FREQ_LEVEL_4, FREQ_LEVEL_5, FREQ_LEVEL_6, FREQ_LEVEL_7
    };

    for (int i = 0; i < 8; i++) {
        frequencyLevels[i].frequencyMHz = frequencies[i];
        frequencyLevels[i].frequencyRatio = (float)frequencies[i] / (float)FREQ_LEVEL_7;
        frequencyLevels[i].voltage = calculateVoltage(frequencyLevels[i].frequencyRatio);
        frequencyLevels[i].powerFactor = calculatePower(
            frequencyLevels[i].frequencyMHz,
            frequencyLevels[i].voltage
        ) / calculatePower(FREQ_LEVEL_7, VMAX);
    }

    printf("[EUP] Initialized %d frequency levels (%.1f MHz to %.1f MHz)\n",
           8, (float)FREQ_LEVEL_0, (float)FREQ_LEVEL_7);
}

/* ============================================================================
 * BATTERY SIMULATION
 * ============================================================================ */

// Initialize battery state
void initializeBattery() {
    xSemaphoreTake(batterySemaphore, portMAX_DELAY);
    battery.soc = INITIAL_SOC;
    battery.voltage = 400.0f;  // Typical EV battery voltage
    battery.current = 0.0f;
    battery.temperature = 25.0f;
    battery.cycleCount = 0;
    battery.lastUpdateTime = xTaskGetTickCount();
    xSemaphoreGive(batterySemaphore);

    printf("[BATTERY] Initialized: SoC=%.1f%%, Voltage=%.1fV, Capacity=%.1f kWh\n",
           battery.soc, battery.voltage, BATTERY_CAPACITY_KWH);
}

// Update battery SoC based on power consumption
void updateBatteryState(float powerMw, uint32_t durationMs) {
    xSemaphoreTake(batterySemaphore, portMAX_DELAY);

    // Energy consumed in mWh (accelerated for demonstration)
    float energyMwh = (powerMw * durationMs) / 3600000.0f;

    // Apply drain multiplier for faster demonstration of battery states
    energyMwh *= BATTERY_DRAIN_MULTIPLIER;

    // Update SoC
    float batteryCapacityMwh = BATTERY_CAPACITY_KWH * 1000000.0f;
    float socDelta = (energyMwh / batteryCapacityMwh) * 100.0f;
    battery.soc -= socDelta;

    if (battery.soc < 0.0f) battery.soc = 0.0f;

    // Update discharge current (simplified)
    battery.current = (powerMw / 1000.0f) / battery.voltage;

    battery.lastUpdateTime = xTaskGetTickCount();

    xSemaphoreGive(batterySemaphore);
}

// Calculate Energy Threshold function (Equation 4 from paper)
float calculateEnergyThreshold(float soc) {
    if (soc > 80.0f) {
        return 0.0f;  // Normal state
    } else if (soc >= 20.0f) {
        return (80.0f - soc) / 60.0f;  // Linear interpolation
    } else {
        return 1.0f;  // Critical state
    }
}

/* ============================================================================
 * EUP SCHEDULER IMPLEMENTATION
 * ============================================================================ */

// Calculate Energy-Urgency metric (Equation 3 from paper)
float calculateEnergyUrgency(TaskParams_t* task) {
    float EU = WEIGHT_PRIORITY * task->normalizedPriority +
               WEIGHT_URGENCY * task->timeUrgency +
               WEIGHT_ENERGY * task->energyThreshold;
    return EU;
}

// Classify task into EUP quadrant (Table I from paper)
EUP_Quadrant_t classifyQuadrant(TaskParams_t* task, float soc) {
    // Determine priority level (High = ASIL-C/D, Low = QM/A/B)
    int highPriority = (task->asilLevel >= ASIL_C);

    // Determine urgency (High = slack < 20% of deadline)
    int highUrgency = (task->timeUrgency > 0.8f);

    // Determine energy state (Critical = SoC < 30%)
    int criticalEnergy = (soc < 30.0f);

    // 3D classification into 8 quadrants
    if (highPriority && highUrgency && criticalEnergy) return Q1;
    if (highPriority && highUrgency && !criticalEnergy) return Q2;
    if (highPriority && !highUrgency && criticalEnergy) return Q3;
    if (highPriority && !highUrgency && !criticalEnergy) return Q4;
    if (!highPriority && highUrgency && criticalEnergy) return Q5;
    if (!highPriority && highUrgency && !criticalEnergy) return Q6;
    if (!highPriority && !highUrgency && criticalEnergy) return Q7;
    return Q8;  // Low priority, low urgency, normal energy
}

// Get frequency for quadrant (Table I from paper)
uint32_t getQuadrantFrequency(EUP_Quadrant_t quadrant, ASIL_Level_t asil) {
    // Apply ISO 26262 safety floor for ASIL-D
    float minRatio = (asil == ASIL_D) ? FREQUENCY_FLOOR_ASIL_D : 0.3f;

    float targetRatio;
    switch (quadrant) {
        case Q1: targetRatio = 1.0f; break;   // fmax
        case Q2: targetRatio = 0.9f; break;
        case Q3: targetRatio = 0.8f; break;
        case Q4: targetRatio = 0.7f; break;
        case Q5: targetRatio = 0.6f; break;
        case Q6: targetRatio = 0.5f; break;
        case Q7: targetRatio = 0.4f; break;
        case Q8: targetRatio = 0.3f; break;
        default: targetRatio = 1.0f;
    }

    if (targetRatio < minRatio) targetRatio = minRatio;

    // Find closest frequency level
    uint32_t targetFreq = (uint32_t)(targetRatio * FREQ_LEVEL_7);
    uint32_t closestFreq = FREQ_LEVEL_7;
    uint32_t minDiff = 1000;

    for (int i = 0; i < 8; i++) {
        uint32_t diff = abs((int)targetFreq - (int)frequencyLevels[i].frequencyMHz);
        if (diff < minDiff) {
            minDiff = diff;
            closestFreq = frequencyLevels[i].frequencyMHz;
        }
    }

    return closestFreq;
}

// Update task EUP metrics
void updateTaskEUPMetrics(TaskParams_t* task, float soc) {
    // Update energy threshold
    task->energyThreshold = calculateEnergyThreshold(soc);

    // Calculate Energy-Urgency metric
    task->energyUrgencyMetric = calculateEnergyUrgency(task);

    // Classify into quadrant
    task->currentQuadrant = classifyQuadrant(task, soc);

    // Get operating frequency
    task->currentFrequency = getQuadrantFrequency(task->currentQuadrant, task->asilLevel);
}

/* ============================================================================
 * TASK IMPLEMENTATION
 * ============================================================================ */

void burnCPU(uint32_t iterations) {
    volatile double result = 0.0;
    for (uint32_t i = 0; i < iterations; i++) {
        result += sqrt((double)i) * 0.001;
    }
}

void simulateWork(uint32_t wcetMs, uint32_t frequency) {
    // Scale execution time based on frequency
    float scaleFactor = (float)FREQ_LEVEL_7 / (float)frequency;
    uint32_t actualTimeMs = (uint32_t)(wcetMs * scaleFactor);

    // Burn CPU for realistic load
    uint32_t iterations = actualTimeMs * 50000;
    burnCPU(iterations);

    // Sleep for remaining time
    vTaskDelay(pdMS_TO_TICKS(actualTimeMs / 2));
}

void GenericTask(void* pvParameters) {
    TaskID_t taskID = *((TaskID_t*)pvParameters);
    TaskParams_t* task = &taskParams[taskID];

    TickType_t xLastWakeTime = xTaskGetTickCount();

    printf("[INIT] %-25s | ASIL-%c | Period=%lums | WCET=%lums | Pri=%lu\n",
           task->taskName,
           task->asilLevel == ASIL_QM ? 'Q' :
           task->asilLevel == ASIL_A ? 'A' :
           task->asilLevel == ASIL_B ? 'B' :
           task->asilLevel == ASIL_C ? 'C' : 'D',
           task->period * portTICK_PERIOD_MS,
           (unsigned long)task->wcetMs,
           task->staticPriority);

    while (keepRunning) {
        TickType_t startTime = xTaskGetTickCount();

        // Get current battery SoC
        float currentSoc;
        xSemaphoreTake(batterySemaphore, portMAX_DELAY);
        currentSoc = battery.soc;
        xSemaphoreGive(batterySemaphore);

        if (USE_EUP_SCHEDULER) {
            // Calculate time urgency
            TickType_t timeToDeadline = task->deadline;
            TickType_t elapsedTime = startTime - task->lastExecutionTime;
            if (elapsedTime < timeToDeadline) {
                task->timeUrgency = (float)(timeToDeadline - elapsedTime) / (float)timeToDeadline;
                task->timeUrgency = 1.0f - task->timeUrgency; // Invert so higher = more urgent
            } else {
                task->timeUrgency = 1.0f;
            }

            // Update EUP metrics
            updateTaskEUPMetrics(task, currentSoc);

            // Execute at quadrant-specific frequency
            simulateWork(task->wcetMs, task->currentFrequency);

            // Calculate power consumption
            int freqIndex = 0;
            for (int i = 0; i < 8; i++) {
                if (frequencyLevels[i].frequencyMHz == task->currentFrequency) {
                    freqIndex = i;
                    break;
                }
            }
            float powerMw = calculatePower(task->currentFrequency, frequencyLevels[freqIndex].voltage);

            // Update battery
            TickType_t execTime = xTaskGetTickCount() - startTime;
            uint32_t execMs = execTime * portTICK_PERIOD_MS;
            updateBatteryState(powerMw, execMs);

            // Update energy statistics
            float energyMwh = (powerMw * execMs) / 3600000.0f;
            totalEnergyConsumed += energyMwh;
            powerMeasurementCount++;
            avgPowerConsumption = (totalEnergyConsumed * 3600000.0f) /
                                  (xTaskGetTickCount() * portTICK_PERIOD_MS);

        } else {
            // Baseline RMS: always run at fmax
            simulateWork(task->wcetMs, FREQ_LEVEL_7);

            TickType_t execTime = xTaskGetTickCount() - startTime;
            uint32_t execMs = execTime * portTICK_PERIOD_MS;
            float powerMw = calculatePower(FREQ_LEVEL_7, VMAX);
            updateBatteryState(powerMw, execMs);

            float energyMwh = (powerMw * execMs) / 3600000.0f;
            totalEnergyConsumed += energyMwh;
            powerMeasurementCount++;
            avgPowerConsumption = (totalEnergyConsumed * 3600000.0f) /
                                  (xTaskGetTickCount() * portTICK_PERIOD_MS);
        }

        // Record statistics
        TickType_t executionTime = xTaskGetTickCount() - startTime;
        uint32_t execMs = executionTime * portTICK_PERIOD_MS;

        xSemaphoreTake(statsMutex, portMAX_DELAY);
        task->executionCount++;
        task->totalExecutionTime += execMs;
        task->lastExecutionTime = startTime;
        if (execMs > task->maxExecutionTime) {
            task->maxExecutionTime = execMs;
        }

        // Check deadline
        if (executionTime > task->deadline) {
            task->missedDeadlines++;
            if (task->asilLevel >= ASIL_C) {
                printf("[CRITICAL] %s MISSED DEADLINE! Exec=%lums, Deadline=%lums\n",
                       task->taskName, (unsigned long)execMs,
                       task->deadline * portTICK_PERIOD_MS);
            }
        }
        xSemaphoreGive(statsMutex);

        vTaskDelayUntil(&xLastWakeTime, task->period);
    }

    vTaskDelete(NULL);
}

/* ============================================================================
 * MONITORING TASK
 * ============================================================================ */
void Task_Monitor(void* pvParameters) {
    (void)pvParameters;

    const TickType_t xPeriod = pdMS_TO_TICKS(5000);
    TickType_t xLastWakeTime = xTaskGetTickCount();

    static float lastSoC = 100.0f;
    static int energyStateChangePrinted = 0;

    printf("\n");
    printf("========================================\n");
    printf("EUP SCHEDULER MONITORING STARTED\n");
    printf("Mode: %s\n", USE_EUP_SCHEDULER ? "ENERGY-URGENCY-PRIORITY" : "BASELINE RMS");
    printf("Battery Drain: ACCELERATED (50000x for demo)\n");
    printf("========================================\n\n");

    vTaskDelay(pdMS_TO_TICKS(3000));

    while (keepRunning) {
        printf("\n\n");
        printf("================================================================================\n");
        printf("EUP SYSTEM STATISTICS (Time: %lu ms)\n",
               (unsigned long)(xTaskGetTickCount() * portTICK_PERIOD_MS));
        printf("================================================================================\n");

        // Battery status with energy state alerts
        xSemaphoreTake(batterySemaphore, portMAX_DELAY);
        float currentSoC = battery.soc;
        printf("[BATTERY] SoC=%.2f%% | Voltage=%.1fV | Current=%.2fA | Temp=%.1f°C",
               battery.soc, battery.voltage, battery.current, battery.temperature);

        // Energy state indication
        if (currentSoC > 80.0f) {
            printf(" | State: NORMAL ✓\n");
        } else if (currentSoC >= 30.0f) {
            printf(" | State: MODERATE ⚠\n");
            if (!energyStateChangePrinted && lastSoC > 80.0f) {
                printf("    >>> ENERGY STATE CHANGE: Entered MODERATE zone (30-80%%) <<<\n");
                energyStateChangePrinted = 1;
            }
        } else if (currentSoC >= 20.0f) {
            printf(" | State: CRITICAL ⚠⚠\n");
            if (energyStateChangePrinted != 2 && lastSoC >= 30.0f) {
                printf("    >>> ENERGY STATE CHANGE: Entered CRITICAL zone (20-30%%) <<<\n");
                printf("    >>> QUADRANT SHIFT: Tasks moving to Q1/Q3/Q5/Q7 <<<\n");
                energyStateChangePrinted = 2;
            }
        } else {
            printf(" | State: EMERGENCY ⚠⚠⚠\n");
            if (energyStateChangePrinted != 3 && lastSoC >= 20.0f) {
                printf("    >>> ENERGY STATE CHANGE: Entered EMERGENCY zone (<20%%) <<<\n");
                printf("    >>> MAXIMUM ENERGY CONSERVATION MODE <<<\n");
                energyStateChangePrinted = 3;
            }
        }

        lastSoC = currentSoC;
        xSemaphoreGive(batterySemaphore);

        // Power statistics
        printf("[POWER]   Avg Power=%.1f mW | Total Energy=%.3f mWh | Measurements=%lu\n",
               avgPowerConsumption, totalEnergyConsumed, (unsigned long)powerMeasurementCount);

        printf("--------------------------------------------------------------------------------\n");
        printf("%-20s %4s %8s %6s %4s %6s %8s %4s\n",
               "Task", "Exec", "Missed", "Quad", "Freq", "EU", "AvgT(ms)", "ASIL");
        printf("--------------------------------------------------------------------------------\n");

        xSemaphoreTake(statsMutex, portMAX_DELAY);

        uint32_t totalExec = 0;
        uint32_t totalMissed = 0;

        for (int i = 0; i < NUM_TASKS; i++) {
            uint32_t avgTime = (taskParams[i].executionCount > 0) ?
                              (taskParams[i].totalExecutionTime / taskParams[i].executionCount) : 0;

            const char* asilStr = taskParams[i].asilLevel == ASIL_QM ? "QM" :
                                 taskParams[i].asilLevel == ASIL_A ? "A" :
                                 taskParams[i].asilLevel == ASIL_B ? "B" :
                                 taskParams[i].asilLevel == ASIL_C ? "C" : "D";

            printf("%-20s %4lu %8lu %6s %4lu %6.3f %8lu %4s\n",
                   taskParams[i].taskName,
                   (unsigned long)taskParams[i].executionCount,
                   (unsigned long)taskParams[i].missedDeadlines,
                   USE_EUP_SCHEDULER ?
                       (taskParams[i].currentQuadrant == Q1 ? "Q1" :
                        taskParams[i].currentQuadrant == Q2 ? "Q2" :
                        taskParams[i].currentQuadrant == Q3 ? "Q3" :
                        taskParams[i].currentQuadrant == Q4 ? "Q4" :
                        taskParams[i].currentQuadrant == Q5 ? "Q5" :
                        taskParams[i].currentQuadrant == Q6 ? "Q6" :
                        taskParams[i].currentQuadrant == Q7 ? "Q7" : "Q8") : "N/A",
                   (unsigned long)(USE_EUP_SCHEDULER ? taskParams[i].currentFrequency : FREQ_LEVEL_7),
                   taskParams[i].energyUrgencyMetric,
                   (unsigned long)avgTime,
                   asilStr);

            totalExec += taskParams[i].executionCount;
            totalMissed += taskParams[i].missedDeadlines;
        }

        xSemaphoreGive(statsMutex);

        printf("--------------------------------------------------------------------------------\n");
        printf("Total: Executions=%lu | Deadline Violations=%lu %s\n",
               (unsigned long)totalExec, (unsigned long)totalMissed,
               totalMissed == 0 ? "✓" : "✗");
        printf("================================================================================\n");

        vTaskDelayUntil(&xLastWakeTime, xPeriod);
    }

    vTaskDelete(NULL);
}

/* ============================================================================
 * TASK INITIALIZATION
 * ============================================================================ */
void initializeTaskParams() {
    // Task 0: Airbag Sensor (ASIL-D)
    strcpy(taskParams[0].taskName, "AirbagSensor");
    taskParams[0].taskID = TASK_AIRBAG_SENSOR;
    taskParams[0].asilLevel = ASIL_D;
    taskParams[0].period = pdMS_TO_TICKS(10);
    taskParams[0].deadline = pdMS_TO_TICKS(5);
    taskParams[0].wcetMs = 1;
    taskParams[0].staticPriority = 9;
    taskParams[0].normalizedPriority = 1.0f;
    taskParams[0].energyPerExec = 15.0f;

    // Task 1: ABS Wheel Speed (ASIL-C)
    strcpy(taskParams[1].taskName, "ABS_WheelSpeed");
    taskParams[1].taskID = TASK_ABS_WHEEL_SPEED;
    taskParams[1].asilLevel = ASIL_C;
    taskParams[1].period = pdMS_TO_TICKS(20);
    taskParams[1].deadline = pdMS_TO_TICKS(10);
    taskParams[1].wcetMs = 3;
    taskParams[1].staticPriority = 8;
    taskParams[1].normalizedPriority = 0.9f;
    taskParams[1].energyPerExec = 28.0f;

    // Task 2: Door Lock Control (ASIL-B)
    strcpy(taskParams[2].taskName, "DoorLockControl");
    taskParams[2].taskID = TASK_DOOR_LOCK_CONTROL;
    taskParams[2].asilLevel = ASIL_B;
    taskParams[2].period = pdMS_TO_TICKS(50);
    taskParams[2].deadline = pdMS_TO_TICKS(50);
    taskParams[2].wcetMs = 5;
    taskParams[2].staticPriority = 5;
    taskParams[2].normalizedPriority = 0.5f;
    taskParams[2].energyPerExec = 45.0f;

    // Task 3: Window Control (ASIL-A)
    strcpy(taskParams[3].taskName, "WindowControl");
    taskParams[3].taskID = TASK_WINDOW_CONTROL;
    taskParams[3].asilLevel = ASIL_A;
    taskParams[3].period = pdMS_TO_TICKS(100);
    taskParams[3].deadline = pdMS_TO_TICKS(100);
    taskParams[3].wcetMs = 8;
    taskParams[3].staticPriority = 4;
    taskParams[3].normalizedPriority = 0.4f;
    taskParams[3].energyPerExec = 82.0f;

    // Task 4: Ambient Lighting (QM)
    strcpy(taskParams[4].taskName, "AmbientLighting");
    taskParams[4].taskID = TASK_AMBIENT_LIGHTING;
    taskParams[4].asilLevel = ASIL_QM;
    taskParams[4].period = pdMS_TO_TICKS(200);
    taskParams[4].deadline = pdMS_TO_TICKS(200);
    taskParams[4].wcetMs = 12;
    taskParams[4].staticPriority = 3;
    taskParams[4].normalizedPriority = 0.3f;
    taskParams[4].energyPerExec = 125.0f;

    // Task 5: Comfort Features (QM)
    strcpy(taskParams[5].taskName, "ComfortFeatures");
    taskParams[5].taskID = TASK_COMFORT_FEATURES;
    taskParams[5].asilLevel = ASIL_QM;
    taskParams[5].period = pdMS_TO_TICKS(500);
    taskParams[5].deadline = pdMS_TO_TICKS(500);
    taskParams[5].wcetMs = 16;
    taskParams[5].staticPriority = 1;
    taskParams[5].normalizedPriority = 0.1f;
    taskParams[5].energyPerExec = 158.0f;

    // Initialize all runtime statistics to zero
    for (int i = 0; i < NUM_TASKS; i++) {
        taskParams[i].executionCount = 0;
        taskParams[i].missedDeadlines = 0;
        taskParams[i].totalExecutionTime = 0;
        taskParams[i].maxExecutionTime = 0;
        taskParams[i].lastExecutionTime = 0;
        taskParams[i].timeUrgency = 0.0f;
        taskParams[i].energyThreshold = 0.0f;
        taskParams[i].energyUrgencyMetric = 0.0f;
        taskParams[i].currentQuadrant = Q2;
        taskParams[i].currentFrequency = FREQ_LEVEL_7;
    }
}

/* ============================================================================
 * FREERTOS HOOKS
 * ============================================================================ */
void vApplicationIdleHook(void) {
    usleep(1000);
}

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    printf("[ERROR] Stack overflow in task: %s\n", pcTaskName);
    exit(1);
}

void vApplicationMallocFailedHook(void) {
    printf("[ERROR] Malloc failed!\n");
    exit(1);
}

void vAssertCalled(const char * const pcFileName, unsigned long ulLine) {
    printf("[ASSERT] %s:%lu\n", pcFileName, ulLine);
    exit(1);
}

/* ============================================================================
 * MAIN
 * ============================================================================ */
int main(void) {
    signal(SIGINT, sigintHandler);

    printf("\n");
    printf("====================================================================\n");
    printf("FreeRTOS Energy-Urgency-Priority (EUP) Scheduler\n");
    printf("====================================================================\n");
    printf("Implementation of IEEE Paper by Azad Mohammed Shaik\n");
    printf("Three-Dimensional Battery-Aware Real-Time Control\n");
    printf("Mode: %s\n", USE_EUP_SCHEDULER ? "EUP SCHEDULER" : "BASELINE RMS");
    printf("====================================================================\n\n");

    // Create semaphores
    statsMutex = xSemaphoreCreateMutex();
    batterySemaphore = xSemaphoreCreateMutex();
    if (statsMutex == NULL || batterySemaphore == NULL) {
        printf("[ERROR] Failed to create semaphores\n");
        return 1;
    }

    // Initialize subsystems
    initializeFrequencyLevels();
    initializeBattery();
    initializeTaskParams();

    printf("\nCreating Body Control Module (BCM) tasks...\n\n");

    // Create tasks
    for (int i = 0; i < NUM_TASKS; i++) {
        static TaskID_t taskIDs[NUM_TASKS];
        taskIDs[i] = (TaskID_t)i;

        xTaskCreate(GenericTask,
                    taskParams[i].taskName,
                    configMINIMAL_STACK_SIZE * 2,
                    &taskIDs[i],
                    taskParams[i].staticPriority,
                    &taskHandles[i]);
    }

    // Create monitoring task
    xTaskCreate(Task_Monitor, "EUP_Monitor",
                configMINIMAL_STACK_SIZE * 2, NULL, 2, NULL);

    printf("\nStarting FreeRTOS Scheduler with EUP framework...\n");
    printf("Press Ctrl+C to stop and view final results\n\n");

    vTaskStartScheduler();

    // Should never reach here
    printf("[ERROR] Scheduler failed to start!\n");
    return 1;
}
