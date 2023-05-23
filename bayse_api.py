import config
import json
import logging
import requests
import sys
import time

logging.basicConfig(format='batch_submit: %(levelname)s - module=%(module)s function=%(funcName)s() - message=%('
                           'message)s', level=logging.INFO, force=True)
logger = logging.getLogger()


def setup_session():
    s = requests.Session()
    s.headers = {"X-API-KEY": config.API_KEY}
    return s


def process_urls(source_instance, bayse_api_session):
    """Calls Bayse API to submit URLs. Tries to sleep for 0. seconds between submissions."""
    have_urls = len(source_instance.urls_to_process) > 0
    logger.info(f"Processing {len(source_instance.urls_to_process)} URLs")
    sleep_time = 0.1  # time in between submissions, in seconds (default)
    while have_urls:
        (source_tag, url) = source_instance.urls_to_process.popleft()
        have_urls = len(source_instance.urls_to_process) > 0
        payload = json.dumps({"url": url, "getScreenshot": True, "allDestinationDetails": True,
                              "tags": config.SOURCE_TAGS_DEFAULT + [source_tag]
                              })
        try:
            response = bayse_api_session.post(config.BAYSE_INTERPRETATION_ENDPOINT, data=payload)
            if response.status_code != 200:
                logger.error(f"{source_tag}: Something FAILED for submission:\n {response.status_code} ->"
                             f" {response.text}")
                if response.status_code == 429:  # too many requests
                    logger.info(f"Sleeping for a minute to give the API a break.")
                    sleep_time += 0.05  # increase the sleep time each time to back off and avoid flooding
                    time.sleep(60)
        except Exception as e:
            logger.error(f"{source_tag}: Issue with {url}: {e}. Skipping\n")
        # capture new urls we've processed so we don't re-run them!
        source_instance.update_processed_file([(source_tag, url)])
        time.sleep(sleep_time)


def process_urls_batch(input_urls_queue, bayse_api_session, source_tag=None, results_file=None):
    """Calls Bayse API to submit URLs. Tries to sleep for .1 seconds between submissions."""
    have_urls = len(input_urls_queue) > 0
    source_tag = "pc_feed" if not source_tag else source_tag  # a temporary feed used for testing
    try:
        fout = open(results_file, "w")
    except Exception as e:
        logger.error(f"Failed to open {results_file}: {e}. Quitting.")
        sys.exit()
    while have_urls:
        url = input_urls_queue.popleft()
        have_urls = len(input_urls_queue) > 0
        logger.info(f"{source_tag}: Processing {url}")
        payload = json.dumps({"url": url, "getScreenshot": True, "allDestinationDetails": True,
                              "tags": config.SOURCE_TAGS_DEFAULT + [source_tag]
                              })
        try:
            response = bayse_api_session.post(config.BAYSE_INTERPRETATION_ENDPOINT, data=payload)
            if response.status_code != 200:
                logger.error(f"{source_tag}: Something FAILED for submission:\n {response.status_code} ->"
                             f" {response.text}")
            else:
                fout.write(f"{response.text}\n")
        except Exception as e:
            logger.error(f"{source_tag}: Issue with {url}: {e}. Skipping\n")
        time.sleep(0.1)
    try:
        fout.close()
    except Exception as e:
        logger.error(f"Failed to close file: {e}")


def check_result_status(result_uuid):
    """Makes sure result is ready"""
    ready = False
    error = False
    url = f"{config.BAYSE_INTERPRETATION_STATUS_ENDPOINT}request_id={result_uuid}"
    payload = {}
    headers = {
        'X-API-KEY': f'{config.API_KEY}'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    try:
        if response.status_code != 200:
            logger.error(f"Something FAILED while checking STATUS for ID {result_uuid}:\n"
                         f" {response.status_code} ->"
                         f" {response.text}")
            error = response.text
        else:
            try:
                result = response.json()
                if result["status"] == "Failed":
                    error = True
                elif result["status"] == "In Progress":
                    ready = False
                    error = False
                elif result["status"] == "Complete":
                    ready = True
                    error = False
                else:
                    ready = False
                    error = True
            except Exception as f:
                logger.error(f"Some unknown failure happened while trying to check STATUS for ID {result_uuid}: {f}")
                error = True
    except Exception as e:
        logger.error(f"Failed while trying to check STATUS for ID {result_uuid}: {e}")
        error = e
    return ready, error


def save_result_uuid(result_uuid):
    """Takes a result UUID and returns its data"""
    # Check the result first for status
    ready, error = check_result_status(result_uuid)
    if error:
        logger.error(f"Something failed while trying to process {result_uuid} within the Bayse backend.")
        return
    attempts = 8
    while not ready and attempts > 0:
        time.sleep(config.SLEEP_TIME)
        ready, error = check_result_status(result_uuid)
        if error:
            logger.error(f"Something failed while trying to process {result_uuid} within the Bayse backend.")
            return
        if not ready and not error:
            logger.info(f"Result {result_uuid} not yet ready. Retrying in {config.SLEEP_TIME} seconds")
        attempts -= 1
    if not ready and attempts <= 0:
        logger.error(f"Something failed while trying to process {result_uuid} within the Bayse backend.")
        return
    elif not ready:
        logger.error(f"Some other (likely Bayse backend) error occurred for {result_uuid}")
        return
    # otherwise, finally process
    payload = {}
    headers = {
        'X-API-KEY': f'{config.API_KEY}'
    }
    url = f"{config.BAYSE_REQUEST_INTERPRETATION_RESULTS_ENDPOINT}result_id={result_uuid}"
    response = requests.request("GET", url, headers=headers, data=payload)
    try:
        if response.status_code != 200:
            logger.error(f"Something FAILED for request with ID {result_uuid}:\n {response.status_code} ->"
                         f" {response.text}")
        else:
            with open(config.RESULTS_FILENAME, "a+") as fout:
                json.dump(response.json(), fout)
                fout.write("\n")
    except Exception as e:
        logger.error(f"Failed while trying to save result with ID {result_uuid}: {e}")
