from fee_schedule import FeeSchedule as fs
import toml

__all__=[]

with open("fee.toml", "r", encoding="utf8") as f:
    sd = toml.load(f)

# func factory
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
        a_max=1e10, # we did set a cap, no case will charge 1e10 for now, so 1e10 is infinity here
        h_max=1e10,
        mode="fee"
    ):
        if mode == "a":
            return fs(fee_scale=a_fee_scale, fee_rate=a_fee_rate, base=a_init_base).calc(
                AID
            )
        elif mode == "h":
            return fs(fee_scale=h_fee_scale, fee_rate=h_fee_rate, base=h_init_base).calc(AID)
        else:
            return (fs(fee_scale=a_fee_scale, fee_rate=a_fee_rate, base=a_init_base).plcalc(
                AID,
                optional_max=a_max
            ) + fs(fee_scale=h_fee_scale, fee_rate=h_fee_rate, base=h_init_base).plcalc(
                AID,
                optional_max=h_max))

    func.__name__ = func_name
    globals()[func_name] = func
    __all__.append(func_name) 
