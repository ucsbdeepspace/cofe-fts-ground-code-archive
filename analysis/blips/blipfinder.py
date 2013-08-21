import numpy
import pylab
import time

class SignalEndError(ValueError):
    pass

def index_of_max(x):
    """Returns the index of the maximum element of the argument."""
    return numpy.where(x == max(x))[0][0]

def floored_signal( signal, floor ):
    """Puts a floor on the values of the signal."""
    result = signal.copy()
    result[result < floor] = floor
    return result

def zeroed_correlate(x, y):
    """Returns the signals' correlation with their maxes subtracted."""
    return numpy.correlate(x-max(x), y-max(y))

def ask_for_help(signal, show_slice):
    """Asks the user to show roughly where the next blip is."""
    # Close any open figure, so we don't show it.
    pylab.close()
    # Make a new figure and plot/zoom in on the current blip.
    f = pylab.figure()
    pylab.plot(signal)
    f.gca().set_xlim(left=show_slice.start, right=show_slice.stop)
    pylab.show()
    # The user has now moved the window over the next blip.
    # We just have to find the axis limits, and those are the boundaries
    #  of the blip!
    start,stop = f.gca().get_xlim()
    return slice(int(start), int(stop))

def find_repetition( signal, where, offset_guess, offset_error_factor ):
    """Returns the location of a repetition of the given signal slice."""
    max_offset_error = offset_guess * offset_error_factor
    if where.start+offset_guess-max_offset_error > len(signal):
        # There's not enough room for another blip. We've finished the signal.
        raise SignalEndError()

    # We know roughly where the next blip is. Let's cut out that area
    #  and cross-correlate with the current blip.
    an_start = where.start + offset_guess - max_offset_error
    an_stop = where.stop + offset_guess + max_offset_error
    around_next = floored_signal( signal[an_start:an_stop],
                                  min(signal[where]) )
    corr = zeroed_correlate(around_next, signal[where])

    # Okay. Now we have a list of correlation values. We figure that
    # since the blips look pretty similar, the offset with the largest
    # correlation is probably the closest fit.
    best = index_of_max(corr)
    error = best - max_offset_error
    result = slice( where.start + offset_guess + error,
                    where.stop + offset_guess + error )
    if result.stop > len(signal):
        raise SignalEndError()
    return result

def repetitions(signal, first, offset_guess, offset_error_factor,
                ask_threshold=0.5):
    """Yields slices of repetitions of the given signal slice."""
    # s is the slice containing the current blip.
    s = first
    # last_corr is the cross-correlation value between the current blip
    #  and the one before. If the next correlation is significantly smaller
    #  than the last one, we probably didn't get a good match on the blip
    #  shape and we need to ask for help.
    last_corr = 0

    # Now we just (find next blip; yield it; find next; yield; ...)
    #  until we run out of signal.
    while True:
        try:
            # Usually, the program can figure out on its own where the
            #  next blip is.
            next = find_repetition( signal, s, offset_guess,
                                    offset_error_factor )
        except SignalEndError:
            # (We ran out of signal -- found all the blips!)
            break

        else:
            if (ask_threshold is not None):
                # The program might not have found a good match, and
                #  we want it to ask for help if that happens.

                # First, let's figure out whether we get about the right
                #  correlation.
                corr = zeroed_correlate(signal[s], signal[next])
                print corr, last_corr

                if corr < last_corr*ask_threshold:
                    print "Trouble finding next repetition (corr {0} -> {1})."\
                          " Move the viewing window approximately over the"\
                          " next blip, then close the plot."\
                          .format(last_corr, corr)
                    input = ask_for_help(signal, s)
                    # Okay. The user just gave us the rough position of the
                    #  next blip. Let's do some fine-tuning, now that we
                    #  know more or less where it is.
                    next = find_repetition(signal, s, input.start-s.start,
                                           offset_error_factor)
                    corr = zeroed_correlate(signal[s], signal[next])

                # And update the correlation.
                last_corr = corr
            # All right! 'next' is the slice of the next blip. Yield it,
            #  update our guess for the spacing between blips, and keep
            #  on going!
            yield next
            offset_guess = next.start - s.start
            s = next


if __name__ == '__main__':

    # We're being run as a script, which means we want to dump images
    # of blips into image files.

    import optparse, pylab, pyfits, math, os

    # These are the command-line options, in the form
    #  ((short_spec, long_spec),
    #   dict(dest=attribute_name,
    #        help=help_info),
    #   default_value).
    # Other information, like data type, is deduced from that given.
    # I've done it this way to ensure that everything is given a
    #  default value that is (a) displayed by the default help and
    #  (b) consistent with the implementation's default, because nothing
    #  sucks more than incorrect documentation.
    OPTIONS = \
        ( (('-f', '--file'),
           dict(dest='file',
                help='the file to plot data from'),
           '/COFE/Level1/0.5/all_10GHz_v0.5_data.fits'),

          (('-c', '--channel'),
           dict(dest='channel',
                help='the channel to plot data from'),
           1),

          (('-o', '--offset'),
           dict(dest='offset',
                help='number of data points to skip at beginning'),
           450000),

          (('-n', '--num-figs'),
           dict(dest='num_figs',
                help='number of blips to plot'),
           1000),

          (('-i', '--blip-interval'),
           dict(dest='interval',
                help='plot every nth blip'),
           1),

          (('-d', '--dest'),
           dict(dest='dest',
                help='directory to put files in'),
           'blip_images'),

          (('-e', '--error'),
           dict(dest='error',
                help='max error factor in offset'),
           0.4),

          (('-t', '--template'),
           dict(dest='template',
                help='position of first blip, in form "start,stop"'),
           '3000,5000'),

          (('-m', '--mpr'),
           dict(dest='mpr',
                help='measurements per revolution'),
           3000),

          (('-T', '--threshold'),
           dict(dest='threshold',
                help='correlation ratio at which the user is asked for help'),
           0.5)
          )

    parser = optparse.OptionParser()
    for args, kwargs, default in OPTIONS:
        if isinstance(default, bool):
            kwargs['action'] = 'store_' + ('false' if default else 'true')
            kwargs['help'] += ' (done by default)' if default\
                              else ' (not done by default)'
        else:
            kwargs['default'] = default
            kwargs['type'] = type(default).__name__
            kwargs['help'] += ' (default {0!r})'.format(default)

        parser.add_option(*args, **kwargs)
            

    options,args = parser.parse_args()

    # If the destination directory doesn't exist, create it.
    if not os.path.exists(options.dest):
        os.makedirs(options.dest)

    # The number of digits for blip number in the filenames we make:
    num_digits = int(math.log(options.num_figs, 10))+1

    h = pyfits.open(options.file, memmap=True)
    channel_data = h[2+options.channel].data['T']
    signal = channel_data[options.offset:]

    # The given information regarding first blip position,
    #  blip spacing, and margin of error:
    start, end = [int(i) for i in options.template.split(',')]
    where = slice(start, end)
    offset = options.mpr
    error = options.error

    # Okay! Let's generate these slices.
    reps = repetitions(signal, where, offset, error,
                       ask_threshold=options.threshold)
    for i in xrange(options.num_figs):
        for _i in xrange(options.interval):
            rep = reps.next()
        fname = ('{dest}/blip_{i:0{digits}}_{where}.png'
                 .format(dest=options.dest, i=i, digits=num_digits,
                         where=int(rep.start)))
        pylab.clf()
        pylab.plot(signal[rep])
        pylab.gcf().gca().set_ylim(-10, 1)
        pylab.savefig(fname)
        if i%10 == 0:
            print i
            time.sleep(.3)
