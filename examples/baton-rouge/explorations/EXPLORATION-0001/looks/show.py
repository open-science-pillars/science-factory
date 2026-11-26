# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print named blocks of a receipt another look wrote, so their numbers are in a look's output. Exploring."""
import json
import sys

d = json.load(open(sys.argv[1]))
for key in sys.argv[2:]:
    node = d
    for part in key.split("."):
        node = node[part]
    print(key + ": " + json.dumps(node))
