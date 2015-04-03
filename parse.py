# -*- encoding: utf-8 -*-
__author__ = 'tla'

import json
import re
import sys
from lxml import etree
from warnings import warn

# The JSON file is a Shared Canvas specification. It has a series of sequences
# (should be 1 sequence), and each sequence has a set of canvases, each of
# which is a page.


def from_sc(jsondata):
    """Extract the textual transcription from the Shared Canvas data."""
    if len(jsondata['sequences']) > 1:
        warn("Your data has more than one sequence. Check to see what's going on.", UserWarning)
    pages = jsondata['sequences'][0]['canvases']
    notes = []
    columns = {}
    xmlstring = ''
    for page in pages:
        pn = re.sub('^[^\d]+(\d+\w)\.jpg', '\\1', page['label'])
        thetext = []
        xval = 0
        for line in page['resources']:
            # TODO motivation: oa:commenting -> it needs to be a note!
            if line['resource']['@type'] == 'cnt:ContentAsText':
                transcription = line['resource']['cnt:chars']
                if len(transcription) == 0:
                    continue
                if line['motivation'] == 'sc:painting':
                    # First see if this line even has any text.
                    # Get the column y value and see if we are starting a new column.
                    coords = re.match('^.*#xywh=-?(\d+)', line['on'])
                    if coords is None:
                        raise ValueError('Could not find the coordinates for line %s' % line['@id'])
                    if xval < int(coords.group(1)):
                        # Start a new 'column' in thetext.
                        thetext.append([])
                        xval = int(coords.group(1))
                    # Get the line ID, for later attachment of notes.
                    lineid = re.match('^.*line/(\d+)$', line['@id'])
                    if lineid is None:
                        raise ValueError('Could not find a line ID on line %s' % json.dump(line))
                    thetext[-1].append((lineid.group(1), transcription))
                elif line['motivation'] == 'oa:commenting':
                    lineid = re.match('^.*line/(\d+)$', line['on'])
                    if lineid is None:
                        raise ValueError('Could not find a line ID on comment %s' % json.dump(line))
                    notes.append((lineid.group(1), transcription))
        # Spit out the text
        if len(thetext):
            xmlstring += '<pb n="%s"/>\n' % pn
            for cn, col in enumerate(thetext):
                if len(thetext) > 1:
                    xmlstring += '<cb n="%d"/>\n' % (cn+1)
                for ln, line in enumerate(col):
                    xmlstring += '<lb xml:id="l%s" n="%d"/>%s\n' % (line[0], ln+1, line[1])
            # Keep track of the number of columns.
            if len(thetext) in columns:
                columns[len(thetext)].append(pn)
            else:
                columns[len(thetext)] = [pn]
    # and then add the notes.
    for n in notes:
        xmlstring += '<note type="transcriptional" target="#l%s">%s</note>\n' % n
    # Report how many columns per page.
    for n in sorted(columns.keys()):
        print("%d columns for pages %s\n" % (n, " ".join(columns[n])), file=sys.stderr)
    return "<body><ab>%s</ab></body>" % xmlstring


def xmlify(txdata):
    """Take the extracted XML structure of from_sc and make sure it is
    well-formed. Also fix any shortcuts, e.g. for the glyph tags."""
    try:
        content = etree.fromstring(txdata)
    except etree.XMLSyntaxError as e:
        print("Parsing error in the JSON: %s" % e.msg)
        print("Full string was %s" % txdata)
        return

    # Now fix the glyph references.
    glyphs_seen = {}
    # LATER get this hard-coded list into a settings file.
    glyph_correction = {
        'the': 'թե',
        'thE': 'թէ',
        'und': 'ընդ',
        'thi': 'թի',
        'asxarh': 'աշխարհ',
        'pt': 'պտ',
        'yr': 'յր',
        'orpes': 'որպէս',
    }
    for glyph in content.xpath('//g'):
        # Find the characters that we have glyph-marked. It could have been done
        # in a couple of different ways.
        gchars = ''
        gtext_explicit = ''
        if glyph.get('ref'):
            gchars = glyph.get('ref')
            if gchars.find('#') == 0:
                gchars = gchars[1:]
        if glyph.text:
            if gchars == '':
                gchars = glyph.text
            else:
                gtext_explicit = True
        if gchars in glyph_correction:
            gchars = glyph_correction[gchars]
        # Now figure out what the reference is for this glyph. Make the
        # XML element if necessary.
        if gchars not in glyphs_seen:
            try:
                glyphs_seen[gchars] = get_glyph(gchars)
            except ValueError as e:
                print("In g element %s:" % etree.tostring(glyph, encoding='unicode', with_tail=False), file=sys.stderr)
                raise e
        gref = '#%s' % glyphs_seen[gchars].get('{http://www.w3.org/XML/1998/namespace}id')
        # Finally, fix the 'g' element here so that it is canonical.
        glyph.set('ref', gref)
        if not gtext_explicit:
            glyph.text = gchars

    for el in content.xpath('//corr'):
        el.tag = 'subst'
    # We should be using 'rend' and not 'type' for the subst and del tags.
    for edit in content.xpath('//subst | //del'):
        if edit.get('type'):
            rend = edit.get('type')
            edit.set('rend', rend)
            edit.attrib.pop('type')

    # And 'certainty' attributes have to have the value 'high, 'medium', or 'low'.
    for el in content.xpath('//*[@cert]'):
        certval = el.get('cert')
        if re.match('^\d+$', certval):
            if int(certval) > 40:
                el.set('cert', 'medium')
            else:
                el.set('cert', 'low')

    return tei_wrap(content, sorted(glyphs_seen.values(), key=lambda x: x.get('{http://www.w3.org/XML/1998/namespace}id')))


def get_glyph(gname):
    """Returns a TEI XML 'glyph' element for the given string."""
    # LATER get this hard-coded list into a settings file.
    armenian_glyphs = {
        'աշխարհ': ('asxarh', 'ARMENIAN ASHXARH SYMBOL'),
        'ամենայն': ('amenayn', 'ARMENIAN AMENAYN SYMBOL'),
        'որպէս': ('orpes', 'ARMENIAN ORPES SYMBOL'),
        'երկիր': ('erkir', 'ARMENIAN ERKIR SYMBOL'),
        'երկին': ('erkin', 'ARMENIAN ERKIN SYMBOL'),
        'ընդ': ('und', 'ARMENIAN END SYMBOL'),
        'ըստ': ('ust', 'ARMENIAN EST SYMBOL'),
        'պտ': ('ptlig', 'ARMENIAN PEH-TIWN LIGATURE'),
        'թե': ('techlig', 'ARMENIAN TO-ECH LIGATURE'),
        'թի': ('tinilig', 'ARMENIAN TO-INI LIGATURE'),
        'թէ': ('tehlig', 'ARMENIAN TO-EH LIGATURE'),
        'էս': ('eslig', 'ARMENIAN EH-SEH LIGATURE'),
        'ես': ('echslig', 'ARMENIAN ECH-SEH LIGATURE'),
        'յր': ('yrlig', 'ARMENIAN YI-REH LIGATURE'),
        'զմ': ('zmlig', 'ARMENIAN ZA-MEN LIGATURE'),
        'թգ': ('tglig', 'ARMENIAN TO-GIM LIGATURE'),
        'ա': ('avar', 'ARMENIAN AYB VARIANT'),
        'հ': ('hvar', 'ARMENIAN HO VARIANT'),
        'յ': ('yabove', 'ARMENIAN YI SUPERSCRIPT VARIANT')
    }
    if gname not in armenian_glyphs:
        raise ValueError("Glyph %s not recognized" % gname)

    glyph_el = etree.Element('glyph')
    glyph_el.set('{http://www.w3.org/XML/1998/namespace}id', '%s' % armenian_glyphs[gname][0])
    etree.SubElement(glyph_el, 'glyphName').text = armenian_glyphs[gname][1]
    etree.SubElement(glyph_el, 'mapping').text = gname
    return glyph_el


def tei_wrap(content, glyphs):
    """Wraps the content, and the glyphs that were found, into TEI XML format."""
    # First make the skeleton
    tei = etree.Element('TEI')
    file_desc = etree.SubElement(etree.SubElement(tei, 'teiHeader'), 'fileDesc')
    etree.SubElement(etree.SubElement(file_desc, 'titleStmt'), 'title').text = 'This is the title'
    etree.SubElement(etree.SubElement(file_desc, 'publicationStmt'), 'p').text = 'This is the publication statement'
    etree.SubElement(etree.SubElement(file_desc, 'sourceDesc'), 'p').text = 'This is the source description'
    # Then add the glyphs we used
    etree.SubElement(etree.SubElement(tei.find('teiHeader'), 'encodingDesc'), 'charDecl').extend(glyphs)
    # Then add the content.
    etree.SubElement(tei, 'text').append(content)
    # Finally, set the appropriate namespace and schema.
    tei.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    tei_doc = etree.ElementTree(tei)
    schema = etree.ProcessingInstruction('xml-model', 'href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"')
    tei.addprevious(schema)
    return tei_doc


if __name__ == '__main__':
    with open(sys.argv[1]) as jfile:
        msdata = json.load(jfile)
    parsed = from_sc(msdata)
    xmltree = xmlify(parsed)
    if xmltree is not None:
        sys.stdout.buffer.write(etree.tostring(xmltree, encoding='utf-8', pretty_print=True, xml_declaration=True))