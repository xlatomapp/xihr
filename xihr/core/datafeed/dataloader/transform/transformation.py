import abc
import datetime as dt
import re
import textwrap
from typing import Any

import numpy as np
import pandas as pd

from ..constant import RACE_DATA_KUBUN_MAP


class Transformation(abc.ABC):
    @abc.abstractmethod
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        """
        transform the input DataFrame.

        Args:
            input_df: The input DataFrame to be transformed.

        Returns:
            The transformed DataFrame.
        """
        pass


# ==============================================================================
#
# Common Transformations
#
# ==============================================================================
class IdentityTransformation(Transformation):
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x


class DropColumnsTransformation(Transformation):
    def __init__(self, columns_to_drop: list):
        self.columns_to_drop = columns_to_drop

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.drop(columns=self.columns_to_drop, axis=1)


class AsTypeTransformation(Transformation):
    def __init__(self, column: str, to_type: type, errors: str = "coerce"):
        self.column = column
        self.to_type = to_type
        self.errors = errors

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        if np.issubdtype(self.to_type, np.number):
            x[self.column] = pd.to_numeric(
                x[self.column], errors=self.errors
            )  # type: ignore
        x[self.column] = x[self.column].astype(dtype=self.to_type)
        return x


class ScaleTransformation(Transformation):
    def __init__(self, column: str, multiplier: float):
        self.column = column
        self.mutiplier = multiplier

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x[self.column] = x[self.column] * self.mutiplier
        return x


class EncodeTransformation(Transformation):
    def __init__(self, column: str, strip: bool = False, code: str = "utf-8"):
        self.column = column
        self.strip = strip
        self.code = code

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        if self.strip:
            x[self.column] = x[self.column].apply(lambda x: x.strip())
        x[self.column] = x[self.column].apply(lambda x: x.encode("utf-8"))
        return x


class RenameColumnsTransformation(Transformation):
    def __init__(self, column_mapping: dict):
        self.column_mapping = column_mapping

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.rename(columns=self.column_mapping)


class IfEqualTransformation(Transformation):
    def __init__(self, column: str, cond: Any, true_value: Any, false_value: Any):
        self.column = column
        self.cond = cond
        self.true_value = true_value
        self.false_value = false_value

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x[self.column] = x[self.column].apply(self.__transform_value)
        return x

    def __transform_value(self, val: Any):
        if val == self.cond:
            return self.true_value
        return self.false_value


class FilterTransformation(Transformation):
    def __init__(self, cond: str):
        self.cond = cond

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.query(self.cond)


class SelectColumnsTransformation(Transformation):
    def __init__(self, columns_to_select: list):
        self.columns_to_select = columns_to_select

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x[self.columns_to_select]


# ==============================================================================
#
# jra dataset Transformations
#
# ==============================================================================
class GenRaceIdTransformation(Transformation):
    """
    Generate race_id
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        cols = [
            "kaisai_nen",
            "kaisai_tsukihi",
            "keibajo_code",
            "kaisai_kai",
            "kaisai_nichime",
            "race_bango",
        ]
        x = x.assign(raceId=x[cols].apply(lambda x: "".join(x), axis=1))
        return x


class GenRaceRecordTypeTransformation(Transformation):
    """
    genRaceRecordTypeTransformation
    Table: ２．レース詳細
    Row: 2 データ区分
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.assign(recordType=x["data_kubun"].map(RACE_DATA_KUBUN_MAP))


class GenRaceDateTransformation(Transformation):
    """
    Generate race date
    Table: ２．レース詳細
    Row: 4, 5 開催年, 開催月日 -> combined into one record after transformation
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        cols = ["kaisai_nen", "kaisai_tsukihi"]
        x = x.assign(date=x[cols].apply(lambda x: "".join(x), axis=1))
        x["date"] = pd.to_datetime(x["date"], format="%Y%m%d").dt.date
        return x


class GenCreateDateTransformation(Transformation):
    """
    GenCreateDateTimeTransformation
    Table: ２．レース詳細
    Row: 3 データ作成年月日
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.assign(createDate=x["data_sakusei_nengappi"].apply(self.__to_datetime))

    def __to_datetime(self, d: str) -> Any:
        if d == "00000000":
            return np.nan
        return pd.to_datetime(d, format="%Y%m%d", errors="coerce")


class GenRefundTransformation(Transformation):
    """
    Generate refund
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x["refund_1a"] = x["henkan_umaban_joho"].apply(
            lambda y: [h for h in y if h == 1]
        )
        x["refund_1b"] = 100
        return x


class GenStrikePatternTransformation(Transformation):
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x1 = x.filter(regex="haraimodoshi_.*_[1-9]a")
        x1 = x1.map(lambda x: textwrap.wrap(x, 2))
        x1 = x1.rename(columns=lambda n: re.sub("haraimodoshi_", "", n))
        return x.join(x1)


class GenPayoffTransformation(Transformation):
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x1 = x.filter(regex="haraimodoshi_.*_[1-9]b")
        x1 = x1.map(pd.to_numeric, errors="coerce")
        x1 = x1.rename(columns=lambda n: re.sub("haraimodoshi_", "", n))
        return x.join(x1)


class GenHorseNumTransformation(Transformation):
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        hn = x.filter(regex="haraimodoshi_.*a").map(lambda r: textwrap.wrap(r, 2))
        x.update(hn)
        return x


class MapRaceDataKubunTransformation(Transformation):
    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.assign(record_type=x["kubun"].map(RACE_DATA_KUBUN_MAP))
