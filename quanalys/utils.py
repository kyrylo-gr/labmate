import datetime


def get_timestamp() -> str:
    x = datetime.datetime.now()
    return x.strftime("%Y-%m-%d_%H-%M-%S")
