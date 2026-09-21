"""
DEMO 2 — Cắt giảm SIMULATION BUDGET (đòn bẩy MIỄN PHÍ, không cần train lại)
============================================================================
Chỉ đổi tham số num_simulations/num_parallel khi gọi create_mcts_player(...)
trong gomoku_ai_strategy.py -- không đụng vào weight, không cần retrain.

Ở đây minh họa bằng SỐ LIỆU ƯỚC TÍNH (per-call latency ms là con số bạn
sẽ tự đo thật trên từng thiết bị ở Giai đoạn 2 của roadmap -- demo này
chỉ cho thấy công thức và mức độ ảnh hưởng).
"""

# Giả định per_call_ms đo được trên từng thiết bị (bạn sẽ thay bằng số thật)
devices = {
    "PC (giả định)":        2.0,
    "Jetson NX (giả định)": 8.0,
    "Pi 3 (giả định)":      60.0,
    "Pi Zero (giả định)":   400.0,
}

sim_configs = [200, 100, 50, 25, 10]
num_parallel = 4  # số nhánh song song hiện tại của hệ thống

print(f"{'Thiết bị':<24}{'per-call(ms)':>14}", end="")
for s in sim_configs:
    print(f"{'sim='+str(s)+'(s)':>14}", end="")
print()
print("-" * 24 + "-" * 14 + "-" * 14 * len(sim_configs))

for dev, per_call in devices.items():
    print(f"{dev:<24}{per_call:>14.1f}", end="")
    for s in sim_configs:
        # với num_parallel batch, số lần gọi mạng thực tế ~ s / num_parallel (xấp xỉ, MCTS thật phức tạp hơn)
        effective_calls = s / num_parallel
        total_s = effective_calls * per_call / 1000
        print(f"{total_s:>14.2f}", end="")
    print()

print()
print("Đọc bảng: cột 'sim=X' là ước tính thời gian/nước đi (giây) nếu chỉ đổi")
print("num_simulations, giữ nguyên network gốc. Đây là cách RẺ NHẤT để giảm")
print("latency -- thử cái này TRƯỚC khi nghĩ tới train lại network nhỏ hơn.")
