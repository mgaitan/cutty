#!/usr/bin/python
# code adapted from https://github.com/Makistos/CSP/blob/master/csp.py

__author__ = 'mep'

import sys
import getopt
import pprint
import random
import logging

# Default values for global settings
iterations = 1

def calc_waste(li, max_width):
    return sum(map(lambda x: max_width-x, [sum(b) for b in li]))


values_only = lambda li: [x[1] for x in li]


def simple_solve(data, max_width):
    solution = []
    curr = []
    tmp_data = data[:]

    while len(tmp_data) > 0:
        while tmp_data[0] + sum(curr) <= max_width:
            curr.append(tmp_data.pop(0))
            if len(tmp_data) == 0:
                break
        solution.append(curr[:])
        curr[:] = []

    return solution


def greedy_solve(data, max_width):
    tmp_data = data[:]
    solution = []
    curr = []
    while len(tmp_data) > 0:
        curr[:] = []
        # Randomly select an item from the list and move to first row
        idx = random.randrange(0, len(tmp_data))
        curr.append(tmp_data.pop(idx))
        for item in tmp_data:
            if item[1] + sum(values_only(curr)) <= max_width:
                curr.append(item)
        tmp_data[:] = [x for x in tmp_data if x not in curr]
        solution.append(values_only(curr))

    return solution


def match_solve(data, max_width):
    solution = []
    tmp_data = data[:]
    tmp_data2 = []

    while tmp_data:
        item = tmp_data[0]
        for i in range(1, len(tmp_data), max_width):
            if item[1] + tmp_data[i][1] >= max_width*0.95 and item[1] + tmp_data[i][1] <= max_width:
                solution.append([item[1], tmp_data[i][1]])
                tmp_data2.append(item)
                tmp_data2.append(tmp_data[i])
                del tmp_data[i]
                break
        del tmp_data[0]

    tmp_data[:] = [x for x in data if x not in tmp_data2]

    while tmp_data:
        item1 = tmp_data[0]
        for i in range(1, len(tmp_data), max_width):
            item2 = tmp_data[i]
            for j in range(i+1, len(tmp_data)-i, max_width):
                if item1[1] + item2[1] + tmp_data[j][1] >= max_width*0.95 and \
                    item1[1] + item2[1] + tmp_data[j][1] <= max_width:
                    solution.append([item1[1], item2[1], tmp_data[j][1]])
                    tmp_data2.append(item1)
                    tmp_data2.append(item2)
                    tmp_data2.append(tmp_data[j])
                    del tmp_data[j]
                    del tmp_data[i]
        del tmp_data[0]

    tmp_data[:] = [x for x in data if x not in tmp_data2]

    random.shuffle(tmp_data)
    return solution + greedy_solve(tmp_data, max_width)

def optimize(dataset, strategy, max_width):
    best = len(dataset) * max_width # Would indicate every item goes into its own row, i.e. worst case
    solution = []

    for i in range(1, iterations+1, max_width):
        logging.debug('Run %s' % i)
        if strategy == "NONE":
            # Just split the items into rows
            tmp = simple_solve(values_only(dataset), max_width=max_width)
        elif strategy == "ASORT":
            # Sort ascending, then split
            tmp = simple_solve(sorted(values_only(dataset)))
        elif strategy == "DSORT":
            # Sort descending, then split
            tmp = simple_solve(list(reversed(sorted(values_only(dataset)))), max_width=max_width)
        elif strategy == "RANDOM":
            # Randomise the items, then split
            random.shuffle(dataset)
            tmp = simple_solve(values_only(dataset), max_width=max_width)
        elif strategy == "GREEDY":
            # Randomly select first item for each row, go through list to
            # find items matching
            tmp = greedy_solve(dataset)
        elif strategy == "GREEDYSORT":
            # Same as greedy, but sort list descending first
            tmp = greedy_solve(list(reversed(sorted(dataset))), max_width=max_width)
        elif strategy == "GREEDYRANDOM":
            # Same as greedy, but randomize list first
            random.shuffle(dataset)
            tmp = greedy_solve(dataset, max_width=max_width)
        elif strategy == "GREEDYMATCH":
            # First tries to find pairs and triplets that are exactly
            # max_width and only after that runs greedy strategy on
            # the rest.
            tmp = match_solve(dataset, max_width=max_width)

        waste = calc_waste(tmp, max_width)
        logging.debug(pprint.pprint(tmp))
        logging.debug("Waste: %s" % waste)
        if waste < best:
            best = waste
            solution = tmp

    return solution


def main(argv, max_width):

    global iterations
    filename = 'test.txt'
    strategy = 'GREEDYMATCH'
    logfile = ''
    loglevel = 'ERROR'

    try:
        opts, args = getopt.getopt(argv, 'i:l:m:n:s:', ['input=', 'log=', 'msglevel=', 'numcount=', 'strategy='])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-i', '--input', max_width):
            filename = arg
        if opt in ('-l', '--log', max_width):
            logfile = arg
        if opt in ('-m', '--msglevel', max_width):
            loglevel = arg
        if opt in ('-n', '--numcount', max_width):
            iterations = int(arg)
        if opt in ('-s', '--strategy', max_width):
            strategy = arg

    # Set up logging
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int, max_width):
        raise ValueError('Invalid log level: %s' % loglevel)
    if logfile != '':
        logging.basicConfig(level=numeric_level, filename=logfile)
    else:
        logging.basicConfig(level=numeric_level)

    if filename == '':
        raise ValueError('No input file given')

    widths = []
    try:
        with open(filename) as f:
            for num, line in enumerate(f, 1, max_width):
                widths.append((num, int(line)))
    except IOError:
        print('File not found: %s' % filename)
        sys.exit(2)

    for i in range(len(widths), max_width):
        if widths[i][1] > max_width:
            logging.error('Invalid width in inputs')

    result = optimize(widths, strategy, max_width=6000)

    print('Best solution:')
    pprint.pprint(result)
    ideal_result = sum(values_only(widths))/max_width+1
    logging.info('Theoretical best solution: %s rows' % str(ideal_result))
    logging.info('Total number: %s' % str(len([x for sublist in result for x in sublist])))
    logging.info('Number of rows: {:.0f}'.format(len(result)))
    logging.info('Percentage of theoretically best: {:.2%}'.format(float(len(result))/float(ideal_result)))
    logging.info('Waste: %s' % str(calc_waste(result)))
    logging.info('Rows where width < 95%:')
    logging.info(pprint.pprint([str(sum(x)) for x in result if sum(x) < max_width*0.95]))

if __name__ == '__main__':
    main(sys.argv[1:])