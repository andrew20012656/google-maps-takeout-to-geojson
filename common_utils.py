from datetime import datetime


def convert_to_timestamp(time_str: str):
    """
    Return a POSIX timestamp 

    Parameters:
    - `time_str` (str): a string representing a datetime following the following formats:
        - "%Y-%m-%dT%H:%M:%S.%fZ"
        - "%Y-%m-%dT%H:%M:%SZ"
        - "%Y:%m:%d %H:%M:%S"
        - "%Y%m%dT%H%M%S.%fZ"
    """
    date_formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                    "%Y:%m:%d %H:%M:%S", "%Y%m%dT%H%M%S.%fZ"]
    datetime_obj = None
    for date_format in date_formats:
        try:
            datetime_obj = datetime.strptime(time_str, date_format)
            break
        except ValueError:
            continue
    if datetime is None:
        print("The input Datetime format is not recognized")
    else:
        return datetime_obj.timestamp()
