#!/usr/bin/env bash

export SURFACE_DISPATCHERS_NUMBER=1 \
       JOINERS_NUMBER=1 \
       AGE_CALCULATORS_NUMBER=1 \
       AGE_DIFFERENCE_FILTERS_NUMBER=1 \
       DIFFERENT_HANDS_FILTERS_NUMBER=1

docker-compose up --build \
                  --scale surface_dispatcher=$SURFACE_DISPATCHERS_NUMBER \
                  --scale joiner=$JOINERS_NUMBER \
                  --scale age_calculator=$AGE_CALCULATORS_NUMBER \
                  --scale age_difference_filter=$AGE_DIFFERENCE_FILTERS_NUMBER \
                  --scale different_hands_filter=$DIFFERENT_HANDS_FILTERS_NUMBER
