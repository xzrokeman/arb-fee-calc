from dataclasses import dataclass
from typing import Union, Optional, Generator
from decimal import Decimal, ROUND_HALF_UP
import polars as pl

DECIMAL_PRECISION = "0.00"


@dataclass
class FeeSchedule:
    # list of break points, to be used to infer the intervals
    # len(fee_scale) - len(fee_rate) = 1
    fee_scale: list[float]
    # list of rates for intervals
    fee_rate: list[float]
    # base fee, most likely a int if the fee curve is continuous
    # len(base) = len(fee_rate) if self.base is a list
    base: Union[int, list[int]]
    # a list of ComplexRate instances
    fee_std: list = None

    @dataclass
    # like the 
    class ComplexRate:
        lower_range: Optional[float]
        upper_range: Optional[float]
        rate: float
        base: float

    def __post_init__(self):
        self._construct_fee_std()

    def _range_generator(self, n: int) -> Generator[list[float], None, None]:
        for x in range(n - 1):
            yield [self.fee_scale[x], self.fee_scale[x + 1]]

    # this is only used when the self.base is a int
    def _next_base_generator(self, n: int) -> Generator[list[float], None, None]:
        base = self.base
        for x in range(n):
            yield base # len(fee_scale) - len(fee_rate) = 1
            base += (self.fee_scale[x + 1] - self.fee_scale[x]) * self.fee_rate[x]

    def _construct_fee_std(self):
        # Due to the fact that some institutions' fee curves(structures) are not continuous,
        # they cannot be inferred solely through a combination of a minimum base fee,
        # intervals(or scales here), and rates. Therefore, it is necessary to directly
        # provide a list of base fees for different intervals(scales).
        if type(self.base) == list:
            fee_base = self.base
        else:
            fee_base = list(self._next_base_generator(len(self.fee_rate)))
        fee_std = [
            [lower, upper, rate, base]
            for (lower, upper), rate, base in zip(
                self._range_generator(len(self.fee_scale)), self.fee_rate, fee_base
            )
        ]
        self.fee_std = [
            self.ComplexRate(lower_range=v[0], upper_range=v[1], rate=v[2], base=v[3])
            for v in fee_std
        ]

    def calc(
        self, aid: Union[int, float], return_decimal: bool = True
    ) -> Union[Decimal, float]:
        for std in self.fee_std:
            if std.lower_range < aid <= std.upper_range:
                result = std.base + (aid - std.lower_range) * std.rate
                if return_decimal:
                    return Decimal(result).quantize(
                        Decimal(DECIMAL_PRECISION), rounding=ROUND_HALF_UP
                    )
                return result
        return (
            Decimal(self.base).quantize(
                Decimal(DECIMAL_PRECISION), rounding=ROUND_HALF_UP
            )
            if return_decimal
            else self.base
        )

    def plcalc(self, aid: str, optional_max: float) -> pl.Expr:
        # Create a placeholder for the result expression
        result_expr = pl.lit(None).alias("result")

        # Iterate over the fee_std list to construct the conditional expression
        for std in self.fee_std:
            condition = (pl.lit(std.lower_range) < pl.col(aid)) & (
                pl.col(aid) <= pl.lit(std.upper_range)
            )
            calculation = (
                pl.lit(std.base)
                + (pl.col(aid) - pl.lit(std.lower_range)) * pl.lit(std.rate)
            ).clip(upper_bound=optional_max)
            result_expr = pl.when(condition).then(calculation).otherwise(result_expr)

        # Handle the default case when aid does not fall within any range
        default_case = (
            pl.when(result_expr.is_null()).then(pl.lit(0)).otherwise(result_expr)
        )  # self.base[0]

        # Return the final expression
        return default_case
 
