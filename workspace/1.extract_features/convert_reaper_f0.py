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
import numpy as np


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
    in_filename = sys.argv[1]
    out_f0_filename = sys.argv[2]
    out_lf0_filename = sys.argv[3]

    inf_float = -1.0e+10

    with open(in_filename) as in_file:
        vuv_list = []; f0_list = []
        for i, line in enumerate(in_file.readlines()):
            if i < 7: continue  # skip EST_FILE Track
            _, vuv, f0= line.strip().split()
            vuv_list.append(int(vuv))
            f0_list.append(float(f0))
        vuv_mat = np.array(vuv_list, dtype=np.int32)
        f0_mat = np.array(f0_list, dtype=np.float32)

        f0_mat[vuv_mat == 0] = 0
        write_binary_file(f0_mat, out_f0_filename)

        lf0_mat = np.array(f0_mat)
        for i in range(lf0_mat.shape[0]):
            if lf0_mat[i] == 0:
                lf0_mat[i] = inf_float
            else:
                lf0_mat[i] = np.log(lf0_mat[i])
        write_binary_file(lf0_mat, out_lf0_filename)
