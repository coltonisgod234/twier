# soimethging

BANNED_CLAIMS = set()
with open("config/unclaimable.txt", "r") as f:
    BANNED_CLAIMS = [line.lower() for line in f.read().splitlines()]
    f.close()
    del f

DICTIONARY = set()
with open("config/dictionary.txt", "r") as f:
    DICTIONARY = [line.lower() for line in f.read().splitlines()]
    f.close()
    del f

BANNED_WORDS = set()
with open("config/bans.txt", "r") as f:
    BANNED_WORDS = [line.lower() for line in f.read().splitlines()]
    f.close()
    del f
