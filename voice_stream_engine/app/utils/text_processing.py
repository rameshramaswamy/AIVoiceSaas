import re

class TextBuffer:
    def __init__(self):
        self.buffer = ""
        self.end_sentence_pattern = re.compile(r'[.!?]\s')

    def append(self, text: str):
        self.buffer += text

    def process(self):
        """
        Yields complete sentences and keeps incomplete ones in buffer.
        """
        while True:
            match = self.end_sentence_pattern.search(self.buffer)
            if match:
                end_idx = match.end()
                sentence = self.buffer[:end_idx].strip()
                self.buffer = self.buffer[end_idx:]
                if sentence:
                    yield sentence
            else:
                break
    
    def flush(self):
        if self.buffer.strip():
            final = self.buffer.strip()
            self.buffer = ""
            return final
        return None