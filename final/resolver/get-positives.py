import json
import sys

print("Suggested system state [name, version]:\n")

with open(sys.argv[1], 'r') as file:
    num_to_pkg = json.load(file)

with open(sys.argv[2], 'r') as file:
    for line in file:
        line = line.rstrip() # remove trailing \n

        if line == "0":
            break

        print(num_to_pkg[line])
