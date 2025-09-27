import datetime as dt
import textwrap
from typing import Any

import numpy as np
import pandas as pd

from ..constant import RACE_DATA_KUBUN_MAP
from .transformation import (
    EncodeTransformation,
    GenCreateDateTransformation,
    GenRaceDateTransformation,
    GenRaceIdTransformation,
    GenRaceRecordTypeTransformation,
    RenameColumnsTransformation,
    SelectColumnsTransformation,
    Transformation,
)


class GenDistanceTransformation(Transformation):
    """
    GenDistanceTransformation
    Table: ２．レース詳細
    Row: 34
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        """
        GenDistanceTransformation.transform
        Transform  column "kyori" to int and assign it to new column "distance"
        :param x: pd.DataFrame
        :return: pd.DataFrame
        """
        return x.assign(distance=x["kyori"].astype(float))


class GenDistancePreChangeTransformation(Transformation):
    """
    GenDistancePreChangeTransformation
    Table: ２．レース詳細
    Row: 35
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        """
        GenDistancePreChangeTransformation.transform
        Transform  column "kyori_henkomae" to int and assign it
            to new column "distancePreChange"
        :param x: pd.DataFrame
        :return: pd.DataFrame
        """
        x1 = x.assign(distancePreChange=x["kyori_henkomae"].astype(int))
        x1 = x1.assign(
            distancePreChange=x1["distancePreChange"].apply(self.__parse_col)
        )
        return x1

    def __parse_col(self, n: int) -> Any:
        """
        Parses the given integer column value and returns NaN if
            the value is zero, otherwise returns the original value.

        :param n: Integer value from the column.
        :return: np.nan if n is zero, otherwise the original integer value.
        """

        return np.nan if n == 0 else n


class GenPrizeTransformation(Transformation):
    """
    GenPrizeTransformation
    Table: ２．レース詳細
    Row: 40
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        t = x["honshokin"].map(lambda r: textwrap.wrap(r, 8))
        r = t.pipe(lambda s: pd.DataFrame(dict(zip(s.index, s.values))))
        r = r.T.rename(columns=lambda c: f"prize{c+1}")
        r = r.astype(int) * 100  # unit is 100 yen, hence time 100 to get raw
        return x.join(r, how="left")


class GenPrizePreChangeTransformation(Transformation):
    """
    GenPrizeTransformation
    Table: ２．レース詳細
    Row: 41
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        t = x["honshokin_henkomae"].map(lambda r: textwrap.wrap(r, 8))
        r = t.pipe(lambda s: pd.DataFrame(dict(zip(s.index, s.values))))
        r = r.T.rename(columns=lambda c: f"prizePreChange{c+1}")
        r = r.astype(int) * 100  # unit is 100 yen, hence time 100 to get raw
        return x.join(r, how="left")


class GenBonusPrizeTransformation(Transformation):
    """
    GenPrizeTransformation
    Table: ２．レース詳細
    Row: 42
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        t = x["fukashokin"].map(lambda r: textwrap.wrap(r, 8))
        r = t.pipe(lambda s: pd.DataFrame(dict(zip(s.index, s.values))))
        r = r.T.rename(columns=lambda c: f"bonusPrize{c+1}")
        r = r.astype(int) * 100  # unit is 100 yen, hence time 100 to get raw
        return x.join(r, how="left")


class GenBonusPrizePreChangeTransformation(Transformation):
    """
    GenPrizeTransformation
    Table: ２．レース詳細
    Row: 43
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        t = x["fukashokin_henkomae"].map(lambda r: textwrap.wrap(r, 8))
        r = t.pipe(lambda s: pd.DataFrame(dict(zip(s.index, s.values))))
        r = r.T.rename(columns=lambda c: f"bonusPrizePreChange{c+1}")
        r = r.astype(int) * 100  # unit is 100 yen, hence time 100 to get raw
        return x.join(r, how="left")


class GenStartTimeTransformation(Transformation):
    """
    Generate start time
    Table: ２．レース詳細
    Row: 44
    """

    def __init__(self, time_format: str = "%H%M"):
        super().__init__()
        self.time_format = time_format

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x = x.assign(startTime=x["hasso_jikoku"].apply(self._to_time))
        return x

    # this is pandas-stub issue actual typing should be dt.time
    def _to_time(self, dtstr: str) -> Any:

        """
        Convert given string to dt.time object.

        Args:
            dtstr (str): date string in specified format in self.time_format

        Returns:
            dt.time: time object
        """
        return dt.datetime.strptime(dtstr, self.time_format).time()


class GenStartTimePreChangeTransformation(GenStartTimeTransformation):
    """
    Generate start time
    Table: ２．レース詳細
    Row: 44
    """

    def __init__(self, time_format: str = "%H%M"):
        super().__init__()
        self.time_format = time_format

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x = x.assign(startTimePreChange=x["hasso_jikoku_henkomae"].apply(self._to_time))
        return x


class GenRegisteredCountTransformation(Transformation):
    """
    Generate registered count
    Table: ２．レース詳細
    Row: 46 登録頭数
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x = x.assign(registeredCount=x["toroku_tosu"].astype(int))
        return x


class GenRacedCountTransformation(Transformation):
    """
    Generate raced count
    Table: ２．レース詳細
    Row: 47 出走頭数
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x = x.assign(racedCount=x["shusso_tosu"].astype(int))
        return x


class GenCompletedNumTransformation(Transformation):
    """
    Generate Completed Count
    Table: ２．レース詳細
    Row: 48 入線頭数
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        x = x.assign(completedCount=x["nyusen_tosu"].astype(int))
        return x


__COLUM_MAPPING = {
    "keibajo_code": "raceVenueCode",
    "kaisai_kai": "raceSeriesNumber",
    "kaisai_nichime": "raceDayNumber",
    "race_bango": "raceNumber",
    "yobi_code": "dayType",
    "tokubetsu_kyoso_bango": "specialRaceNumber",
    "kyosomei_hondai": "raceTitle",
    "kyosomei_fukudai": "raceSubTitle",
    "kyosomei_kakkonai": "raceNameParenthetical",
    "kyosomei_hondai_eur": "raceTitleRomaji",
    "kyosomei_fukudai_eur": "raceSubTitleRomaji",
    "kyosomei_kakkonai_eur": "raceNameParentheticalRomaji",
    "kyosomei_ryakusho_10": "raceNameShort10",
    "kyosomei_ryakusho_6": "raceNameShort6",
    "kyosomei_ryakusho_3": "raceNameShort3",
    "kyosomei_kubun": "raceNameCategory",
    "jusho_kaiji": "gradedRaceEdition",
    "grade_code": "gradeCode",
    "grade_code_henkomae": "gradeCodePreChange",
    "kyoso_shubetsu_code": "raceTypeCode",
    "kyoso_kigo_code": "raceSymbolCode",
    "juryo_shubetsu_code": "weightTypeCode",
    "kyoso_joken_code_2sai": "raceConditionCode2yo",
    "kyoso_joken_code_3sai": "raceConditionCode3yo",
    "kyoso_joken_code_4sai": "raceConditionCode4yo",
    "kyoso_joken_code_5sai_ijo": "raceConditionCode5yoUp",
    "kyoso_joken_code": "raceConditionCode",
    "kyoso_joken_meisho": "raceConditionName",
    "track_code": "trackCode",
    "track_code_henkomae": "trackCodePreChange",
    "course_kubun": "courseCategory",
    "course_kubun_henkomae": "courseCategoryPreChange",
    "tenko_code": "weatherCode",
    "babajotai_code_shiba": "turfConditionCode",
    "babajotai_code_dirt": "dirtConditionCode",
    "record_koshin_kubun": "recordUpdateType",
}

__RACE_COLUMNS = [
    "date",
    "recordType",
    "raceId",
    "startTime",
    "startTimePreChange",
    "raceSeriesNumber",
    "raceDayNumber",
    "raceNumber",
    "raceVenueCode",
    "dayType",
    "specialRaceNumber",
    "raceTitle",
    "raceSubTitle",
    "raceNameParenthetical",
    "raceTitleRomaji",
    "raceSubTitleRomaji",
    "raceNameParentheticalRomaji",
    "distance",
    "distancePreChange",
    "raceNameShort10",
    "raceNameShort6",
    "raceNameShort3",
    "raceNameCategory",
    "gradedRaceEdition",
    "gradeCode",
    "gradeCodePreChange",
    "raceTypeCode",
    "raceSymbolCode",
    "weightTypeCode",
    "raceConditionCode2yo",
    "raceConditionCode3yo",
    "raceConditionCode4yo",
    "raceConditionCode5yoUp",
    "raceConditionCode",
    "raceConditionName",
    "trackCode",
    "trackCodePreChange",
    "courseCategory",
    "courseCategoryPreChange",
    "prize1",
    "prize2",
    "prize3",
    "prize4",
    "prize5",
    "prize6",
    "prize7",
    "prizePreChange1",
    "prizePreChange2",
    "prizePreChange3",
    "prizePreChange4",
    "prizePreChange5",
    "bonusPrize1",
    "bonusPrize2",
    "bonusPrize3",
    "bonusPrize4",
    "bonusPrize5",
    "bonusPrizePreChange1",
    "bonusPrizePreChange2",
    "bonusPrizePreChange3",
    "registeredCount",
    "racedCount",
    "completedCount",
    "weatherCode",
    "turfConditionCode",
    "dirtConditionCode",
    "recordUpdateType",
]

RACE_TRANSFORMATIONS = [
    GenRaceIdTransformation(),
    GenRaceRecordTypeTransformation(),
    GenRaceDateTransformation(),
    GenStartTimeTransformation(),
    GenStartTimePreChangeTransformation(),
    GenDistancePreChangeTransformation(),
    GenDistanceTransformation(),
    GenPrizeTransformation(),
    GenBonusPrizeTransformation(),
    GenPrizePreChangeTransformation(),
    GenRegisteredCountTransformation(),
    GenBonusPrizePreChangeTransformation(),
    GenRacedCountTransformation(),
    GenCompletedNumTransformation(),
    EncodeTransformation("kyosomei_hondai"),
    EncodeTransformation("kyosomei_fukudai"),
    EncodeTransformation("kyosomei_kakkonai"),
    EncodeTransformation("kyosomei_hondai_eur"),
    EncodeTransformation("kyosomei_fukudai_eur"),
    EncodeTransformation("kyosomei_kakkonai_eur"),
    EncodeTransformation("kyosomei_ryakusho_10"),
    EncodeTransformation("kyosomei_ryakusho_6"),
    EncodeTransformation("kyosomei_ryakusho_3"),
    RenameColumnsTransformation(__COLUM_MAPPING),
    SelectColumnsTransformation(__RACE_COLUMNS),
]
