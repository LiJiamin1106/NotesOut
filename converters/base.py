def log(msg, log_fn=None):
    if log_fn:
        log_fn(msg)
    else:
        print(msg)