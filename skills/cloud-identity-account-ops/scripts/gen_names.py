import json, random, sys

# 用法: python gen_names.py [輸出路徑] [前綴] [起始號] [數量]
# 例: python gen_names.py D:\Hermes\skills\google-admin\cloud-identity-account-ops\scripts\names.json a 1 50
OUT = sys.argv[1] if len(sys.argv) > 1 else r"D:\Hermes\skills\google-admin\cloud-identity-account-ops\scripts\names.json"
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "a"
START = int(sys.argv[3]) if len(sys.argv) > 3 else 1
COUNT = int(sys.argv[4]) if len(sys.argv) > 4 else 50

# 100 個中性英文名（a01-a50, b01-b50 各 50 個，不重複）
first_a = ["Alex","Sam","Jordan","Riley","Taylor","Casey","Jamie","Morgan","Avery","Quinn",
           "Rowan","Blake","Parker","Charlie","Finley","Skyler","Emery","Phoenix","Reese","Sage",
           "Dakota","Harper","Cameron","Devon","Drew","Elliott","Hayden","Jules","Kendall","Lane",
           "Logan","Marley","Micah","Noel","Oakley","Peyton","River","Robin","Rory","Sawyer",
           "Shay","Sidney","Sterling","Teagan","Tatum","Terry","Tracy","Wren","Zane","Arden"]
first_b = ["Ariel","Blair","Case","Gale","Hart","Ivey","Kai","Kit","Lark","Lee",
           "Lyn","Maris","Onyx","Paz","Rae","Reed","Rene","Rue","Sky","Sol",
           "Stacy","Stevie","Vale","Vic","Wynn","Xan","Ziv","Bell","Bryn","Cade",
           "Dell","Ellis","Fable","Gray","Haven","Indigo","Joss","Kelsey","Lake","Monroe",
           "Navy","Ocean","Remy","Scout","Tobin","Vesper","West","Yael","Jade","Ainsley"]

lasts = ["Chen","Lin","Wang","Lee","Liu","Yang","Huang","Chang","Wu","Hsu",
         "Cheng","Ho","Liao","Tsai","Tseng","Su","Chiang","Chuang","Kao","Kuo",
         "Lo","Liang","Sung","Tang","Han","Feng","Yu","Tung","Hsiao","Tu",
         "Smith","Johnson","Miller","Brown","Davis","Wilson","Moore","Anderson","Thomas","Jackson",
         "White","Harris","Martin","Thompson","Garcia","Martinez","Robinson","Clark","Rodriguez","Lewis"]

names = []
for i, f in enumerate(first_a[:COUNT]):
    names.append({"acc": f"{PREFIX}{i+START:02d}", "first": f, "last": lasts[i % 50]})
for i, f in enumerate(first_b):
    if len(names) >= COUNT:
        break
    names.append({"acc": f"{chr(ord(PREFIX)+1)}{i+1:02d}", "first": f, "last": lasts[(i + 25) % 50]})

with open(OUT, "w", encoding="utf-8") as fp:
    json.dump(names, fp, ensure_ascii=False, indent=1)

print(f"生成 {len(names)} 個帳號：")
for n in names[:5]:
    print(f"  {n['acc']} -> {n['first']} {n['last']}")
print("  ...")
for n in names[-3:]:
    print(f"  {n['acc']} -> {n['first']} {n['last']}")
# 檢查重複
fnames = [n["first"] for n in names]
print("重複名:", [x for x in set(fnames) if fnames.count(x) > 1] or "無")
