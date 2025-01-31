# collatex-tei

Utility functions for converting between CollateX JSON and TEI XML.

---

## Installation

```console
pip install collatex-tei
```

## Quick Start

```python
import os
import json

from collatex_tei import collatex_to_tei

# Read JSON from a file
with open("data.json") as f:
    data = json.load(f)

# Get the TEI files as BeautifulSoup objects
main_soup, witness_soups = collatex_to_tei(data, path_to_witnesses="./witness")

# Write the TEI spine (standoff)
with open("main.xml", "w") as file:
    file.write(str(main_soup.prettify()))

# Write the TEI witnesses
for wit in witness_soups:
    with open(f"./witness{wit.siglum}.xml", "w") as file:
        file.write(str(wit.soup.prettify()))
```
