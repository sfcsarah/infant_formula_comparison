import argparse
from infant_formula.save_page import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save a formula product page as PDF from the CSV.")
    parser.add_argument("index_100", type=int, help="index_100 value (row index + 100)")
    args = parser.parse_args()
    run(args.index_100)
