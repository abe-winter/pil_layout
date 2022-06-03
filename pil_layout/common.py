from typing import Tuple

class LayoutError(Exception):
    # todo: add tree position to these
    pass

def partition(seq, predicate) -> Tuple[list, list]:
    "turn seq into two seqs, (predicate_true, predict_false). ugh use a collections library"
    rets = ([], [])
    for item in seq:
        # note: True / False are 0/1 as indexes, that's why this works
        rets[predicate(item)].append(item)
    return rets
