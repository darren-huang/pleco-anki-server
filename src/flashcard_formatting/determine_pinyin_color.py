def get_pinyin_color(pinyin):
    tones = {
        1: '#E30000',  # Red
        2: '#02B31C',  # Green
        3: '#8900BF',  # Purple
        4: '#1510F0',  # Blue
        5: '#777777'   # Gray (neutral tone)
    }

    tone = 1 if any(char in pinyin for char in 'āēīōūǖ') else \
           2 if any(char in pinyin for char in 'áéíóúǘ') else \
           3 if any(char in pinyin for char in 'ǎěǐǒǔǚ') else \
           4 if any(char in pinyin for char in 'àèìòùǜ') else 5

    return tones[tone]
