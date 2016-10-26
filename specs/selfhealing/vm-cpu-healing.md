# GOAL
- Enforce fair cpu usage policy
- Ommit neighbouring vms from having impact from noisy neighbours
- Create a feedback channel to vm owner when his virtual machine consumes an unusable amount of cpu

# CPU fair use policy
Cpu capacity is being oversubscribed 4x. Which means that every vcpu can only consume max 25% of a single physical hyperthread (=0.25 cpu seconds / second).

## Parameters
- **VCPU_UNFAIR_USE_THRESHOLD**: X cpu seconds / second (eg 0.8 = 80% of hyperthread. 1 hyperthreaded core can do max 2 cpu seconds / second)
- **WARN_TIME**: Time in seconds for which a vcpu consumes more than *VCPU_UNFAIR_USE_THRESHOLD* cpu seconds / second constantly
- **QUARANTINE_TIME**: Time in seconds after *WARN_TIME* when a vcpu is pinned on a physical hyperthread. Max 4 vpcus are pinned on 1 hyperthread.
- **QUARANTIME_RELEASE_TIME**: Time in seconds after a vcpu is being put in quarantine can be tried to be released

## VCPU quarantine section
Vcpus are for vm are grouped together on X amount of the complete cpu power of a node. See ../provisioning-limits.md for more information.
The VCPU quarantine section are the hyperthreads at the end of the reserved cpu pool of the node. On each hyperthread max 4 vcpu's will be pinned.

## Self healing script
- jumpscript name: vm-cpu-fair-use-policy.py
- jumpscript rules

### 1) We measured a problem
When a vcpu consumes more than **VCPU_UNFAIR_USE_THRESHOLD** for more than **WARN_TIME** an automatic email will be sent to the owner of the vm with the message that his vm consumes an abnormal amount of cpu and that he needs to look into it.

### 2) The vm owner did not solve the problem in time
If the owner ignores this message after **QUARANTINE_TIME** the vpcu will be placed in the **VCPU quarantine section** (see above). The owner of the vm gets a second message stating that his vm has been put into quarantine.

### 3) Lets check wether the problem is already resolved
**QUARANTINE_TIME** seconds after being put into quarantine, a vcpu is pinned on one of the host reserved cpu's for 5 seconds.
- If the vcpu consumes less than the **VCPU_UNFAIR_USE_THRESHOLD** over these 5 seconds, the vcpu is released from quarantine and moved back into the group of cpu's reserved for vms. Also the owner of the vm is notified about this via an email message.
- Else the vcpu is pinned back into the **VCPU quarantine section**. Each time the vcpu is being put back to quarantine the **QUARANTINE_TIME** for a next release check will be doubled.
