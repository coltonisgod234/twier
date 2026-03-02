def fileset(fp: str) -> set:
    print(f"loading {fp}")

    data = set()
    with open(fp, "r") as f:
        data = [line.lower() for line in f.read().splitlines()]
        f.close()
        del f

    return data
