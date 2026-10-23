"""save_check and after_check in the v3 kit work as in v2 (K37, K39 to K41): the next <brand-slug>-check-N.html, never an
overwrite, a fourth build refused unless the rep asked for a fix round, "continue" is not a fix round, and after_check
says build again in this turn while a build is left. Runs offline against a fake create-once chat.
Run: python3 tests/v3checkcap.py"""
import io
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v3fixture as F

K = F.kit
fails = 0


def check(label, ok, detail=""):
    global fails
    fails += not ok
    print(("OK   " if ok else "FAIL ") + label, "" if ok else detail)


class Chat:
    def __init__(self, *names):
        self.files = {n: "<html>" for n in names}

    def __call__(self, name, mode="r"):
        if "x" in mode:
            if name in self.files:
                raise FileExistsError(name)
            chat = self

            class W(io.StringIO):
                def close(s):
                    chat.files[name] = s.getvalue()
                    super().close()
            return W()
        if "w" in mode:
            raise PermissionError("open_artifact refuses 'w'")
        if name not in self.files:
            raise FileNotFoundError(name)
        return io.BytesIO(self.files[name].encode()) if "b" in mode else io.StringIO(self.files[name])


doc, r = F.build()
slug = K.check_slug(r.M[0].name)
check("slug", slug == "natural-retreats", slug)


def save(chat, rep_asked=None):
    try:
        return K.save_check("<html>build</html>", r, chat, rep_asked=rep_asked), ""
    except ValueError as e:
        return None, str(e)


chat = Chat()
names = []
for n in (1, 2, 3):
    names.append(save(chat)[0])
    msg = K.after_check(r, ["page 2 overlaps"])
    check(f"build {n}: a defect with a build left says build again", (n < 3 and "Not done" in msg and "build again now, in this turn" in msg)
          or (n == 3 and "No build left" in msg), msg[:120])
check("three builds written in turn", names == [f"{slug}-check-{k}.html" for k in (1, 2, 3)], names)
check("no defect: reply now", "reply now" in K.after_check(r, []) and "no defect" in K.after_check(r, []))
name, got = save(chat)
check("a fourth build is refused", name is None and "at most 3 check builds" in got and "rep_asked" in got, got[:160])
name, got = save(chat, rep_asked="continue")
check("continue is not a fix round", name is None and "not a fix round" in got and f"{slug}-check-4.html" not in chat.files, got[:100])
name, got = save(chat, rep_asked="  ")
check("blank words are not a fix round", name is None, got[:80])
name, got = save(chat, rep_asked="Kevin's fix round on natural-retreats-check-1: move the Pitfall row")
check("a rep's words write build 4", name == f"{slug}-check-4.html", name or got[:80])
check("after a fix round a defect still says build again", "fix round" in K.after_check(r, ["logo blurry"]))
try:
    K.after_check(type("R", (), {})(), [])
    check("after_check needs a saved build", False, "no error")
except ValueError:
    check("after_check needs a saved build", True)
other = Chat("doctoralia-check-1.html", f"{slug}-creative-review.html", "spec-1.json")
check("other files are not counted", save(other)[0] == f"{slug}-check-1.html")
sys.exit(1 if fails else 0)
