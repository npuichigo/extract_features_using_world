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


if __name__ == '__main__':

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
            os.path.join('cmp', filename + '.cmp'), dimension=67)
        frame_num = min(label_mat.shape[0], cmp_mat.shape[0])
        write_binary_file(
            label_mat[:frame_num, :],
            os.path.join('prepared_label', filename + '.lab'))
        # f0 context
        f0_context = 4
        cmp_mat = cmp_mat[:frame_num, :]
        cmp_context_mat = np.zeros([cmp_mat.shape[0], cmp_mat.shape[1] + 2 * f0_context], dtype=np.float32)
        # apply medfilt
        #cmp_context_mat[:, : 60] = signal.medfilt(cmp_mat[:, : 60], kernel_size=(3, 1))
        # apply averfilt
        cmp_context_mat[:, : 60] = signal.convolve2d(
            cmp_mat[:, : 60], [[1.0 / 3], [1.0 / 3], [1.0 / 3]], mode='same', boundary='symm')
        cmp_context_mat[:, 60] = cmp_mat[:, 60]
        for i in xrange(-f0_context, f0_context + 1):
            for j in xrange(frame_num):
                index = j + i
                if index < 0:
                    index = 0
                elif index >= frame_num:
                    index = frame_num - 1
                cmp_context_mat[j, 61 + i + f0_context] = cmp_mat[index, 61]
        cmp_context_mat[:, 70:] = cmp_mat[:, 62:]

        write_binary_file(
            cmp_context_mat[:frame_num, :],
            os.path.join('prepared_cmp', filename + '.cmp'))
