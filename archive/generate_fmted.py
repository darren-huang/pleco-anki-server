import re

def parse_silk_def(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def generate_fmted(content):
    traditional = "絲"
    simplified = "丝"
    pinyin = "sī"
    
    header = f'<div align="left"><p><span style="font-size:32px" ;="">{traditional}〔{simplified}〕</span><br>\n'
    header += f'<span style="color:#B4B4B4;"><b><span style="font-size:0.80em;">PY </span></b></span><span style="color:#E30000;"><span style="font-weight:600;">{pinyin}</span></span></p>\n</div>'
    
    noun_section = re.search(r'noun\s+1\s+silk\s+2\s+threadlike\s+thing\s+(.+?)\s+3\s+stringed\s+instruments', content, re.DOTALL).group(1)
    noun_section = re.sub(r'\s+', ' ', noun_section).strip()
    noun_section = noun_section.replace('(', '').replace(')', '')
    
    measure_word_section = re.search(r'measure\s+word\s+1\s+a\s+thread\s+or\s+shred\s+of\s+(.+?)\s+2\s+si\s+a\s+a\s+traditional\s+unit\s+of\s+length', content, re.DOTALL).group(1)
    measure_word_section = re.sub(r'\s+', ' ', measure_word_section).strip()
    
    fmted_content = header + '\n<div align="left"><p><b><span style="font-size:0.80em;"><span style="color:#B4B4B4;">NOUN</span></span></b><br>\n'
    fmted_content += f'<b>1\t</b>silk<br>\n<b>2\t</b>threadlike thing<br>\n</p>\n'
    fmted_content += f'<blockquote style="border-left: 2px solid #0078c3; margin-left: 3px; padding-left: 1em; margin-top: 0px; margin-bottom: 0px;"><p>{noun_section}</p></blockquote>\n'
    fmted_content += f'<p><b>3\t</b>stringed instruments</p>\n'
    fmted_content += f'<p><b><span style="font-size:0.80em;"><span style="color:#B4B4B4;">MEASURE WORD</span></span></b><br>\n'
    fmted_content += f'<b>1\t</b>a thread or shred of<br>\n</p>\n'
    fmted_content += f'<blockquote style="border-left: 2px solid #0078c3; margin-left: 3px; padding-left: 1em; margin-top: 0px; margin-bottom: 0px;"><p>{measure_word_section}</p></blockquote>\n'
    fmted_content += f'<p><b>2\t</b>si<br>\n<b>a</b> a traditional unit of length, equal to 0.00001 chi (市尺), and equivalent to 3.333 microns<br>\n'
    fmted_content += f'<b>b</b> a traditional unit of weight, equal to 0.000001 jin (市斤), and equivalent to 0.5 milligram or 0.0075 grain<br>\n'
    fmted_content += f'<b>3\t</b>a tiny bit; trace<br>\n</p>\n'
    fmted_content += f'<p><b>4\t</b>one ten-thousandth of certain units of measure</p>\n</div><plecoentry c="00000000" d="50414345" e="01d53000" x="-1"></plecoentry>'
    
    return fmted_content

def write_fmted_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

if __name__ == "__main__":
    silk_def_path = '/Users/darrenhuang/code/pleco-anki-server/silk_def.txt'
    silk_def_fmted_path = '/Users/darrenhuang/code/pleco-anki-server/silk_def_fmted.txt'
    
    silk_def_content = parse_silk_def(silk_def_path)
    fmted_content = generate_fmted(silk_def_content)
    write_fmted_file(silk_def_fmted_path, fmted_content)
