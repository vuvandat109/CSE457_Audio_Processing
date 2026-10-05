from vietnamese_phonology import parse_syllable


TESTS = [
    # Thanh dieu
    ("ma", "m", "", "a", "", "ngang"),
    ("má", "m", "", "a", "", "sac"),
    ("mà", "m", "", "a", "", "huyen"),
    ("mả", "m", "", "a", "", "hoi"),
    ("mã", "m", "", "a", "", "nga"),
    ("mạ", "m", "", "a", "", "nang"),

    # Phu am dau don
    ("ba", "b", "", "a", "", "ngang"),
    ("đi", "đ", "", "i", "", "ngang"),
    ("xa", "x", "", "a", "", "ngang"),

    # Phu am dau ghep
    ("cha", "ch", "", "a", "", "ngang"),
    ("nhà", "nh", "", "a", "", "huyen"),
    ("nghe", "ngh", "", "e", "", "ngang"),
    ("nghiêng", "ngh", "", "iê", "ng", "ngang"),
    ("thơ", "th", "", "ơ", "", "ngang"),
    ("phá", "ph", "", "a", "", "sac"),
    ("khi", "kh", "", "i", "", "ngang"),
    ("trời", "tr", "", "ơ", "i", "huyen"),

    # Am cuoi
    ("nam", "n", "", "a", "m", "ngang"),
    ("lan", "l", "", "a", "n", "ngang"),
    ("lang", "l", "", "a", "ng", "ngang"),
    ("lạnh", "l", "", "a", "nh", "nang"),
    ("hát", "h", "", "a", "t", "sac"),
    ("học", "h", "", "o", "c", "nang"),
    ("đẹp", "đ", "", "e", "p", "nang"),

    # Ban nguyen am cuoi
    ("tay", "t", "", "a", "y", "ngang"),
    ("mai", "m", "", "a", "i", "ngang"),
    ("sao", "s", "", "a", "o", "ngang"),
    ("đau", "đ", "", "a", "u", "ngang"),

    # Am dem
    ("hoa", "h", "o", "a", "", "ngang"),
    ("khoa", "kh", "o", "a", "", "ngang"),
    ("loan", "l", "o", "a", "n", "ngang"),
    ("thuyền", "th", "u", "yê", "n", "huyen"),

    # Nguyen am tieng Viet
    ("ăn", "", "", "ă", "n", "ngang"),
    ("ân", "", "", "â", "n", "ngang"),
    ("êm", "", "", "ê", "m", "ngang"),
    ("ôm", "", "", "ô", "m", "ngang"),
    ("ơn", "", "", "ơ", "n", "ngang"),
    ("ưng", "", "", "ư", "ng", "ngang"),

    # Cac vi du quan trong trong ASR
    ("chạy", "ch", "", "a", "y", "nang"),
    ("chảy", "ch", "", "a", "y", "hoi"),
    ("già", "gi", "", "a", "", "huyen"),
    ("giả", "gi", "", "a", "", "hoi"),
    ("nước", "n", "", "ươ", "c", "sac"),
    ("người", "ng", "", "ươ", "i", "huyen"),
    ("ánh", "", "", "a", "nh", "sac"),
    ("lãnh", "l", "", "a", "nh", "nga"),
    ("lánh", "l", "", "a", "nh", "sac"),
]


passed = 0
failed = 0

print("===== TEST VIETNAMESE PHONOLOGY =====")

for word, initial, medial, nucleus, coda, tone in TESTS:

    result = parse_syllable(word)

    expected = {
        "initial": initial,
        "medial": medial,
        "nucleus": nucleus,
        "coda": coda,
        "tone": tone
    }

    actual = {
        "initial": result["initial"],
        "medial": result["medial"],
        "nucleus": result["nucleus"],
        "coda": result["coda"],
        "tone": result["tone"]
    }

    if actual == expected:

        passed += 1
        print(f"[PASS] {word}")

    else:

        failed += 1

        print(f"\n[FAIL] {word}")
        print("Expected:", expected)
        print("Actual  :", actual)


print("\n==============================")
print("Tong test :", len(TESTS))
print("PASS      :", passed)
print("FAIL      :", failed)

if failed == 0:
    print("\nKET QUA: TAT CA TEST DEU PASS")
else:
    print("\nKET QUA: PARSER VAN CAN SUA")