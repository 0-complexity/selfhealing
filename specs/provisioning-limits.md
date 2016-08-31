# Introduction

In order to protect the cloud infrastructure from its own consumers we are going to make sure that the deployed resources cannot drain all capacity from the cloud infrastructure, disabling the cloud infrastructure itself as such.

## General principles

- define the minimum amount of resources required by the G8OS to function properly on each of the nodes
- define the maximum amount of resources that is allowed to be used by both G8OS and guests (can be a % of total resources to be configured at install time per node)
- make sure this amount of resources is guaranteed on each of the nodes
- agents measure the resource utilization and throttle the utilization by guests to make sure that minimum resources are always guaranteed for the G8OS
- this allows for thin provisioning and thus oversubscription
- @TODO later - add a scheduler that provides intelligent provisioning of resources on the nodes

## Network

No need to constrain the network because mgmt traffic for physical machines goes over a reserved 1GB backplane with a separate reserved switch connecting the G8 nodes and controller together in one mgmt lan.

## CPU

- resources to be constraint is CPU utilization
- we should do thin provisioning
- Via vcpu pinning we can make sure that guests are not able to consume every bit of cpu power preventing the cloud itself from functioning, by freeing up **G8.minimum-reserved-host-cpu**.

**Interesting links:**
- [vcpu pinning](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization_Tuning_and_Optimization_Guide/sect-Virtualization_Tuning_Optimization_Guide-NUMA-NUMA_and_libvirt-vcpu_pinning_with_virsh.html)
- [emulator pinning](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization_Tuning_and_Optimization_Guide/sect-Virtualization_Tuning_Optimization_Guide-NUMA-NUMA_and_libvirt-domain_cpu_pinning_with_virsh.html)
- https://pythonhosted.org/psutil/#cpu

## Memory

- resources to be constraint is used memory per node
- no thin provisioning, Memory does not get oversubscribed
- Before booting up a virtual machine we need to check that the combined assigned memory sizes to the guests leaves at least **G8.minimum-reserved-host-os-memory** MB of memory available to the host operating system.
To make sure that only 1 process can do this check simultaniously this process should try to exclusifly lock some file before executing this task, and only free-up the lock file after the guest has been started.

## G8 provisioning limits

- G8.minimum-reserved-host-os-memory [MB]
  - For now hardcode to 16GB RAM
- G8.minimum-reserved-host-cpu [#]
  - For now hardcode to 4 CPUs (2 cores)
