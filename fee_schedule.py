from typing import Union, Optional
from decimal import Decimal
from dataclasses import dataclass

# I don't want to write accumulating fee calc scripts any more,
# so I wrote this fee_schedule class as a reasonable abstraction for scenarios of
# this kind.
# example:
# fee_scale = [0, 1000, 50000, 100000, 200000, 500000, 1000000, float('inf')]
# fee_rate = [0, 0.05, 0.04, 0.03, 0.02, 0.01, 0.005]
# init_base = 100.0
# handling_fee_calc = fee_schedule(fee_scale=fee_scale,
#                                  fee_rate=fee_rate,
#                                  base=init_base)
# handling_fee_calc.fee_std
# handling_fee_calc.calc(100000)


@dataclass
class fee_schedule:
    fee_scale: list[Union[int, float]]
    fee_rate: list[Union[int, float]]
    base: Union[int, float]

    # upper/lower bound, rate, base, pack them up in an Inner Class
    @dataclass
    class complexRate:
        lower_range: Optional[float]
        upper_range: Optional[float]
        rate: float
        base: float

    def __post_init__(self):
        def range_generator(n: int, fee_scale: list[float]) -> list[float]:
            x = 0
            while x < n - 1:
                yield [fee_scale[x], fee_scale[x + 1]]
                x += 1

        def next_base_generator(
            n: int, fee_scale: list[float], fee_rate: list[float], base: float
        ) -> float:
            x = 0
            while x < n - 1:
                yield base
                x += 1
                base += (fee_scale[x + 1] - fee_scale[x]) * fee_rate[x]

        self.fee_base = [
            i
            for i in next_base_generator(
                len(self.fee_rate), self.fee_scale, self.fee_rate, self.base
            )
        ]
        self.fee_base.insert(0, self.base)
        self._fee_std = [
            value for value in range_generator(len(self.fee_scale), self.fee_scale)
        ]
        for i, v in enumerate(self._fee_std):
            v.append(self.fee_rate[i])
            v.append(self.fee_base[i])

        self.fee_std = [
            self.complexRate(lower_range=v[0], upper_range=v[1], rate=v[2], base=v[3])
            for v in self._fee_std
        ]

    def calc(self, AID: Union[int, float]) -> Decimal:
        for std in self.fee_std:
            if std.lower_range < AID and std.upper_range >= AID:
                return Decimal(std.base + (AID - std.lower_range) * std.rate).quantize(
                    Decimal("0.00")
                )
        return Decimal(self.base).quantize(Decimal('0.00'))
    
    def fcalc(self, AID: Union[int, float]) -> float:
        for std in self.fee_std:
            if std.lower_range < AID and std.upper_range >= AID:
                return std.base + (AID - std.lower_range) * std.rate
        return self.base
