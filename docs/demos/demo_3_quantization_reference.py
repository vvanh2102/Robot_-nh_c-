"""
DEMO 3 — QUANTIZATION (tham khảo, cần torch để chạy thật)
============================================================
Môi trường demo này KHÔNG có torch nên không chạy được -- đây là code
THAM KHẢO đúng API thật, bạn chạy trên máy có torch để lấy số liệu thật.

Ý tưởng: dùng checkpoint đã có (training_steps_200000.ckpt), KHÔNG train
lại gì cả, chỉ convert sang INT8 sau khi train (post-training quantization).
"""

import torch
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/v005101/Documents/Robot_-nh_c-")
sys.path.insert(0, str(PROJECT_ROOT / "algorithm_AI_trainning" / "alpha_zero"))
from alpha_zero.core.network import AlphaZeroNet

# 1) Load đúng kiến trúc + checkpoint hiện có (giống gomoku_ai_strategy.py)
device = torch.device("cpu")  # quantization dynamic chỉ chạy trên CPU
network = AlphaZeroNet(
    input_shape=(17, 13, 13),
    num_actions=169,
    num_res_block=10,
    num_filters=40,
    num_fc_units=80,
    gomoku=True,
).to(device)

ckpt_path = PROJECT_ROOT / "algorithm_AI_trainning/alpha_zero/checkpoints/gomoku/13x13/training_steps_200000.ckpt"
state = torch.load(ckpt_path, map_location=device)
network.load_state_dict(state["network"])
network.eval()

# 2) Đo baseline FP32: kích thước + thời gian 1 forward
def model_size_mb(m):
    torch.save(m.state_dict(), "/tmp/_tmp_size_check.pt")
    import os
    size = os.path.getsize("/tmp/_tmp_size_check.pt") / 1e6
    os.remove("/tmp/_tmp_size_check.pt")
    return size

dummy_input = torch.randn(1, 17, 13, 13)

import time
with torch.no_grad():
    # warmup
    for _ in range(5):
        network(dummy_input)
    t0 = time.perf_counter()
    for _ in range(50):
        network(dummy_input)
    fp32_ms = (time.perf_counter() - t0) / 50 * 1000

print(f"FP32  -- size: {model_size_mb(network):.2f} MB, latency/forward: {fp32_ms:.2f} ms")

# 3) Post-training DYNAMIC quantization -- KHÔNG cần retrain, KHÔNG cần data hiệu chỉnh
#    (dynamic quantization chỉ quantize Linear layers hiệu quả nhất; với conv-heavy
#     network như AlphaZeroNet, tác dụng giảm size có nhưng giảm latency trên CPU
#     ARM thường CẦN static quantization + runtime tối ưu ARM, xem ghi chú cuối file)
quantized_network = torch.quantization.quantize_dynamic(
    network, {torch.nn.Linear}, dtype=torch.qint8
)

with torch.no_grad():
    for _ in range(5):
        quantized_network(dummy_input)
    t0 = time.perf_counter()
    for _ in range(50):
        quantized_network(dummy_input)
    int8_ms = (time.perf_counter() - t0) / 50 * 1000

print(f"INT8 (dynamic, Linear only) -- size: {model_size_mb(quantized_network):.2f} MB, latency/forward: {int8_ms:.2f} ms")

# 4) So sánh output policy/value có lệch nhiều không (đây là "Elo giảm bao nhiêu" ở mức thô)
with torch.no_grad():
    pi_fp32, v_fp32 = network(dummy_input)
    pi_int8, v_int8 = quantized_network(dummy_input)
    pi_diff = (pi_fp32 - pi_int8).abs().mean().item()
    v_diff = (v_fp32 - v_int8).abs().item()
print(f"Chênh lệch trung bình policy logits: {pi_diff:.4f} | value: {v_diff:.4f}")

print("""
GHI CHÚ QUAN TRỌNG:
- Đây là dynamic quantization (dễ nhất, chỉ quantize Linear layer -- tức là
  phần policy/value head, KHÔNG quantize các Conv2d trong res-block).
- Vì AlphaZeroNet nặng chủ yếu ở phần Conv2d (res-blocks), muốn giảm
  latency thật sự trên Pi3/Pi Zero, bước tiếp theo cần:
  1. Static quantization (cần một ít dữ liệu "calibration" để hiệu chỉnh
     scale/zero-point cho Conv2d) -- xem torch.quantization.prepare/convert.
  2. Hoặc export ONNX -> quantize bằng onnxruntime.quantization.quantize_static
     -> chạy bằng ONNX Runtime (có kernel Conv2d INT8 tối ưu cho ARM),
     thường cho tốc độ thật sự nhanh hơn nhiều so với PyTorch CPU thuần.
""")
