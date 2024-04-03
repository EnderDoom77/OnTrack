from config import Config
from data import Profile, ProgramData
from lib.constants import GROUPING_OTHER

def bucket_into_other(data: dict[str, float], threshold: float, other_name: str = GROUPING_OTHER) -> dict[str, float]:
    result = {}
    other = 0
    for k,v in data.items():
        if v < threshold:
            other += v
        else:
            result[k] = v
    if other > 0:
        result[other_name] = other
    return result

# Always put GROUPING_OTHER at the end
def sort_dict_by_value(data: dict[str, float], reverse: bool = True, force_min_key = GROUPING_OTHER) -> tuple[list[str], list[float]]:
    def sorter_key(k):
        v = data[k]
        if k == force_min_key:
            return float("-inf")
        return v
    keys = sorted(data.keys(), key=sorter_key, reverse=reverse)
    values = [data[k] for k in keys]
    return keys, values