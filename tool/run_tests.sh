#!/usr/bin/env bash

# Setup virtual CAN interface vcan0
if ! ifconfig | grep -q "vcan0:"; then
    echo "Setting up virtual CAN interface vcan0"
    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set vcan0 up
fi

# Number of test rounds
rounds=1
# Run tests
for ((i=1; i<=$rounds; i++))
do
  printf "*** [Round $i/$rounds] Python 2\n"
  python2 -m unittest discover
  echo ""
  printf "*** [Round $i/$rounds] Python 3\n"
  python3 -m unittest discover
done
