from datetime import datetime

def convert_to_timestamp(time_str: str):
    """
    Return a POSIX timestamp 

    Parameters:
    - time_str (str): a string representing a timestamp following ISO 8601 Standard
    """
    date_formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y:%m:%d %H:%M:%S", "%Y%m%dT%H%M%S.%fZ"]
    start_datetime = None
    for date_format in date_formats:
        try:
            start_datetime = datetime.strptime(time_str, date_format)
            break
        except ValueError:
            continue
    
    print(start_datetime)
    return start_datetime.timestamp()