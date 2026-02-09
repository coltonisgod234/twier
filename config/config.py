# soimethging

BANNED_CLAIMS = set()
with open("config/unclaimable.txt", "r") as f:
    BANNED_CLAIMS = set(f.read().splitlines())
    f.close()
    del f


with open("config/dictionary.txt", "r") as f:
    BANNED_CLAIMS = set(f.read().splitlines())
    f.close()
    del f
