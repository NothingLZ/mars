#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 1999-2018 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np

from mars.tensor.expressions.random import RandomState, beta, rand, choice, multivariate_normal, randint, randn
from mars.tensor.expressions.datasource import tensor as from_ndarray
from mars.tensor.expressions.tests.test_core import TestBase


class Test(TestBase):
    def testRandomSerialize(self):
        arr = RandomState(0).beta([[2, 3]], from_ndarray([[4, 6], [5, 2]], chunk_size=2),
            chunk_size=1, size=(3, 2, 2)).tiles()
        chunk = arr.chunks[0]

        self.assertEqual(chunk.op.dtype, np.dtype('f8'))

        serials = self._pb_serial(chunk)
        chunk2 = self._pb_deserial(serials)[chunk.data]

        self.assertEqual(chunk.index, chunk2.index)
        state, state2 = chunk.op.state, chunk2.op.state
        self.assertTrue(np.array_equal(state.keys, state2.keys))

    def testRandom(self):
        arr = rand(2, 3)

        self.assertIsNotNone(arr.dtype)

        arr = beta(1, 2, chunk_size=2).tiles()

        self.assertEqual(arr.shape, ())
        self.assertEqual(len(arr.chunks), 1)
        self.assertEqual(arr.chunks[0].shape, ())
        self.assertEqual(arr.chunks[0].op.dtype, np.dtype('f8'))

        arr = beta([1, 2], [3, 4], chunk_size=2).tiles()

        self.assertEqual(arr.shape, (2,))
        self.assertEqual(len(arr.chunks), 1)
        self.assertEqual(arr.chunks[0].shape, (2,))
        self.assertEqual(arr.chunks[0].op.dtype, np.dtype('f8'))

        arr = beta([[2, 3]], from_ndarray([[4, 6], [5, 2]], chunk_size=2),
                   chunk_size=1, size=(3, 2, 2)).tiles()

        self.assertEqual(arr.shape, (3, 2, 2))
        self.assertEqual(len(arr.chunks), 12)
        self.assertEqual(arr.chunks[0].op.dtype, np.dtype('f8'))

    def testChoice(self):
        t = choice(5, chunk_size=1)
        self.assertEqual(t.shape, ())
        t.tiles()
        self.assertEqual(t.nsplits, ())
        self.assertEqual(len(t.chunks), 1)

        t = choice(5, 3, chunk_size=1)
        self.assertEqual(t.shape, (3,))
        t.tiles()
        self.assertEqual(t.nsplits, ((1, 1, 1),))

        t = choice(5, 3, replace=False)
        self.assertEqual(t.shape, (3,))

    def testMultivariateNormal(self):
        mean = [0, 0]
        cov = [[1, 0], [0, 100]]

        t = multivariate_normal(mean, cov, 5000, chunk_size=500)
        self.assertEqual(t.shape, (5000, 2))
        self.assertEqual(t.op.size, (5000,))

        t.tiles()
        self.assertEqual(t.nsplits, ((500,) * 10, (2,)))
        self.assertEqual(len(t.chunks), 10)
        c = t.chunks[0]
        self.assertEqual(c.shape, (500, 2))
        self.assertEqual(c.op.size, (500,))

    def testRandint(self):
        arr = randint(1, 2, size=(10, 9), dtype='f8', density=.01, chunk_size=2).tiles()

        self.assertEqual(arr.shape, (10, 9))
        self.assertEqual(len(arr.chunks), 25)
        self.assertEqual(arr.chunks[0].shape, (2, 2))
        self.assertEqual(arr.chunks[0].op.dtype, np.float64)
        self.assertEqual(arr.chunks[0].op.low, 1)
        self.assertEqual(arr.chunks[0].op.high, 2)
        self.assertEqual(arr.chunks[0].op.density, .01)

    def testUnexpectedKey(self):
        with self.assertRaises(ValueError):
            rand(10, 10, chunks=5)

        with self.assertRaises(ValueError):
            randn(10, 10, chunks=5)
