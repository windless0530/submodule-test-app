#!/bin/bash

find . -name "*.py" | xargs -P 8 -I {} yapf -i {} ;
