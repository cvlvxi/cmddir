# print("cmd 1 executed")

from unicodedata import decimal


print("cmd 1 executed")

def main(*args, **kwargs):
    print(f"args: {args}, kwargs: {kwargs}")


if __name__ == "__main__":
    main()
