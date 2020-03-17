#!/lustre/scratch/software/anaconda-2.4.0/bin/python

# -*- coding: utf-8 -*-
"""
Created on Thu May 16 11:01:35 2019

@author: Efren A. Serra
"""

import datetime
import logging
import numpy as np
import re, sys

LOG = logging.getLogger(__name__)

ISO8061_DATETIME_FRMT = "%Y%m%dT%H00Z"

def filter_lines(f, pattern):
    for i, line in enumerate(f):
        if re.search(pattern, line):
            LOG.info("Keeping %s", line)
            yield line

def is_numeric(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def loadprc_fromtxt(fname, pattern):
    """
    Load PJC data from a text file.

     i] OY_TP_i Number of observation yes when forecast is between the
    ith and i+1th probability thresholds as a proportion of
    the total OY (repeated)

    ii] ON_TP_i Number of observation no when forecast is between the
    ith and i+1th probability thresholds as a proportion of
    the total ON (repeated)
    """
    with open(fname, "r") as fd:
        hdr = fd.readline()
        print hdr
        colno = 0
        colnomap = {}
        for colno,colna in enumerate(hdr.split()):
            colnomap[colna] = colno
        print colnomap
        colnas = []
        colnos = []
        for m in pattern.finditer(hdr):
            print('column: %02d: %s' % (colnomap[m.group(0)],m.group(0)))
            print('string position: %02d-%02d: %s' % (m.start(),m.end(),m.group(0)))
            colnas.append(m.group(0))
            colnos.append(colnomap[m.group(0)])

        try:
            converters = dict(map(lambda k,v: (k,v), colnos, [lambda s: (float(s) if is_numeric(s) else 0.) for n in range(len(colnos))]))
            data=np.loadtxt(filter_lines(fd, re.compile(r"(box_mask).+(>=12.0)")),converters=converters,usecols=tuple(colnos),unpack=True)
        except UserWarning:
            pass

        print(data)
        return data[0::3], data[1::3], data[2::3]

def to_iso8061_datetime(s):
    """Returns datetime from string in ISO8061 format."""
    iso8061_datetime= datetime.datetime.strptime(s, ISO8061_DATETIME_FRMT)
    return iso8061_datetime.strftime("%d %b %Y %HZ")

def main():
    import argparse
    parser = argparse.ArgumentParser(sys.argv)
    parser.add_argument('storm_id', type=str, help='Storm id')
    parser.add_argument('valid_time', type=to_iso8061_datetime, help='YYYYMMDDTHHMMZ formatted date-time-group')
    parser.add_argument('fcst_time', type=to_iso8061_datetime, help='YYYYMMDDTHHMMZ formatted date-time-group')
    parser.add_argument('tau', type=int, help='TAU offset')
    parser.add_argument('in_file', type=str, help='MET .prc input file')
    parser.add_argument('fcst_mdl', type=str, help='Forecast model name')
    parser.add_argument('anal_mdl', type=str, help='Analysis model name')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Set output volume - using this twice will result in even more!'
    )
    args = parser.parse_args()

    if args.verbose > 1:
        log_level = logging.DEBUG
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    log_format = "%(asctime)s %(levelname)s - %(name)s - %(message)s"
    logging.basicConfig(level=log_level, format=log_format)

    try:
        pattern = re.compile(r"(THRESH_\d+|PODY_\d+|POFD_\d+)")
        THRESH,PODY,POFD=loadprc_fromtxt(args.in_file, pattern)
        THRESH = THRESH[:-1]
    except IndexError:
        print("loadprc_fromtxt: {} Not results!".format(pattern.pattern))
        sys.exit(0)

    print(THRESH)
    print(PODY)
    print(POFD)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    nthresh = len(THRESH)
    fig = plt.figure(figsize=(7,7))
    plt.plot(POFD,PODY, '-r^', label='Treshold values')

    x=np.array([i/float(nthresh) for i in range(0,nthresh+1)])
    plt.plot(x, x, '--b', label='No Skill')
    plt.text(0.,-0.2, 'Probability forecast : {}'.format(args.fcst_mdl), horizontalalignment='left')
    plt.text(1.0,-0.2, 'Ground-truth : {}'.format(args.anal_mdl), horizontalalignment='right')
    plt.text(0.8,1.0, '{}'.format(args.storm_id))
    i=0
    for x,y in zip(POFD,PODY):
        label = "{:.1f}".format(THRESH[i])
        plt.annotate(label, # this is the text
                 (x,y), # this is the point to label
                 textcoords="offset points", # how to position the text
                 xytext=(5,-5), # distance from text to points (x,y)
                 ha='left') # horizo
        i = i + 1

    plt.xlabel('False Alarm Rate')
    plt.ylabel('Probability of Detection')
    plt.legend(loc='lower right')
    plt.title('Receiver Operating Characteristic Sig Wave Height GT 12-ft \nVT: {}; Forecast: {} Tau: {}'.format(args.valid_time, args.fcst_time, args.tau))
    plt.savefig('{}_{}-{}_{}_{}_ROC.png'.format(args.storm_id, args.fcst_mdl, args.anal_mdl, args.fcst_time.replace(' ', '_'), args.tau))

if __name__=="__main__":
    main()
