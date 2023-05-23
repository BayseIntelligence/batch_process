import bayse_api
import collections
import config
import itertools
import logging

logging.basicConfig(format='batch_submit: %(levelname)s - module=%(module)s function=%(funcName)s() - message=%('
                           'message)s', level=logging.INFO, force=True)
logger = logging.getLogger()


def process():
    """Takes a file with one url per line to be processed. Submits to the Bayse API"""
    bayse_api_session = bayse_api.setup_session()
    tag = config.TRIAL_TAG
    if len(tag) == 0:
        tag = None
    input_urls = collections.deque(maxlen=1000000)
    try:
        with open(config.BATCH_INPUT_FILENAME, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if not line.startswith("http"):
                    logger.warning(f"Skipping line {line} due to incorrect format.")
                    continue
                input_urls.append(line.strip())
    except Exception as e:
        logger.error(f"Failed to process file: {e}")
    try:
        logger.info(f"First 5 inputs to process: {list(itertools.islice(input_urls, 1, 5))}")
    except Exception as e:
        logger.error(f"Failed to find at least 5 inputs for {input_urls}: {e}. Continuing with what we have")
    bayse_api.process_urls_batch(input_urls, bayse_api_session, source_tag=tag, results_file=config.UUIDS_FILENAME)
    logger.info(f"Finished batch processing URLs")


process()