import os
from convertBase import process_dir

if "__main__" == __name__:
    num = process_dir(os.path.abspath("."), "small", 0.5)
    print("Done. ")
    print(f"Totally {num} files processed.")
