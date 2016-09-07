# GOAL

Control number of processes/threads running on the system

# Description

Read information from local redis see [monitored-metrics](monitored-metrics)

If the amount of threads used by the system grows over **18000** interrupts the operator should see a **warning**.  
If the amount of thrrads used by the system grows over **20000** interrupts the operator should see an **error**.
