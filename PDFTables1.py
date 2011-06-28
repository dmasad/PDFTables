""" 
PDF Table Extractor
David Masad
06/27/11

Work based on
http://denis.papathanasiou.org/?p=343
"""

# Base Includes
from pdfminer.pdfparser import PDFParser, PDFDocument, PDFNoOutlines
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage

# Other Includes
import csv

def open_pdf(filepath):
	""" Read in a PDF file, create a PDFMiner document object and return it. """
	fp = open(filepath, 'rb') # Open the file
	parser = PDFParser(fp) # Create the parser
	doc = PDFDocument() # Create the document object
	parser.set_document(doc)
	doc.set_parser(parser)
	doc.initialize('')
	
	return doc

def parse_pages(doc):
	"""Returns a  list of layout objects."""
	resource_manager = PDFResourceManager()
	laparams = LAParams()
	device = PDFPageAggregator(resource_manager, laparams=laparams)
	interpreter = PDFPageInterpreter(resource_manager, device)
	layout_list = []
	
	for page in doc.get_pages():
		interpreter.process_page(page)
		layout = device.get_result()
		layout_list.append(layout)
	
	return layout_list

def extract_plaintext(layout):
	"""Extracts the plain text from a Layout object"""
	plaintext = []
	
	for lt_obj in layout._objs:
		if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
			#If lt_obj is a text object
			plaintext.append(lt_obj.get_text())
		elif isinstance(lt_obj, LTFigure):
			# an LTFigure contains other objects
			plaintext.append(extract_plaintext(lt_obj))
	return plaintext

def extract_textobjs(layout, initial_textobjs = []):
    """Extracts the text objects from Layout object """
    textobjs = initial_textobjs
    for lt_obj in layout._objs:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            textobjs.append(lt_obj)
        elif isinstance(lt_obj, LTFigure):
            textobjs = extract_textobjs(lt_obj, textobjs)
    return textobjs 

def output_textobjs_table(textobs, outfile):
    f = open(outfile, "wb")
    writer = csv.writer(f)
    
    for obj in textobs:
        row = []
        for coord in obj.bbox:
            row.append(coord) # Write out the four box corners
        row.append(obj.get_text()) # Write the object text.
        writer.writerow(row)
    f.close()

def sort_textobjs(textobs, pct=0.1):
    """Sort the Textobs first into rows, then into columns. """
    
    # Sort the textobs by their y origin.
    sorted_y = sorted(textobs, key=lambda o: o.bbox[1], reverse=True) # Reversed since the y-coords on PDFs seem to be
    rows = [ [sorted_y[0]] ]
    row_y = sorted_y[0].bbox[1] # The variable holding the seed y of the current row.
    
    for box in sorted_y[1:]:
        if row_y*(1.0-pct) < box.bbox[1] < row_y*(1.0+pct): rows[-1].append(box)
        else:
            rows.append([box])
            row_y = box.bbox[1]
    
    for row in rows: row = sorted(row, key=lambda o: o.bbox[0]) # Sort all the rows by X value. 
    return rows
    
            
if __name__ == "__main__":
    doc = open_pdf('/home/dmasad/Test.pdf')
    l = parse_pages(doc)[0]
    textobs = extract_textobjs(l)