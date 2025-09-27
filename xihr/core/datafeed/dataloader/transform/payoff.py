import pandas as pd

from .transformation import (
    AsTypeTransformation,
    GenCreateDateTransformation,
    GenRaceDateTransformation,
    GenRaceIdTransformation,
    IfEqualTransformation,
    Transformation,
)


class GenRefundTransformation(Transformation):
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        cols = [f"refund{i}" for i in range(1, 29)]
        x[cols] = pd.DataFrame(
            x["henkan_umaban_joho"].apply(lambda y: [h for h in y]).to_list(),
            index=x.index,
        )
        return x


PAYOFF_TRANSFORMATIONS = [
    GenRaceDateTransformation(),
    GenRaceIdTransformation(),
    IfEqualTransformation("fuseiritsu_flag_tansho", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_fukusho", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_wakuren", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_umaren", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_wide", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_umatan", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_sanrenpuku", "1", True, False),
    IfEqualTransformation("fuseiritsu_flag_sanrentan", "1", True, False),
    IfEqualTransformation("tokubarai_flag_tansho", "1", True, False),
    IfEqualTransformation("tokubarai_flag_fukusho", "1", True, False),
    IfEqualTransformation("tokubarai_flag_wakuren", "1", True, False),
    IfEqualTransformation("tokubarai_flag_umaren", "1", True, False),
    IfEqualTransformation("tokubarai_flag_wide", "1", True, False),
    IfEqualTransformation("tokubarai_flag_umatan", "1", True, False),
    IfEqualTransformation("tokubarai_flag_sanrenpuku", "1", True, False),
    IfEqualTransformation("tokubarai_flag_sanrentan", "1", True, False),
    IfEqualTransformation("henkan_flag_tansho", "1", True, False),
    IfEqualTransformation("henkan_flag_fukusho", "1", True, False),
    IfEqualTransformation("henkan_flag_wakuren", "1", True, False),
    IfEqualTransformation("henkan_flag_umaren", "1", True, False),
    IfEqualTransformation("henkan_flag_wide", "1", True, False),
    IfEqualTransformation("henkan_flag_umatan", "1", True, False),
    IfEqualTransformation("henkan_flag_sanrenpuku", "1", True, False),
    IfEqualTransformation("henkan_flag_sanrentan", "1", True, False),
    GenRefundTransformation(),
]
