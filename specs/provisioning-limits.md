# Introduction

In order to protect the cloud infrastructure from its own consumers we are going to make sure that the deployed resources cannot drain all capacity from the cloud infrastructure, disabling the cloud infrastructure itself as such.

## Network

?? Is this possible via OpenvSwitch ??

## CPU

Via vcpu pinning we can make sure that guests are not able to consume every bit of cpu power preventing the cloud itself from functioning, by freeing up **G8.minimum-reserved-host-cpu**.

## Memory

Before booting up a virtual machine we need to check that the combined assigned memory sizes to the guests leaves at least **G8.minimum-reserved-host-os-memory** MB of memory available to the host operating system.
To make sure that only 1 process can do this check simultaniously this process should try to exclusifly lock some file before executing this task, and only free-up the lock file after the guest has been started.

## G8 provisioning limits

- G8.minimum-reserved-host-os-memory [MB]
- G8.minimum-reserved-host-cpu [#]
- G8.minimum-reserved-host-networking-bandwidth [MB/s]
