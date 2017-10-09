# Copyright 2016 ASLP@NPU.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: npuichigo@gmail.com (zhangyuchao)

import os
import sys
import struct
import numpy as np
import argparse
from scipy import signal


def read_binary_file(filename, dimension=None):
    """Read data from matlab binary file (row, col and matrix).

    Returns:
        A numpy matrix containing data of the given binary file.
    """
    if dimension is None:
        read_buffer = open(filename, 'rb')

        rows = 0; cols= 0
        rows = struct.unpack('<i', read_buffer.read(4))[0]
        cols = struct.unpack('<i', read_buffer.read(4))[0]

        tmp_mat = np.frombuffer(read_buffer.read(rows * cols * 4), dtype=np.float32)
        mat = np.reshape(tmp_mat, (rows, cols))

        read_buffer.close()

        return mat
    else:
        fid_lab = open(filename, 'rb')
        features = np.fromfile(fid_lab, dtype=np.float32)
        fid_lab.close()
        assert features.size % float(dimension) == 0.0,'specified dimension %s not compatible with data'%(dimension)
        features = features[:(dimension * (features.size // dimension))]
        features = features.reshape((-1, dimension))

        return features


def write_binary_file(data, output_file_name, with_dim=False):
    data = np.asarray(data, np.float32)
    fid = open(output_file_name, 'wb')
    if with_dim:
        fid.write(struct.pack('<i', data.shape[0]))
        fid.write(struct.pack('<i', data.shape[1]))
    data.tofile(fid)
    fid.close()


def main():

    if not os.path.exists('prepared_label'):
        os.mkdir('prepared_label')
    if not os.path.exists('prepared_cmp'):
        os.mkdir('prepared_cmp')

    for line in os.listdir('label'):
        filename, _ = os.path.splitext(line.strip())
        print('processing ' + filename)
        sys.stdout.flush()

        label_mat = np.loadtxt(os.path.join('label', filename + '.lab'))
        cmp_mat = read_binary_file(
            os.path.join('cmp', filename + '.cmp'),
            dimension=FLAGS.mgc_dim + FLAGS.lf0_dim + 1 + FLAGS.bap_dim)

        if label_mat.shape[0] <= cmp_mat.shape[0]:
            cmp_mat = cmp_mat[:label_mat.shape[0], :]
        else:
            frame_diff = label_mat.shape[0] - cmp_mat.shape[0]
            rep = np.repeat(cmp_mat[-1:, :], frame_diff, axis=0)
            cmp_mat = np.concatenate([cmp_mat, rep], axis=0)

        frame_num =label_mat.shape[0]

        write_binary_file(
            label_mat,
            os.path.join('prepared_label', filename + '.lab'))

        cmp_context_mat = np.zeros([
            cmp_mat.shape[0], cmp_mat.shape[1] + 2 * FLAGS.f0_context], dtype=np.float32)

        # apply medfilt
        #cmp_context_mat[:, : FLAGS.mgc_dim] = signal.medfilt(
        #    cmp_mat[:, : FLAGS.mgc_dim], kernel_size=(3, 1))
        # apply averfilt
        cmp_context_mat[:, : FLAGS.mgc_dim] = signal.convolve2d(
            cmp_mat[:, : FLAGS.mgc_dim],
            [[1.0 / 3], [1.0 / 3], [1.0 / 3]],
            mode='same', boundary='symm')
        cmp_context_mat[:, FLAGS.mgc_dim] = cmp_mat[:, FLAGS.mgc_dim]

        for i in xrange(-FLAGS.f0_context, FLAGS.f0_context + 1):
            for j in xrange(frame_num):
                index = j + i
                if index < 0:
                    index = 0
                elif index >= frame_num:
                    index = frame_num - 1
                cmp_context_mat[j, FLAGS.mgc_dim + 1 + i + FLAGS.f0_context] = (
                    cmp_mat[index, FLAGS.mgc_dim + 1])

        cmp_context_mat[:, FLAGS.mgc_dim + 1 + 2 * (FLAGS.f0_context) + 1:] = (
            cmp_mat[:, FLAGS.mgc_dim + 1 + FLAGS.lf0_dim:])

        write_binary_file(
            cmp_context_mat,
            os.path.join('prepared_cmp', filename + '.cmp'))


if __name__ == '__main__':
    def _str_to_bool(s):
        """Convert string to bool (in argparse context)."""
        if s.lower() not in ['true', 'false']:
            raise ValueError('Argument needs to be a '
                             'boolean, got {}'.format(s))
        return {'true': True, 'false': False}[s.lower()]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--mgc_dim',
        type=int,
        default=60,
        help='The dimension of mgc.'
    )
    parser.add_argument(
        '--lf0_dim',
        type=int,
        default=1,
        help='The dimension of lf0.'
    )
    parser.add_argument(
        '--bap_dim',
        type=int,
        default=5,
        help='The dimension of bap.'
    )
    parser.add_argument(
        '--f0_context',
        type=int,
        default=4,
        help='The f0 context of output.'
    )
    FLAGS, unparsed = parser.parse_known_args()

    main()
