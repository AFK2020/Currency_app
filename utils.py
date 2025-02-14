import functools
import time


def retry(func, retries=3):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        attemps=0

        while attemps<retries:
            try:
                return func(*args,*kwargs)
            except ConnectionError as e:
                print(e)
                time.sleep(2)
                attemps+=1

        print("Max retries reached. Exiting.")
        raise Exception(f"Failed to execute {func.__name__} after {retries} retries.")
    
    return wrapper
