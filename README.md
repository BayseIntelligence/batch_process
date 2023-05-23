Before starting, go to config.py and update it with your API Key.

Use a file named _batch_input.txt_ in the same directory as the code to pass in your URLs. The file should have one url 
per line to be processed and should not be defanged.

Run the batch submission by typing ```python3 batch_submit.py```

Information will be logged to the screen as the run occurs.

While the data is being processed, the UUIDs (that will need to be used to look up the final results) will be logged 
to _bayse_result_ids.txt_, one per line.

To review those results, you can do one of three things:
1. ) Type python3 batch_save.py to save all results to a file named _bayse_results_data.json_
2. ) Perform an API request for each result (documented at https://documenter.getpostman.com/view/23795814/2s8YRpGWoi#724e0559-5496-4460-a01e-4f7a71d6713c)
3. ) Look up the result in the UI at ```https://bayse.io/interpretation/UUID```

Filenames can be customized in _config.py_