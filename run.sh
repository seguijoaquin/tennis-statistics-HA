#!/usr/bin/env bash

export DATE_FILTERS_NUMBER=3 \
       SURFACE_DISPATCHERS_NUMBER=3 \
       JOINERS_NUMBER=3 \
       AGE_CALCULATORS_NUMBER=3 \
       AGE_DIFFERENCE_FILTERS_NUMBER=3 \
       DIFFERENT_HANDS_FILTERS_NUMBER=3

docker-compose up --build \
                  --scale date_filter=$DATE_FILTERS_NUMBER \
                  --scale surface_dispatcher=$SURFACE_DISPATCHERS_NUMBER \
                  --scale joiner=$JOINERS_NUMBER \
                  --scale age_calculator=$AGE_CALCULATORS_NUMBER \
                  --scale age_difference_filter=$AGE_DIFFERENCE_FILTERS_NUMBER \
                  --scale different_hands_filter=$DIFFERENT_HANDS_FILTERS_NUMBER
