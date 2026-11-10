"""Extract text and URI annotations from a browser-downloaded test report."""

import json
import sys

from pypdf import PdfReader


def main() -> None:
    reader = PdfReader(sys.argv[1], strict=True)
    text = []
    links = []
    for page in reader.pages:
        text.append(page.extract_text())
        for reference in page.get("/Annots", []):
            annotation = reference.get_object()
            action = annotation.get("/A")
            if annotation.get("/Subtype") == "/Link" and action is not None:
                if action.get("/S") == "/URI":
                    links.append(str(action["/URI"]))
    print(json.dumps({"text": "\n".join(text), "links": links}))


if __name__ == "__main__":
    main()
