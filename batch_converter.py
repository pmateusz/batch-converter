#!/usr/bin/env python3
#
# Copyright 2018 Mateusz Polnik
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import concurrent.futures
import glob
import os
import subprocess
import sys
import warnings

import tqdm


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converts multiple files in parallel using 'convert' Linux command line utility.")
    parser.add_argument('glob-pattern')
    parser.add_argument('output-format')
    return parser.parse_args()


def convert(input_file, output_file):
    return subprocess.run(['convert', input_file, output_file], check=True)


if __name__ == '__main__':
    args_ = parse_args()

    glob_pattern = getattr(args_, 'glob-pattern')
    output_format = getattr(args_, 'output-format')

    future_args = []
    for file_path in glob.glob(glob_pattern):
        file_name = os.path.basename(file_path)
        base_file_name, file_ext = os.path.splitext(file_name)
        input_file = os.path.abspath(file_path)
        output_file = os.path.abspath(base_file_name + '.' + output_format)
        future_args.append((input_file, output_file))

    conversion_failures = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        queue = {executor.submit(convert, *args): args for args in future_args}
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', '', tqdm.TqdmSynchronisationWarning)
            for future in tqdm.tqdm(queue, desc='Converting {0} files:'.format(len(queue)), unit='files', leave=False):
                input_file, output_file = queue[future]
                try:
                    data = future.result()
                    if not os.path.isfile(output_file):
                        conversion_failures.append(input_file)
                except Exception as ex:
                    conversion_failures.append(input_file)

    if conversion_failures:
        conversion_failures.sort()
        print('Failed to process the following files:', (',' + os.linesep).join(conversion_failures), file=sys.stderr)
