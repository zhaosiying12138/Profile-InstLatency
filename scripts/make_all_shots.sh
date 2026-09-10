#!/usr/bin/env bash
# Regenerate ALL blog screenshots in one go (requires an UNLOCKED Windows
# desktop; a locked desktop yields black captures).
# Usage: bash make_all_shots.sh
set -u
S=/home/zhaosiying/codebase/yushuxin-v2-design/scripts/ub_shot.sh
C=/home/zhaosiying/.yxshots/cmds
cd /home/zhaosiying/codebase/Profile-InstLatency

shot() { # name cmd timeout
  bash "$S" "$C/$2.sh" "shot_$1" "${3:-150}" >/dev/null 2>&1 || { echo "FAIL shot_$1"; return 1; }
  python3 - "$1" <<'PY'
import sys
from PIL import Image
p=f'/home/zhaosiying/codebase/yushuxin-v2-design/blog-output/shots/shot_{sys.argv[1]}.png'
im=Image.open(p).convert('RGB'); w,h=im.size
im2=im.resize((w//8,h//8)); px=list(im2.getdata()); n=len(px)
def near(c,t,tol=26): return all(abs(x-y)<=tol for x,y in zip(c,t))
purple=sum(1 for q in px if near(q,(48,10,36)))/n
black=sum(1 for q in px if sum(q)<10)/n
print(f"shot_{sys.argv[1]}: purple={purple:.0%} black={black:.0%} " +
      ("GOOD" if purple>0.3 else ("LOCKED/black" if black>0.9 else "BAD")))
PY
}

# ensure cmd scripts exist
bash "$(dirname "$0")/make_shot_cmds.sh"

shot env env
shot e0 e0
shot e2 e2
shot e3 e3
shot e4 e4
shot gate gate
shot mca mca
shot ab_asm ab_asm 200
shot ab_gem5 ab_gem5 200
shot ab_mca ab_mca 120
shot overlap overlap 120
