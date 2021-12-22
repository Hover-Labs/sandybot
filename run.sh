#!/bin/bash

# This script patches the timing for python to be the "real" date, even in environments where we monkey with
# the server time. 

LD_PRELOAD=/usr/local/lib/faketime/libfaketime.so.1 \
  FAKETIME="$(curl -s http://worldclockapi.com/api/json/est/now | jq -r '.currentDateTime' | cut -b -10) 00:00:00" \
  python main.py
