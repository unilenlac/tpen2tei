# Downloaded 2018-03-14 from https://github.com/DHUniWien/moe-data/blob/master/ci/resources/teixml2collatex.py

import logging
import os
import fnmatch
import sys
import pprint
import argparse
import json
import re
import importlib
import statistics
import datetime

from tpen2tei.wordtokenize import Tokenizer


def milestones(configmod):
    """Returns a list of milestones that should be individually collated"""
    if configmod is not None:
        mst = getattr(configmod, "milestones", None)
        #print(mst)
        if mst is not None:
            return mst #VS()
    return []


def normalise(configmod):
    """Returns a function that takes a token and modifies it, or None"""
    if configmod is not None:
        na = getattr(configmod, "normalise", None)
        return na
    return None


def unfinished(configmod):
    """Returns a list of manuscripts that aren't to be collated yet"""
    if configmod is not None:
        unf = getattr(configmod, "unfinished", None)
        if unf is not None:
            return unf()
    return []


def teixml2collatex(milestone, indir, verbose, configmod):
    # list elements are already so
    # that collatex can digest them
    witnesses = []
    skipwit = unfinished(configmod)

    # walk through all available witnesses
    # and look for the current milestone
    #
    # presume: one witness per file
    mslength = []
    missing = []
    for infile in fnmatch.filter (os.listdir (indir), '*.xml'):
        if verbose:
            print ("{}: milestone {} in file: {}".format (
                datetime.datetime.now().strftime ("%a, %d %b %Y %H:%M:%S %z"),
                milestone,
                infile,
            ))

        # get a witness name for display by removing file extensions
        witness_name = re.sub ('-merged', '', infile[:infile.find('.')])
        if witness_name in skipwit:
            if verbose:
                print('skipping unfinished witness %s' % witness_name)
            continue

        # print("Witness: " + infile)
        witness = extract_witness(indir + '/' + infile, milestone, normalise(configmod))

        if witness is not None and witness.get('tokens'):
            # for t in witness.get('tokens'):
            #     print(t)
            #     print(len(t['t']))
            witnesses.append(witness)
            logging.info ('milestone <%s> found in witness file <%s>' % (
                milestone,
                infile,
            ))

            # VS: no layers: we handle corrections as sigle nodes (XML annotation preserved in field 't')
            # # Get the layer witness too
            # layerwit = extract_witness(indir + '/' + infile, milestone, normalise(configmod), True)
            # if layerwit.get('tokens'):
            #     layerwit['id'] += " (a.c.)"
            #     witnesses.append(layerwit)
            # Note the length of the (main) witness
            mslength.append(len(witness.get('tokens')))
        else:
            logging.info ('milestone <%s> not found in witness file <%s>' % (
                milestone,
                infile,
            ))
            missing.append(witness_name)

    # warn and exclude if one of the witnesses seems weirdly longer than
    # the others; it probably indicates a missing milestone marker and can
    # cause SVG generation to hang.
    msmedian = 0
    if mslength:
        msmedian = statistics.median(mslength)
    collation = {"witnesses": []}
    for wit in witnesses:
        if len(wit.get('tokens')) > msmedian + 800:
            print("Witness %s seems too long; excluding it from collation" % wit.get('id'),
                    file=sys.stderr)
        else:
            collation.get("witnesses").append(wit)

    # note on output which files are missing milestones
    if verbose and len(missing) > 0:
        print ("{}: milestone {} not in witnesses: {}".format (
            datetime.datetime.now().strftime ("%a, %d %b %Y %H:%M:%S %z"),
            milestone,
            ' '.join (missing),
        ))
    return collation


def extract_witness (xmlfile, milestone, normalisation, first_layer=False):
    """ returns json
    """

    tokenizer = Tokenizer(
        milestone=milestone,
        normalisation=normalisation,
        first_layer=first_layer,
        id_xpath='//t:msDesc/@xml:id')

    try:
        with open (xmlfile, encoding = 'utf-8') as fh:
            return tokenizer.from_string (fh.read())
    except FileNotFoundError:
        print('file not found: %s' % xmlfile, file=sys.stderr)
    except:
        # print('Caught Python exception trying to tokenise %s; see log' % xmlfile, file=sys.stderr)
        logging.info ('exception type: %s' % sys.exc_info()[0])
        logging.info ('exception value: %s' % sys.exc_info()[1])
        logging.info ('exception trace: %s' % sys.exc_info()[2])


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument (
         "indir",
         help = "input directory t-pen output files",
    )
    parser.add_argument (
        "outdir",
        help = "output directory",
    )
    parser.add_argument (
        "-v",
        "--verbose",
        action = "store_true",
        help = "make output more verbose",
    )
    parser.add_argument (
        "-c",
        "--config",
        help = "module for custom collation logic"
    )

    logging.basicConfig (
        format = '%(asctime)s %(message)s',
        filename = '%s.log' % os.path.basename (sys.argv[0]),
        level = logging.NOTSET,
    )

    args = parser.parse_args()

    configmod = None
    if args.config is not None:
        configpath = os.path.expanduser(args.config)
        sys.path.append(os.path.dirname(configpath))
        configmod = importlib.import_module(os.path.basename(configpath))

    for milestone in milestones(configmod):
        c = teixml2collatex(milestone, args.indir, args.verbose, configmod)
        if c.get ('witnesses'):
            outfile = '%s/milestone-%s.json' % (args.outdir, milestone)

            with open (outfile, 'w', encoding='utf-8') as fh:
                json.dump (
                    c,
                    fh,
                    ensure_ascii = False,
                    indent = 4,
                    check_circular = True,
                )
