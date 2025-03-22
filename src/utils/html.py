from bs4 import BeautifulSoup


def reorder_nested_spans(html_text):
    # Parse the HTML text
    soup = BeautifulSoup(f"<root>{html_text}</root>", "html.parser")

    # Find all span elements
    spans = soup.find_all("span")

    for span in spans:
        style = span.get("style", "")
        if "font-weight" in style:
            nested_span = span.find("span")
            if nested_span is not None:
                nested_style = nested_span.get("style", "")
                if "color" in nested_style:
                    # Swap the styles
                    span["style"], nested_span["style"] = (
                        nested_span["style"],
                        span["style"],
                    )

        if ";" in spans[0].attrs:
            del spans[0].attrs[";"]

    # Convert the soup back to a string
    return str(soup).replace("<root>", "").replace("</root>", "")


# # Example usage
# html_text = '<span style="font-weight:600;"><span style="color:#FF0000;">Text</span></span>'
# reordered_html = reorder_nested_spans(html_text)
# print(reordered_html)
