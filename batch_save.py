import bayse_api
import collections
import config
import itertools
import json
import logging

logging.basicConfig(format='batch_submit: %(levelname)s - module=%(module)s function=%(funcName)s() - message=%('
                           'message)s', level=logging.INFO, force=True)
logger = logging.getLogger()


def save_results():
    """Takes a file containing one result ID JSON record per line, requests the results, and saves to a file named
       bayse_results_data.json
    """
    try:
        with open(config.UUIDS_FILENAME, "r") as f:
            for line in f.readlines():
                try:
                    result_id = json.loads(line)["request_id"]
                    logger.info(f"Attempting to save {result_id}")
                    bayse_api.save_result_uuid(result_uuid=result_id)
                except Exception as f:
                    logger.error(f"Failed to save result ID: {f}. Skipping")
    except Exception as e:
        logger.error(f"Failed to process results file: {e}")
    logger.info(f"Finished batch saving results to {config.RESULTS_FILENAME}")


save_results()