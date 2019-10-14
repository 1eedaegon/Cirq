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
"""Abstract base class for things sampling quantum circuits."""

from typing import List, Union, TYPE_CHECKING
import abc
import asyncio
import threading

import pandas as pd

from cirq import study

if TYPE_CHECKING:
    import cirq


class Sampler(metaclass=abc.ABCMeta):
    """Something capable of sampling quantum circuits. Simulator or hardware."""

    def run(
            self,
            program: Union['cirq.Circuit', 'cirq.Schedule'],
            param_resolver: 'cirq.ParamResolverOrSimilarType' = None,
            repetitions: int = 1,
    ) -> 'cirq.TrialResult':
        """Samples from the given Circuit or Schedule.

        By default, the `run_async` method invokes this method on another
        thread. So this method is supposed to be thread safe.

        Args:
            program: The circuit or schedule to sample from.
            param_resolver: Parameters to run with the program.
            repetitions: The number of times to sample.

        Returns:
            TrialResult for a run.
        """
        return self.run_sweep(program, study.ParamResolver(param_resolver),
                              repetitions)[0]

    def sample(
            self,
            program: Union['cirq.Circuit', 'cirq.Schedule'],
            *,
            repetitions: int = 1,
            params: 'cirq.Sweepable' = None,
    ) -> 'pd.DataFrame':
        """Samples the given Circuit or Schedule, producing a pandas data frame.

        Args:
            program: The circuit or schedule to sample from.
            repetitions: The number of times to sample the program, for each
                parameter mapping.
            params: Maps symbols to one or more values. This argument can be
                a dictionary, a list of dictionaries, a `cirq.Sweep`, a list of
                `cirq.Sweep`, etc. The program will be sampled `repetition`
                times for each mapping. Defaults to a single empty mapping.

        Returns:
            A `pandas.DataFrame` with a row for each sample, and a column for
            each measurement result as well as a column for each symbolic
            parameter. There is an also index column containing the repetition
            number, for each parameter assignment.

        Examples:
            >>> a, b, c = cirq.LineQubit.range(3)
            >>> sampler = cirq.Simulator()
            >>> circuit = cirq.Circuit(cirq.X(a),
            ...                        cirq.measure(a, key='out'))
            >>> print(sampler.sample(circuit, repetitions=4))
               out
            0    1
            1    1
            2    1
            3    1

            >>> circuit = cirq.Circuit(cirq.X(a),
            ...                        cirq.CNOT(a, b),
            ...                        cirq.measure(a, b, c, key='out'))
            >>> print(sampler.sample(circuit, repetitions=4))
               out
            0    6
            1    6
            2    6
            3    6

            >>> circuit = cirq.Circuit(cirq.X(a)**sympy.Symbol('t'),
            ...                        cirq.measure(a, key='out'))
            >>> print(sampler.sample(
            ...     circuit,
            ...     repetitions=3,
            ...     params=[{'t': 0}, {'t': 1}]))
               t  out
            0  0    0
            1  0    0
            2  0    0
            0  1    1
            1  1    1
            2  1    1
        """

        sweeps_list = study.to_sweeps(params)
        keys = sorted(sweeps_list[0].keys) if sweeps_list else []
        for sweep in sweeps_list:
            if sweep and set(sweep.keys) != set(keys):
                raise ValueError(
                    'Inconsistent sweep parameters. '
                    f'One sweep had {repr(keys)} '
                    f'while another had {repr(sorted(sweep.keys))}.')

        results = []
        for sweep in sweeps_list:
            sweep_results = self.run_sweep(program,
                                           params=sweep,
                                           repetitions=repetitions)
            for resolver, result in zip(sweep, sweep_results):
                param_values_once = [resolver.value_of(key) for key in keys]
                param_table = pd.DataFrame(data=[param_values_once] *
                                           repetitions,
                                           columns=keys)
                results.append(pd.concat([param_table, result.data], axis=1))

        return pd.concat(results)

    @abc.abstractmethod
    def run_sweep(
            self,
            program: Union['cirq.Circuit', 'cirq.Schedule'],
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> List['cirq.TrialResult']:
        """Samples from the given Circuit or Schedule.

        In contrast to run, this allows for sweeping over different parameter
        values.

        Args:
            program: The circuit or schedule to sample from.
            params: Parameters to run with the program.
            repetitions: The number of times to sample.

        Returns:
            TrialResult list for this run; one for each possible parameter
            resolver.
        """

    async def run_async(self, program: Union['cirq.Circuit', 'cirq.Schedule'],
                        *, repetitions: int) -> 'cirq.TrialResult':
        """Asynchronously samples from the given Circuit or Schedule.

        By default, this method calls `run` on another thread and yields the
        result via the asyncio event loop. However, child classes are free to
        override it to use other strategies.

        Args:
            program: The circuit or schedule to sample from.
            repetitions: The number of times to sample.

        Returns:
            An awaitable TrialResult.
        """
        results = await self.run_sweep_async(program, study.UnitSweep,
                                             repetitions)
        return results[0]

    async def run_sweep_async(
            self,
            program: Union['cirq.Circuit', 'cirq.Schedule'],
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> List['cirq.TrialResult']:
        """Asynchronously sweeps and samples from the given Circuit or Schedule.

        By default, this method calls `run_sweep` on another thread and yields
        the result via the asyncio event loop. However, child classes are free
        to override it to use other strategies.

        Args:, '
                f'columns={repr(value.columns)}, '
                columns=['s', 't', 'out'],
            index=[0, 1, 2] * 4,
            data=[
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
                [0, 1, 1],
                [0, 1, 1],
                [0, 1, 1],
                [1, 0, 2],
                [1, 0, 2],
                [1, 0, 2],
                [1, 1, 3],
                [1, 1, 3],
                [1, 1, 3],
            ])
            program: The circuit or schedule to sample from.
            params: One or more mappings from parameter keys to parameter values
                to use. For each parameter assignment, `repetitions` samples
                will be taken.
            repetitions: The number of times to sample.

        Returns:
            An awaitable TrialResult.
        """
        return await run_on_thread_async(lambda: self.run_sweep(
            program, params=params, repetitions=repetitions))


async def run_on_thread_async(func):
    loop = asyncio.get_event_loop()
    done = loop.create_future()  # type: asyncio.Future['cirq.TrialResult']

    def run():
        try:
            result = func()
        except Exception as exc:
            loop.call_soon_threadsafe(done.set_exception, exc)
        else:
            loop.call_soon_threadsafe(done.set_result, result)

    t = threading.Thread(target=run)
    t.start()
    return await done
