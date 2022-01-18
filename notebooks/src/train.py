# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Top-level entrypoint script for model training (also supports loading for inference)
"""
# Python Built-Ins:
import logging
import os
import sys

if __name__ == "__main__":
    # If the file is running as a script, we're in training mode and should run the actual training
    # routine (with a little logging setup before any imports, to make sure output shows up ok):
    consolehandler = logging.StreamHandler(sys.stdout)
    consolehandler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")
    )
    logging.basicConfig(handlers=[consolehandler], level=os.environ.get("LOG_LEVEL", logging.INFO))

    from my_code.train import main

    main()
else:
    # If the file is imported as a module, we're in inference mode and should pass through the
    # override functions defined in the inference module. This is to support directly deploying the
    # model via SageMaker SDK's Estimator.deploy(), which will carry over the environment variable
    # SAGEMAKER_PROGRAM=train.py from training - causing the server to try and load handlers from
    # here rather than inference.py.
    from my_code.inference import *
