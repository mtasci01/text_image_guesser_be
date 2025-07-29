import uuid
from docx import Document
import numpy as np
import os.path

PUNCTUATION = {",",".",";",":","(",")","→","’","'","”","“","\""}
INPUT_FILE = 'input_to_scramble.docx'


def docx_char_scrambler(document,p_change):
    p_change = float(p_change)

    if p_change <= 0 or p_change > 1:
        raise TypeError("invalid p_change " + str(p_change))

    for p in document.paragraphs:

        strArr = []
        
        for i in range(len(p.text)):
            c = p.text[i]
            randnum = np.random.rand()
            if not(c in PUNCTUATION or c == ' ') and  randnum <= p_change:
                strArr.append("?")
            else:
                strArr.append(p.text[i]) 
        p.text = strArr          
    return document

def main():

    if not(os.path.isfile(INPUT_FILE)):
        print(INPUT_FILE + " not found")
    else:
        print("Start processing "+ INPUT_FILE) 
        print("Choose chance of skipping char in percent (like 0.2)")
        p_change = input()    
        document = Document(INPUT_FILE)
        document = docx_char_scrambler(document,p_change)
        document.save("docx_char_scrambler_" + str(uuid.uuid4()) + ".docx")
    val = input("Finished!")


main()
