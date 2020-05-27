import unicodedata
import csv, string

# MILESTONES
milestones = []
milestone_file = "milestones.csv"

try:
    with open(milestone_file, 'rt', encoding='utf-8-sig') as csvfile: #sig <-> BOM
        milestones = []
        reader = csv.reader(csvfile)
        for row in reader:
            milestones.extend(row)
    print("Milestones (" + str(len(milestones)) + "):")
    print(milestones)
except EnvironmentError:
    print("ERROR File Not Found: %s" % milestone_file)


# ABBREVIATIONS
abbr_file = "abbr.csv"
abbr_table = []

try:
    with open(abbr_file, 'rt', encoding='utf-8-sig') as csvfile: #sig <-> BOM
        reader = csv.DictReader(csvfile, delimiter = '\t')
        for row in reader:
            abbr_table.append(row)
        print("Found " + str(len(abbr_table)) + " entries in the abbreviation expansion table (" + abbr_file + ")")

        string = "".join(item['abbr'] + "->" + item['expan'] + "\n" for item in abbr_table) #item['abbr'] + "->" + item['expan']
        #print(string)
except IOError:
    print("Warning: No abreviation-expansion file found (Expected file: <" + abbr_file + ">). Proceeding without...");

def remove_diacritics(input_str):
    #nfkd_form = unicodedata.normalize('NFKD', input_str)
    #return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    output_str = ""
    for c in input_str:
        if not unicodedata.combining(c): # and (c != u"\u1FBD")): # GREEK KORONIS
            output_str += c;
        elif (c == u"\u0345"): # iota subscript, COMBINING GREEK YPOGEGRAMMENI
            output_str += u"\u03B9" # iota adscript
    output_str = unicodedata.normalize('NFKD', output_str)
    return u"".join([c for c in output_str  if not unicodedata.combining(c)])

def is_punctuation(input_char):
    return unicodedata.category(input_char).startswith('P')

def remove_punct(input_str):
    return u"".join([c for c in input_str if not is_punctuation(c)])

def lowercase_noacc_nopunct(input_str):
    return remove_diacritics(remove_punct(input_str).lower());

def expand_abbr(input_str):
    for row in abbr_table:
        #print(row['abbr'] + " vs. " + input_str)
        if lowercase_noacc_nopunct(row['abbr']) == input_str:
            #print("expansion!!!")
            return row['expan']
    return input_str

def normalise(token):
    if not 'n' in token or token["n"] is None:
        if 't' in token:
            token["n"] = token["t"]
    token["n"] = lowercase_noacc_nopunct(token["n"])
    #token["n"] = remove_diacritics(token["t"]);

    #if abbr

    if (token["t"] is not None) and ('<abbr ' in token["t"]):
        token["n"] = expand_abbr(token["n"])
        # now, normalise the expansion!
        token["n"] = lowercase_noacc_nopunct(token["n"]);

    #avoid Empty token error in CollateX
    if (token["n"] == ""):
        token["n"] = " "

    token['normal_form'] = token['n'] # create a copy in 'normal_form' for Stemmaweb, because the latter ignores 'n'
    return token

def display_char_names(input_str):
    for c in input_str:
        print(unicodedata.name(c) + " ; category:" + unicodedata.category(c) + "; is punctuation: " + str(is_punctuation(c)))

# # Tests
# print(string.punctuation)
#
# print(remove_diacritics(remove_punct("ὠμολόγει")).lower())
# print(remove_diacritics(remove_punct("βασιλείαν·")).lower())
# print(remove_diacritics(remove_punct("hebraicȩ")).lower())
# print(remove_diacritics(remove_punct("quȩ,")).lower())
# print(remove_diacritics(lowercase_noacc_nopunct("χυ.")))
# print(remove_diacritics(remove_punct("ἁγίου")))
# print(remove_diacritics(remove_punct("ῳ")))
# print(remove_diacritics(remove_punct("ᾦ")))
# print(remove_diacritics(remove_punct("ἐπ᾽αὐτὸν")))
# ωμολογει
# βασιλειαν
# hebraice
# que
# χυ
# αγιου
# ωι
# ωι
# επ αυτον

# #
# display_char_names("ἐπ᾽αὐτὸν·")
# # GREEK KORONIS ; category:Sk; is punctuation: False
# # print("Testing")
# # print(normalise({'t':'δι’'}))
# display_char_names("δι’")
# RIGHT SINGLE QUOTATION MARK ; category:Pf; is punctuation: True
# MIDDLE DOT ; category:Po; is punctuation: True
# {'t': 'δι’', 'n': 'δι', 'normal_form': 'δι'}
# RIGHT SINGLE QUOTATION MARK ; category:Pf; is punctuation: True
# print(remove_diacritics(remove_punct("ἐπ᾽αὐτὸν")))
# επ αυτον
# print(remove_diacritics(remove_punct("δι’")))
# display_char_names("ἐφ’ἐστῶτα")
# ...
# RIGHT SINGLE QUOTATION MARK ; category:Pf; is punctuation: True

# print(lowercase_noacc_nopunct("ἐπ᾽αὐτὸν·"))
# επ αυτον
# print(lowercase_noacc_nopunct("ἐφ’ἐστῶτα"))
# εφεστωτα
