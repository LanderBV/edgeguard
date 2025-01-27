#!/usr/bin/env python

import logging.config
from utils.csv_utils.scheduler_csv import Scheduler

if __name__ == "__main__":
    FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    Scheduler.run_with_csv("../data/predict_values/data_real.csv")
    
