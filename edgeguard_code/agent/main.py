#!/usr/bin/env python

import logging.config
from utils.scheduler import Scheduler


if __name__ == "__main__":
    FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    Scheduler.run()

    
