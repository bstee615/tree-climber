#!/bin/bash

set -e

find c-example-code -type f -name '*.c' | xargs -n1 python -m tree_climber
