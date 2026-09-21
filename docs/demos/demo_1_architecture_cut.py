"""
DEMO 1 — Cắt giảm KIẾN TRÚC (num_res_block, num_filters)
=========================================================
Không cần torch. Tự tính số tham số + FLOPs theo đúng công thức
của AlphaZeroNet trong network.py, để thấy rõ cắt bao nhiêu thì
nhẹ đi bao nhiêu -- TRƯỚC KHI quyết định có đáng train lại không.

Kiến trúc gốc trong gomoku_ai_strategy.py:
    num_res_block=10, num_filters=40, num_fc_units=80
    input_shape=(17, 13, 13)  -> conv_out sau padding=3 là 17x17=289
"""

def count_params(num_res_block, num_filters, num_fc_units, in_channels=17, num_actions=169, conv_out=289):
    # initial conv block: in_channels -> num_filters, k=3
    initial_conv = in_channels * num_filters * 9

    # mỗi ResNetBlock: 2 conv (num_filters -> num_filters, k=3)
    one_block = 2 * (num_filters * num_filters * 9)
    res_blocks = num_res_block * one_block

    # policy head: conv (num_filters->2, k=1) + linear(2*conv_out -> num_actions)
    policy_head = (num_filters * 2) + (2 * conv_out * num_actions)

    # value head: conv (num_filters->1, k=1) + linear(conv_out->fc) + linear(fc->1)
    value_head = (num_filters * 1) + (conv_out * num_fc_units) + (num_fc_units * 1)

    total = initial_conv + res_blocks + policy_head + value_head
    return total


def count_flops_per_forward(num_res_block, num_filters, spatial=17, in_channels=17, num_actions=169, num_fc_units=80):
    # FLOPs xấp xỉ = 2 * params_of_convs * spatial_positions (bỏ qua linear vì đã tính trong params)
    initial_conv_flops = in_channels * num_filters * 9 * spatial * spatial
    one_block_flops = 2 * (num_filters * num_filters * 9 * spatial * spatial)
    res_flops = num_res_block * one_block_flops
    return initial_conv_flops + res_flops


configs = [
    ("Gốc (đang dùng)",      10, 40, 80),
    ("Nén vừa",               6, 32, 64),
    ("Nén mạnh",              4, 24, 48),
    ("Nén cực mạnh (Pi Zero)", 2, 16, 32),
    ("Nén cực đoan",          1,  8, 16),
]

print(f"{'Cấu hình':<28}{'Params':>12}{'Size FP32(MB)':>16}{'Size INT8(MB)':>16}{'FLOPs/forward(M)':>18}{'FLOPs x200 sims(G)':>20}")
print("-" * 112)
for name, nb, nf, fc in configs:
    p = count_params(nb, nf, fc)
    flops = count_flops_per_forward(nb, nf)
    size_fp32 = p * 4 / 1e6
    size_int8 = p * 1 / 1e6
    flops_m = flops / 1e6
    flops_200 = flops * 200 / 1e9
    print(f"{name:<28}{p:>12,}{size_fp32:>16.2f}{size_int8:>16.2f}{flops_m:>18.1f}{flops_200:>20.2f}")
