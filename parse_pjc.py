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

def loadpjc_fromtxt(fname):
    """
    Load PJC data from a text file.

     i] OY_TP_i Number of observation yes when forecast is between the
    ith and i+1th probability thresholds as a proportion of
    the total OY (repeated)

    ii] ON_TP_i Number of observation no when forecast is between the
    ith and i+1th probability thresholds as a proportion of
    the total ON (repeated)
    """
    pattern = re.compile(r"O[Y|N]_TP_\d+")
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
            data=np.loadtxt(filter_lines(fd, re.compile(r"(box_mask).+(>=12.0)")),usecols=tuple(colnos),unpack=True)
        except UserWarning:
            pass

        return [data[i]/(data[i]+data[i+1]) for i in range(0,len(colnas),2)]

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
    parser.add_argument('in_file', type=str, help='MET .pjc input file')
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
        HR=loadpjc_fromtxt(args.in_file)
    except IndexError:
        print("loadpjc_fromtxt: No results!")
        sys.exit(0)

    print(HR)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    nthresh = len(HR)
    x=[(i+1)/float(nthresh) for i in range(nthresh)]
    plt.plot(x,HR, '--ro', label='{}'.format(args.storm_id))
    plt.plot(x,x,)
    plt.xlabel('{} Forecast probability'.format(args.fcst_mdl))
    plt.ylabel('{} Analysis'.format(args.anal_mdl))
    plt.legend(loc='upper left')
    plt.title('Reliability Diagram Sig Wave Height GT 12-ft \nVT: {}; Forecast: {} Tau: {}'.format(args.valid_time, args.fcst_time, args.tau))
    plt.savefig('{}_{}-{}_{}_{}_pjc.png'.format(args.storm_id, args.fcst_mdl, args.anal_mdl, args.fcst_time.replace(' ', '_'), args.tau))

if __name__=="__main__":
    main()
