## Goal :

Monitor if a network bond (if there is one) has both (or more) interfaces properly active.

### What iz thees bond?

A bond is a way to aggregate 2 (oer more) NICS so that network traffic keeps being forwarded in case a link fails.

A failing link can be:
  * nic breakage
  * Some (hopehully inadvertent) cable yanker
  * Port breakage on switch
  * Whole switch breakage (in case of an MLAG setup)

### Backplane1 bond

The core network backend Vswitch (backplane1), has at least one NIC connected to it, but in case there are 2 _AND_ the switch is configured properly,
we create a bond if there are at least 2 interfaces.

#### Standard LACP 

When the 2 nics are connected to the switch :
  * one bond
  * active LACP
  * passive LACP (on the switch) if possible

#### MLAG bond (2 switches)
When the 2 switches are connected to 2 separate switches 
  * one bond
  * active LACP
  * balance mode `failsafe`
  * both switches configured with a working IPL and MLAG

### Verify

  ```
# Check if a bond exists (if not, backplane has only a single port)
ovs-appctl bond/show
# needs to return empty -> no bond

  ```

Check if the existing bond is up

```
# here we assume a bond of minimum 2 NICs that need to be up
a=(`ovs-appctl bond/show | awk '/slave .*:/&&/enabled/{split($2,a,":") ; print a[1]}'`)
if [ ${#a[@]} -lt 2 ] ; then
    echo "ALERT!! Bond b0Rk3d!!"
fi
```

