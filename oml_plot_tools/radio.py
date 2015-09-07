#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is a part of IoT-LAB oml-plot-tools
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


""" plot_oml_radio.py

plot oml filename [-tbeaplh] -i <filename> or --input=<filename>

for time verification --time or -t
for begin sample --begin=<sample_beg> or -b <sample_beg>
for end sample --end=<sample_end> or -e <sample_end>
for label title plot --label=<title> or -l <title>
for plot in one window --all or -a
for plot in separate windows --plot or -p
for help use --help or -h
"""

# disabling pylint errors 'E1101' no-member, false positive from pylint
# pylint:disable=I0011,E1101

import sys
import getopt
import numpy as np
import matplotlib.pyplot as plt

FIELDS = {'type': 1, 't_s': 3, 't_us': 4, 'channel': 5, 'rssi': 6}


def oml_load(filename):
    """ Load iot-lab om file

    Parameters:
    ------------
    filename: string
              oml filename

    Returns:
    -------
    data : numpy array
    [oml_timestamp 2 count timestamp_s timestamp_us channel rssi]


    >>> from StringIO import StringIO
    >>> oml_load(StringIO('\\n' * 10 + '0 2\\n' + '1 2\\n'))
    array([[ 0.,  2.],
           [ 1.,  2.]])

    # error cases
    >>> sys.stderr = sys.stdout  # hide stderr output
    >>> oml_load('/invalid/file/path')
    Traceback (most recent call last):
    SystemExit: 2

    >>> oml_load(StringIO('\\n' * 10 + 'invalid_content'))
    Traceback (most recent call last):
    SystemExit: 4

    # Not enough lines to skiprows
    # Raises IOError on python2.6 and StopIteration in python2.7
    >>> oml_load(StringIO('1 2 3'))  # doctest:+ELLIPSIS
    Traceback (most recent call last):
    SystemExit: ...

    # invalid oml 'type' file
    >>> oml_load(StringIO('\\n' * 10 + '0 1\\n' + '1 1\\n'))
    Traceback (most recent call last):
    SystemExit: 5

    >>> sys.stderr = sys.__stderr__

    """
    try:
        data = np.genfromtxt(filename, skip_header=10, invalid_raise=False)
    except IOError as err:
        sys.stderr.write("Error opening oml file:\n{0}\n".format(err))
        sys.exit(2)
    except (ValueError, StopIteration) as err:
        sys.stderr.write("Error reading oml file:\n{0}\n".format(err))
        sys.exit(3)

    # Empty 'parsing' makes type verification fail
    if np.all(np.isnan(data)):
        sys.stderr.write("Error non oml file\n")
        sys.exit(4)

    # Type oml file verification
    for typ in data[:, FIELDS['type']]:
        if typ != 2:
            print "Error non radio type oml file"
            sys.exit(5)

    return data


def oml_channels_set(data):
    """ lists radio channels used in data

    Parameters:
    ------------
    data: numpy array
      [oml_timestamp 1 count timestamp_s timestamp_us power voltage current]

    Returns:
    --------
    channels_set : a set of int channel
    """

    channels_set = set([])
    for radio_meas in data:
        channel = str(radio_meas[FIELDS['channel']])
        if channel not in channels_set:
            channels_set.add(channel)

    return channels_set


def oml_separate_plot(data, title):
    """ Plot iot-lab oml all data

    Parameters:
    ------------
    data: numpy array
      [oml_timestamp 1 count timestamp_s timestamp_us power voltage current]
    title: string
       title of the plot
    """
    channels_set = oml_channels_set(data)

    for channel in channels_set:
        plt.figure()
        plt.grid()
        channel = int(float(channel))
        plt.title(title + " Channel " + str(channel))
        data_channel = data[data[:, FIELDS['channel']] == channel]
        time_channel = (data_channel[:, FIELDS['t_s']] +
                        data_channel[:, FIELDS['t_us']] / 1e6)
        plt.plot(time_channel, data_channel[:, FIELDS['rssi']])
        plt.ylabel('RSSI (dBm)')

    return


def oml_all_plot(data, title):
    """ Plot iot-lab oml all data

    Parameters:
    ------------
    data: numpy array
      [oml_timestamp 1 count timestamp_s timestamp_us power voltage current]
    title: string
       title of the plot
    """

    channels_set = oml_channels_set(data)
    nbplots = len(channels_set)

    if nbplots > 0:
        plt.figure()
        i = 0
        for channel in channels_set:
            i = i + 1
            channel_plot = plt.subplot(nbplots, 1, i)
            channel_plot.grid()
            channel = int(float(channel))
            plt.title(title + " Channel " + str(channel))
            data_channel = data[data[:, FIELDS['channel']] == channel]
            time_channel = (data_channel[:, FIELDS['t_s']] +
                            data_channel[:, FIELDS['t_us']] / 1e6)
            channel_plot.plot(time_channel, data_channel[:, FIELDS['rssi']])
            plt.ylabel('RSSI (dBm)')

    return


def oml_plot(data, title, labely, channel):
    """ Plot iot-lab oml data

    Parameters:
    ------------
    data: numpy array
      [oml_timestamp 1 count timestamp_s timestamp_us power voltage current]
    title: string
       title of the plot
    channel: number
       channel to plot 5 = power, 6 = voltage, 7 = current
    """
    timestamps = data[:, FIELDS['t_s']] + data[:, FIELDS['t_us']] / 1e6

    plt.figure()
    plt.title(title)
    plt.grid()
    plt.plot(timestamps, data[:, FIELDS[channel]])
    plt.xlabel('Sample Time (sec)')
    plt.ylabel(labely)

    return


def oml_clock(data):
    """ Clock time plot and verification

    Parameters:
    ------------
    data: numpy array
      [oml_timestamp 1 count timestamp_s timestamp_us power voltage current]
    echd : int
       sample count begin
    echf : int
       sample count end
    """
    plt.figure()
    plt.title("Clock time verification")
    plt.grid()
    time = data[:, FIELDS['t_s']] + data[:, FIELDS['t_us']] / 1e6
    clock = np.diff(time) * 1000  # pylint:disable=I0011,E1101
    plt.plot(clock)

    print 'NB Points      =', len(time)
    print 'Duration    (s)=', time[-1] - time[0]
    print 'Steptime    (ms)=', 1000 * (time[-1] - time[0]) / len(time)
    print 'Time to', time[0], 'From', time[-1]
    print 'Clock mean (ms)=', np.mean(clock)  # pylint:disable=I0011,E1101
    print 'Clock std  (ms)=', np.std(clock)  # pylint:disable=I0011,E1101
    print 'Clock max  (ms)=', np.max(clock)
    print 'Clock min  (ms)=', np.min(clock)
    return


def usage():
    """Usage command print
    """
    print "Usage"
    print __doc__


# R0912:too-many-branches
def main():  # pylint:disable=R0912
    """ Main command
    """
    options = []
    filename = ""
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "i:htapb:e:l:",
                                ["input=", "help", "time", "all", "plot",
                                 "begin=", "end=", "label="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    s_beg = 0
    s_end = -1
    title = ""
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--input"):
            filename = arg
        elif opt in ("-l", "--label"):
            title = arg
        elif opt in ("-t", "--time"):
            options.append("-t")
        elif opt in ("-b", "--begin"):
            s_beg = int(arg)
        elif opt in ("-e", "--end"):
            s_end = int(arg)
        elif opt in ("-a", "--all"):
            options.append("-a")
        elif opt in ("-p", "--plot"):
            options.append("-p")

    if len(filename) == 0:
        usage()
        sys.exit(2)

    # Load file
    data = oml_load(filename)[s_beg:s_end, :]
    # Plot in a single window
    if "-a" in options:
        oml_all_plot(data, title)
    # Plot in several windows
    if "-p" in options:
        oml_separate_plot(data, title)
    # Clock verification
    if "-t" in options:
        oml_clock(data)
    plt.show()


if __name__ == "__main__":
    main()
