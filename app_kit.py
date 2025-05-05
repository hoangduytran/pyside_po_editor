#!/usr/bin/env python3
import AppKit

def main():
    # Get all symbols in the AppKit module
    symbols = dir(AppKit)
    # Sort them alphabetically
    symbols.sort()
    # Print each symbol on its own line
    for sym in symbols:
        print(sym)

if __name__ == "__main__":
    main()
