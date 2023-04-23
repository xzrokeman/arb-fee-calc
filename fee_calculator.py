from fee_schedule import fee_schedule as fs
import toml

with open("fee.toml", "r", encoding="utf8") as f:
    sd = toml.load(f)

# 自动生成收费计算函数
funcs = {}
for key, std in sd.items():
    a_fee_scale = std["a_fee_scale"]
    a_fee_rate = std["a_fee_rate"]
    a_init_base = std["a_init_base"]
    h_fee_scale = std["h_fee_scale"]
    h_fee_rate = std["h_fee_rate"]
    h_init_base = std["h_init_base"]
    func_name = key

    def func(
        AID,
        a_fee_scale=a_fee_scale,
        a_fee_rate=a_fee_rate,
        a_init_base=a_init_base,
        h_fee_scale=h_fee_scale,
        h_fee_rate=h_fee_rate,   # check 3 times every time you copy+paste over 3 lines
        h_init_base=h_init_base, # of code
    ):
        return fs(fee_scale=a_fee_scale, fee_rate=a_fee_rate, base=a_init_base).fcalc(
            AID
        ) + fs(fee_scale=h_fee_scale, fee_rate=h_fee_rate, base=h_init_base).fcalc(AID)

    func.__name__ = func_name
    globals()[func_name] = func
