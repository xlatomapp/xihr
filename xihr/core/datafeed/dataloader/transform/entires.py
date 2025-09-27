import datetime as dt
import textwrap
from typing import Any

import numpy as np
import pandas as pd

from ..constant import RACE_DATA_KUBUN_MAP
from .transformation import (
    AsTypeTransformation,
    EncodeTransformation,
    GenCreateDateTransformation,
    GenRaceDateTransformation,
    GenRaceIdTransformation,
    RenameColumnsTransformation,
    ScaleTransformation,
    SelectColumnsTransformation,
    Transformation,
)


class GenRaceHourseRecordTypeTransformation(Transformation):
    """
    genRaceRecordTypeTransformation
    Table: ２．レース詳細
    Row: 2 データ区分
    """

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.assign(recordType=x["data_kubun"].map(RACE_DATA_KUBUN_MAP))


class GenClothPatternTransformation(Transformation):
    def transform(self, x):
        col = "fukushoku_hyoji"
        x[col] = x[col].apply(lambda x: x.strip().encode("utf-8"))
        return x


class GenUseBlinkerTransformation(Transformation):
    def transform(self, x):
        col = "blinker_shiyo_kubun"
        x[col] = x[col].apply(lambda x: True if x == 1 else False)
        return x


class GenHorseWeightChangeTransformation(Transformation):
    def transform(self, x):
        sign = x["zogen_fugo"].apply(lambda x: -1 if x == "-" else 1)
        x["weightChange"] = sign * x["zogen_sa"]
        return x


class GenTimeTakenTransformation(Transformation):
    def transform(self, x):
        x["timeTaken"] = x["soha_time"].apply(self.__parse_soha_time)
        return x

    def __parse_soha_time(self, time):
        h, m, s = (time[0], time[1:3], time[3:])
        return dt.timedelta(minutes=int(h), seconds=int(m), milliseconds=int(s) * 1000)


__COLUMN_MAPPING = {
    "wakuban": "bracketNum",
    "umaban": "horseNum",
    "ketto_toroku_bango": "horseId",
    "bamei": "horseName",
    "umakigo_code": "symbolCode",
    "seibetsu_code": "genderCode",
    "hinshu_code": "breedCode",
    "moshoku_code": "coatColorCode",
    "barei": "horseAge",
    "tozai_shozoku_code": "affiliationCode",
    "chokyoshi_code": "trainerCode",
    "chokyoshimei_ryakusho": "trainerNameShort",
    "banushi_code": "ownerCode",
    "banushimei": "ownerName",
    "fukushoku_hyoji": "clothPattern",
    "futan_juryo": "carryWeight",
    "futan_juryo_henkomae": "carryWeightBeforeChange",
    "blinker_shiyo_kubun": "blinkerUseCategory",
    "kishu_code": "jockeyCode",
    "kishu_code_henkomae": "jockeyCodeBeforeChange",
    "kishumei_ryakusho": "jockeyNameShort",
    "kishumei_ryakusho_henkomae": "jockeyNameShortBeforeChange",
    "kishu_minarai_code": "jockeyApprenticeCode",
    "kishu_minarai_code_henkomae": "jockeyApprenticeCodeBeforeChange",
    "bataiju": "horseWeight",
    "ijo_kubun_code": "abnormalityCategoryCode",
    "nyusen_juni": "preliminaryFinishOrder",
    "kakutei_chakujun": "finalFinishOrder",
    "dochaku_kubun": "sameRankStatus",
    "dochaku_tosu": "sameRankHorseCount",
    "soha_time": "timeTaken",
    "chakusa_code_1": "marginCode1",
    "chakusa_code_2": "marginCode2",
    "chakusa_code_3": "marginCode3",
    "corner_1": "corner1Position",
    "corner_2": "corner2Position",
    "corner_3": "corner3Position",
    "corner_4": "corner4Position",
    "tansho_odds": "winOdds",
    "tansho_ninkijun": "popularityRank",
    "kakutoku_honshokin": "earnedBasePrize",
    "kakutoku_fukashokin": "earnedAdditionalPrize",
    "yobi_3": "spare3",
    "yobi_4": "spare4",
    "kohan_4f": "last4Furlongs",
    "kohan_3f": "last3Furlongs",
    "time_sa": "timeDifference",
    "record_koshin_kubun": "recordUpdateCategory",
    "kyakushitsu_hantei": "runningStyleAssessment",
}

__RACE_COLUMNS = [
    "date",
    "raceId",
    "recordType",
    "bracketNum",
    "horseNum",
    "horseId",
    "horseName",
    "symbolCode",
    "genderCode",
    "breedCode",
    "coatColorCode",
    "horseAge",
    "affiliationCode",
    "trainerCode",
    "trainerNameShort",
    "ownerCode",
    "ownerName",
    "clothPattern",
    "carryWeight",
    "carryWeightBeforeChange",
    "blinkerUseCategory",
    "jockeyCode",
    "jockeyCodeBeforeChange",
    "jockeyNameShort",
    "jockeyNameShortBeforeChange",
    "jockeyApprenticeCode",
    "jockeyApprenticeCodeBeforeChange",
    "horseWeight",
    "abnormalityCategoryCode",
    "preliminaryFinishOrder",
    "finalFinishOrder",
    "sameRankHorseCount",
    "timeTaken",
    "marginCode1",
    "marginCode2",
    "marginCode3",
    "corner1Position",
    "corner2Position",
    "corner3Position",
    "corner4Position",
    "winOdds",
    "popularityRank",
    "earnedBasePrize",
    "earnedAdditionalPrize",
    "spare3",
    "spare4",
    "last4Furlongs",
    "last3Furlongs",
    "timeDifference",
    "recordUpdateCategory",
    "runningStyleAssessment",
]

ENTRIES_TRANSFORMATIONS = [
    GenRaceDateTransformation(),
    GenRaceIdTransformation(),
    GenRaceHourseRecordTypeTransformation(),
    AsTypeTransformation("wakuban", np.int32),
    AsTypeTransformation("umaban", np.int32),
    AsTypeTransformation("barei", np.int32),
    EncodeTransformation("bamei"),
    EncodeTransformation("banushimei"),
    EncodeTransformation("chokyoshimei_ryakusho"),
    EncodeTransformation("kishumei_ryakusho"),
    EncodeTransformation("kishumei_ryakusho_henkomae"),
    EncodeTransformation("fukushoku_hyoji", strip=True),
    GenUseBlinkerTransformation(),
    AsTypeTransformation("bataiju", float),
    GenHorseWeightChangeTransformation(),
    AsTypeTransformation("nyusen_juni", np.int32),
    AsTypeTransformation("kakutei_chakujun", np.int32),
    AsTypeTransformation("corner_1", np.int32),
    AsTypeTransformation("corner_2", np.int32),
    AsTypeTransformation("corner_3", np.int32),
    AsTypeTransformation("corner_4", np.int32),
    AsTypeTransformation("tansho_odds", np.int32),
    ScaleTransformation("tansho_odds", 0.1),
    AsTypeTransformation("tansho_ninkijun", np.int32),
    AsTypeTransformation("futan_juryo", np.int32),
    AsTypeTransformation("futan_juryo_henkomae", np.int32),
    ScaleTransformation("futan_juryo", 0.1),
    ScaleTransformation("futan_juryo_henkomae", 0.1),
    AsTypeTransformation("kakutoku_honshokin", np.int32),
    AsTypeTransformation("kakutoku_fukashokin", np.int32),
    ScaleTransformation("kakutoku_honshokin", 100),
    ScaleTransformation("kakutoku_fukashokin", 100),
    AsTypeTransformation("kohan_3f", float),
    AsTypeTransformation("kohan_4f", float),
    ScaleTransformation("kohan_3f", 0.1),
    ScaleTransformation("kohan_4f", 0.1),
    AsTypeTransformation("dochaku_tosu", float),
    RenameColumnsTransformation(__COLUMN_MAPPING),
    SelectColumnsTransformation(__RACE_COLUMNS),
]
