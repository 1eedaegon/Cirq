# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import cirq


def test_repr():
    cirq.testing.assert_equivalent_repr(
        cirq.SampleResult(data=pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]],
                                            index=[7, 8],
                                            columns=['a', 'b', 'c'])))


def test_str():
    assert str(
        cirq.SampleResult(data=pd.DataFrame(
            data=[[1, 2, 3], [4, 5, 6]], index=[7, 8],
            columns=['a', 'b', 'c']))) == ("SampleResult with data:\n"
                                           "   a  b  c\n"
                                           "7  1  2  3\n"
                                           "8  4  5  6")


def test_equals():
    eq = cirq.testing.EqualsTester()
    eq.make_equality_group(lambda: cirq.SampleResult(data=pd.DataFrame(
        data=[[1, 2, 3], [4, 5, 6]], index=[7, 8], columns=['a', 'b', 'c'])))
    eq.add_equality_group(
        cirq.SampleResult(data=pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]],
                                            index=[7, 101],
                                            columns=['a', 'bla', 'c'])))
