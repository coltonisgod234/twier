def fileset(fp: str) -> set:
    data = set()
    with open("config/unclaimable.txt", "r") as f:
        data = [line.lower() for line in f.read().splitlines()]
        f.close()
        del f

    return data
