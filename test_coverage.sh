#!/usr/bin/env bash

coverage run --source=missing_bids/ --omit=*/tests/*,*__init__.py \
-m py.test missing_bids/tests/basic_test.py

coverage report -m
