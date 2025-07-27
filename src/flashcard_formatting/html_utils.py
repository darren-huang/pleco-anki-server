import re
from bs4 import BeautifulSoup


def reorder_bold_and_color_spans(html_text):
    """
    Reorders nested bold and color span tags to ensure consistent HTML structure.

    Args:
        html_text (str): The HTML text to process

    Returns:
        str: The processed HTML text with reordered tags
    """
    # Parse the HTML text
    soup = BeautifulSoup(f"<root>{html_text}</root>", "html.parser")

    # Find all bold tags
    bold_tags = soup.find_all("b")

    for bold_tag in bold_tags:
        # Check if the bold tag contains a span with the specific color #0078C3
        color_span = bold_tag.find("span", style=lambda s: s and "color:#0078C3" in s)

        if color_span:
            # Get the content of the span
            content = color_span.contents

            # Create new structure: span outside, b inside
            new_span = soup.new_tag("span")
            new_span["style"] = color_span["style"]

            new_bold = soup.new_tag("b")
            new_bold.extend(content)

            new_span.append(new_bold)

            # Replace the old structure with the new one
            bold_tag.replace_with(new_span)

    # Convert the soup back to a string
    return str(soup).replace("<root>", "").replace("</root>", "")


def fix_separated_pos_tags(html_text):
    """
    Fix part-of-speech tags that have been incorrectly separated.

    Args:
        html_text (str): The HTML text to process

    Returns:
        str: The processed HTML text with fixed POS tags
    """
    pos_text = (
        '<span style="font-size:0.80em;"><span style="color:#B4B4B4;">.*?</span></span>'
    )
    patt = f"({pos_text})</b> <b>({pos_text})"
    previous_text = ""
    current_text = html_text
    while current_text != previous_text:
        previous_text = current_text
        current_text = re.sub(patt, r"\1</b><br/>\n<b>\2", current_text)
    return current_text
