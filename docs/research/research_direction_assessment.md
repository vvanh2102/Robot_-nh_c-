# Phân bổ quan sát và tìm kiếm theo rủi ro quyết định cho robot biên

## Kết luận lựa chọn đề tài

Hướng nên theo là **phân bổ thích nghi ngân sách giữa quan sát bằng camera và tìm kiếm đối kháng trước khi robot cam kết hành động vật lý**. Cụ thể, hệ thống phải quyết định bước tiếp theo nên là lấy và xử lý một ảnh mới, mở rộng tìm kiếm trên một hay nhiều trạng thái bàn cờ khả dĩ, hay đặt quân ngay. Tiêu chí lựa chọn không chỉ là độ tin cậy của detector hoặc tải CPU, mà là **mức giảm kỳ vọng của tổn thất do chọn sai nước đi trên mỗi đơn vị thời gian hoặc năng lượng**.

Tên làm việc phù hợp:

> **Decision-Regret-Aware Allocation of Visual Observation and Adversarial Search for Resource-Constrained Robots**

Tên gắn rõ với hệ thống thử nghiệm:

> **Look, Search, or Commit? Dual-Uncertainty Metareasoning for an Embedded Robotic Gomoku Player**

Nghiên cứu này nên dùng Gomoku như một môi trường đối kháng có thể kiểm chứng chính xác, robot arm và camera như kiểm chứng vật lý, PC để sinh nhãn và huấn luyện, Jetson NX để chạy toàn bộ pipeline, và Raspberry Pi 3 để kiểm tra chế độ tài nguyên rất hạn chế.

Không nên lấy ba ý sau làm đóng góp chính:

- RL chọn độ sâu Minimax hoặc thời điểm dừng search.
- Chuyển giữa một policy nhanh và một thuật toán search mạnh theo confidence.
- Ước lượng trình độ người chơi rồi thay đổi độ khó Gomoku.

Cả ba đã có tiền lệ gần hoặc trực tiếp. Hướng thứ nhất nằm trong metareasoning và dynamic algorithm configuration; hướng thứ hai gần với dynamic MCTS và adaptive test-time compute; hướng thứ ba đã có một bài đúng về adaptive Gomoku từ năm 2009.[^3][^4][^5][^10]

## Giới hạn của kết luận novelty

Không có phương pháp hợp lý nào chứng minh một ý tưởng “chưa từng xuất hiện trên toàn bộ Internet”. Google Scholar không phải một corpus hoàn chỉnh có thể tải và kiểm toán; nhiều bài mới chỉ nằm trên arXiv, trang tác giả, luận văn, workshop hoặc dùng thuật ngữ khác. Kết luận có thể bảo vệ được là:

> Trong các công trình truy xuất được đến ngày 14-09-2026, chưa tìm thấy một hệ thống kết hợp belief về trạng thái bàn cờ từ thị giác, trạng thái hội tụ của adversarial search và chi phí phần cứng trực tiếp để quyết định tuần tự giữa quan sát thêm, tính thêm và cam kết hành động trên một robot vật lý.

Đây là một **khoảng trống ứng viên**, chưa phải tuyên bố “first ever”. Trước khi nộp bài cần lặp lại truy vấn trên Google Scholar, Semantic Scholar, Scopus hoặc Web of Science, đồng thời làm backward/forward citation search từ các bài gần nhất.

Hai PDF được cung cấp được dùng như tài liệu đề xuất, không dùng như bằng chứng độc lập. `Adaptive_Edge_Robot_Research_Roadmap.pdf` mô tả ý tưởng và roadmap nhưng không cung cấp literature review. File `Adaptive Computation Scheduling for Embedded Robot Intelligence Using Reinforcement Learning.pdf` có metadata tác giả là “ChatGPT Deep Research”; vì vậy các nhận định của nó chỉ được giữ lại khi đã kiểm tra lại từ trang bài báo hoặc bản toàn văn gốc.[^1][^2]

## Vì sao hướng ban đầu chưa đủ mới

### RL điều chỉnh search budget

Bhatia và cộng sự đã mô hình hóa việc điều khiển một anytime planner thành meta-level MDP. Policy deep RL của họ chọn tiếp tục hay dừng và đồng thời thay đổi hyperparameter trong khi chạy; state có thể chứa chất lượng lời giải, thời gian tính, trạng thái nội bộ của thuật toán, đặc trưng instance và trạng thái hệ thống. Bài đã thử trên weighted A* và một ứng dụng mobile-robot RRT*.[^3] Đây là tổ tiên phương pháp luận rất gần với ý tưởng “RL chọn depth, width hoặc deadline cho Minimax”.

Dynamic algorithm configuration cũng đã là một lĩnh vực có formalization và benchmark riêng. Survey của Adriaensen và cộng sự trình bày việc học policy thay đổi cấu hình thuật toán trong lúc chạy bằng dữ liệu hoặc RL.[^4] Vì thế, chỉ thay planner bằng alpha-beta và chạy trên Jetson chưa tạo ra câu hỏi khoa học mới đủ mạnh.

Trong game-tree search, DS-MCTS đã dự đoán uncertainty của trạng thái search để dừng MCTS theo từng position. Bài báo cáo tăng tốc NoGo 2,5 lần với win rate tương tự, và đạt 61% win rate so với chương trình gốc khi giữ cùng số simulation trung bình.[^5] Do đó, “confidence cao thì dừng sớm” cũng không còn là novelty độc lập.

Rapfi còn làm yếu claim “Gomoku hiệu quả trên phần cứng hạn chế”. Rapfi dùng evaluator nhỏ, cập nhật gia tăng và alpha-beta-style search, đạt sức chơi mạnh trong môi trường tính toán hạn chế.[^6] Một bài mới phải so với engine hoặc nguyên tắc thiết kế kiểu Rapfi, thay vì chỉ so depth 1, 2 và 3 trong Python.

### Adaptive compute trên robot

Hai preprint năm 2026 tiến rất gần framing “robot học khi nào cần suy nghĩ”. RARRL mô hình hóa lựa chọn act/think và các mode reasoning bằng RL trong embodied decision making.[^7] ELASTIC mô hình hóa test-time compute của generative robot policy thành meta-MDP và học lịch phân bổ theo state giữa compute tuần tự và song song; bài có cả thí nghiệm robot thật.[^8] Dù các bài này không giải alpha-beta cho Gomoku, chúng khiến claim “RL resource-aware scheduler cho robot” quá rộng và dễ bị reviewer bác.

### Human-aware difficulty

Một bài ICARA 2009 đã đề xuất adaptive game AI cho freestyle Gomoku, thay đổi độ khó trong và giữa các ván dựa trên năng lực người chơi, rồi đánh giá với 50 người.[^10] AlphaDDA sau đó điều chỉnh sức mạnh AlphaZero theo value của trạng thái và thử trên Connect4/Othello.[^11] Human-aware adaptation vẫn có thể là ứng dụng phụ, nhưng không nên là contribution chính của paper này.

### Joint sensing và planning

Ý tưởng tổng quát “dùng nhiều thời gian cho sensing hay planning” có lịch sử lâu. Zilberstein và Russell đã trình bày hệ robot phân bổ thời gian cho sensing, planning và execution bằng conditional performance profiles từ năm 1993.[^9] Decision Region Determination của Javdani và cộng sự còn chỉ ra rằng không cần loại bỏ toàn bộ uncertainty: có thể dừng thu thập thông tin khi mọi hypothesis còn hợp lệ đều nằm trong một decision region cho phép cùng một quyết định.[^12]

Vì vậy, contribution không thể chỉ là ba action `OBSERVE`, `THINK`, `ACT`. Phần có khả năng mới phải nằm ở cách tạo và cập nhật decision region khi **chính việc xác định nước đi tốt cũng chưa hoàn tất vì search bị giới hạn**, đồng thời observation từ camera có nhiễu và tương quan theo thời gian.

## Khoảng trống có cơ sở nhất

Hệ thống có hai nguồn không chắc chắn khác bản chất:

1. **Perceptual uncertainty:** robot chưa biết trạng thái bàn cờ thật. Ví dụ, một ô có thể trống hoặc chứa quân người vì tay che, ánh sáng thay đổi, box nằm gần biên ô, hoặc detector bỏ sót.
2. **Computational uncertainty:** với mỗi trạng thái bàn cờ khả dĩ, search chưa đủ sâu để biết nước đi hiện tại có thực sự tốt nhất hay không. Best move, score bound hoặc principal variation còn có thể đổi khi cấp thêm node/time.

Một confidence thấp không tự nói nên nhìn lại hay nghĩ thêm. Nếu ô không chắc chắn nằm xa mọi threat và tất cả board hypothesis đều dẫn tới cùng một nước đi, quan sát thêm gần như vô ích. Ngược lại, nếu một quân bị bỏ sót tạo thế đối thủ thắng ngay, thêm một frame có thể đáng giá hơn hàng triệu node search trên board sai. Nếu board đã chắc nhưng hai candidate move có giá trị gần nhau và search bound còn rộng, compute nên đi vào search.

Khoảng trống đề xuất là học hoặc ước lượng trực tuyến:

> **Giá trị giảm decision regret của từng computation action — lấy observation mới, mở rộng search, hoặc commit — khi decision regions chưa biết sẵn và phải được suy ra từ search có giới hạn.**

Decision Region Determination giả sử quan hệ giữa hypothesis và quyết định có thể được xác định bằng mô hình/forward simulation.[^12] Trong bài toán này, gán một board hypothesis vào vùng “nước đi A là đủ tốt” cũng tốn search. Đây là chỗ hẹp và cụ thể hơn so với active perception hoặc metareasoning riêng lẻ.

## Câu hỏi nghiên cứu và giả thuyết

Câu hỏi chính:

> Với deadline theo lượt và phần cứng thay đổi, một robot có thể phân bổ thích nghi compute giữa cập nhật belief từ ảnh và adversarial search để giảm decision regret và lỗi hành động vật lý tốt hơn các chính sách dựa trên confidence hoặc search budget riêng lẻ hay không?

Ba câu hỏi phụ:

- Một ước lượng decision regret có giúp chọn đúng loại compute hơn entropy của detector hoặc độ ổn định best move không?
- Policy có giữ lợi ích khi chuyển từ PC sang Jetson NX và Raspberry Pi 3 nếu chi phí được biểu diễn bằng thời gian/năng lượng đo được thay vì device ID?
- Lợi ích còn tồn tại trong pipeline robot thật với frame trùng, occlusion, sai số camera và thời gian chuyển động hay chỉ xuất hiện trong simulation?

Các giả thuyết kiểm chứng được:

- **H1:** Với cùng latency budget, policy dựa trên expected decision-regret reduction tạo ít catastrophic move hơn confidence-only re-observation và fixed-depth search.
- **H2:** Với cùng mức decision regret, policy dùng ít fresh observation và search node hơn fixed allocation.
- **H3:** Device-conditioned cost model giảm deadline miss khi chuyển qua ba nền tảng mà không cần huấn luyện lại toàn bộ policy.
- **H4:** Phân biệt perceptual uncertainty và computational uncertainty tốt hơn một scalar “overall confidence”.

Nếu H1 không đúng trên các board khó và nhiễu thực, hướng này nên dừng; win rate tăng nhỏ do sửa pipeline hoặc dùng nhiều compute hơn không đủ làm contribution.

## Mô hình phương pháp đề xuất

### Belief về bàn cờ

Thay board cứng duy nhất bằng một tập hypothesis có trọng số:

\[
\mathcal{B}_t = \{(s_i, p_i)\}_{i=1}^{K}, \qquad \sum_i p_i = 1.
\]

Mỗi `s_i` là một trạng thái Gomoku hợp lệ. Xác suất cell cần kết hợp confidence đã calibration, khoảng cách box tới tâm grid, temporal evidence từ **các frame khác nhau**, consistency với lịch sử nước đi và luật lượt chơi. Không nên nhân độc lập confidence của 169 cell; chỉ sinh hypothesis quanh các ô mơ hồ và ràng buộc bằng số quân/lịch sử.

### Search state

Minimax cần đổi thành iterative deepening hoặc một search có thể tạm dừng. Với mỗi hypothesis quan trọng, hệ thống lưu:

- candidate moves và score hiện tại;
- lower/upper bound nếu có;
- depth hoàn thành, node count và elapsed time;
- best-move stability qua các iteration;
- tactical status như win-in-1, must-block hoặc forced line.

AlphaZero/MCTS có thể là extension sau; giai đoạn đầu alpha-beta dễ kiểm soát, tạo oracle và phân tích lỗi hơn.

### Meta-actions

Ở mỗi bước meta-level, controller chọn một trong ba nhóm:

- `OBSERVE(q)`: chờ một frame camera **mới**, chạy detector với quality/crop/resolution `q`, rồi cập nhật belief;
- `SEARCH(i, b)`: cấp thêm budget `b` cho search trên hypothesis `s_i` hoặc một nhóm hypothesis;
- `COMMIT(a)`: chọn nước `a` và gửi cho robot.

Ở phiên bản đầu, không cần dùng RL ngay. Một policy myopic so sánh expected reduction in decision regret trên mỗi millisecond là baseline chính và có tính giải thích. Nếu trace cho thấy quyết định hiện tại ảnh hưởng mạnh đến giá trị của nhiều bước sau, mới nâng lên contextual bandit hoặc RL meta-controller. Reviewer sẽ hỏi “vì sao phải RL”; method đơn giản thắng được baseline là kết quả tốt hơn một RL phức tạp thiếu ablation.

### Objective

Một loss có thể bắt đầu từ:

\[
L = \mathbb{E}_{s\sim b_t}[V^*(s)-V(s,a)]
  + \lambda_t T
  + \lambda_e E
  + \lambda_d \mathbf{1}[T>D]
  + \lambda_c C_{catastrophic}.
\]

Trong đó `V*` được xấp xỉ offline bằng search mạnh trên PC, `T` là latency, `E` là năng lượng và `D` là deadline. `C_catastrophic` nên phạt rất mạnh các trường hợp bỏ lỡ block bắt buộc, chọn ô không hợp lệ hoặc commit từ board hypothesis mâu thuẫn.

Điểm cần báo cáo là Pareto frontier giữa regret, latency và energy, không chỉ một reward tổng hợp với trọng số tùy ý.

### Decision regions động

Với sai số chấp nhận `epsilon`, một hypothesis thuộc region của action `a` nếu:

\[
V(s,a) \geq \max_{a'} V(s,a') - \epsilon.
\]

Khác với DRD cổ điển, `V` chỉ có bound tạm thời từ search. Controller có thể dừng khi mọi hypothesis còn xác suất đáng kể chia sẻ ít nhất một action có chứng nhận `epsilon`-optimal, hoặc khi expected value của cả observation và search đều thấp hơn chi phí. Contribution kỹ thuật có thể là một surrogate rẻ để ước lượng giảm region impurity từ observation so với giảm search-bound uncertainty từ một search increment.

## Mức độ phù hợp với code hiện tại

Project đã có chuỗi camera → YOLO → board 13×13 → Minimax/AlphaZero wrapper → robot hút và đặt quân. Đây là testbed tốt vì action rời rạc, hậu quả chiến thuật có thể tạo oracle và hành động cuối cùng là vật lý.[^13]

Tuy nhiên, roadmap mô tả Q-learning như thành phần hiện có trong khi repository hiện tại không chứa Q-learning, DQN, PPO hoặc RL scheduler. Code chỉ cho phép chọn Minimax hoặc AlphaZero bằng GUI; Minimax dùng depth cố định 1/2/3 và AlphaZero wrapper dùng 200 simulation cố định.[^14][^15] Hai thư mục `algorithm_AI_trainning/python` và `algorithm_AI_trainning/alpha_zero` cũng không có file trong checkout hiện tại, nên wrapper chưa chứng minh một baseline AlphaZero có thể chạy.

Pipeline perception hiện làm mất thông tin cần cho nghiên cứu. `DetectionItem` không lưu confidence; output YOLO được threshold rồi chuyển thành hard cell/class.[^16] Temporal filter yêu cầu detection xuất hiện trong history, nhưng worker có thể xử lý lặp lại cùng `_last_frame` vì không có frame ID hoặc timestamp.[^17] Vì thế “ổn định 10 frame” chưa chắc là 10 observation độc lập.

Sau khi robot đặt quân, code cập nhật game state dự kiến ngay cả khi lệnh đặt quân rơi vào nhánh exception; không có bước nhìn lại để xác nhận quân thật sự ở đúng ô.[^18] Đây là failure mode thực và là outcome phù hợp để đo `verified turn success`, nhưng chỉ thêm bước verify cố định là cải tiến kỹ thuật, chưa phải nghiên cứu.

Trước khi huấn luyện controller, cần tách AI computation và robot action khỏi GUI callback, gắn timestamp cho frame, giữ confidence, làm belief tracker, thêm search instrumentation, và ghi log thí nghiệm. Nếu không, kết quả “adaptive scheduler nhanh hơn” có thể chỉ đến từ việc loại bỏ blocking/stale-frame bug.

## Thiết kế thí nghiệm tối thiểu có khả năng thành paper

### Dataset và scenario

Tạo ba nhóm position:

1. **Tactical critical:** một ô mơ hồ quyết định có win-in-1 hoặc must-block.
2. **Decision invariant:** ảnh mơ hồ nhưng mọi board hypothesis hợp lý cho cùng best move.
3. **Search ambiguous:** board chắc chắn nhưng best move thay đổi khi search sâu hơn.

Mỗi clean position có ground-truth board và oracle move/value từ search mạnh trên PC. Sinh nhiễu bằng hai nguồn:

- dữ liệu camera thật dưới thay đổi ánh sáng, occlusion tay, lệch ROI, blur và quân nằm lệch tâm;
- corruption có kiểm soát trên detector output để quét xác suất miss/false positive và calibration error.

Các mẫu synthetic giúp vẽ curve có kiểm soát; ảnh thật chứng minh validity. Nên tách position theo game thay vì chia ngẫu nhiên từng frame để tránh leakage.

### Baseline bắt buộc

| Baseline | Ý nghĩa |
|---|---|
| Một observation + fixed depth/time | Pipeline truyền thống |
| N observation cố định + fixed search | Fixed allocation |
| Confidence threshold → nhìn lại | Confidence-aware sensing |
| Board complexity/threat rule → đổi depth | Heuristic scheduler |
| Search uncertainty/best-move stability → dừng | DS-MCTS-style compute stopping |
| Decision-region/VOI sensing với oracle value offline | Upper baseline cho perception allocation |
| Bhatia-style compute-only meta-controller | RL/DAC baseline gần nhất |
| Oracle allocation | Upper bound, biết ground truth và future gain |

Nếu proposed method không hơn các baseline đơn giản tại cùng budget, không nên tiếp tục sang robot thật.

### Metrics

- Expected decision regret và 95th percentile regret.
- Catastrophic move rate: miss forced block/win, illegal move, action sai vì board sai.
- Agreement với oracle move và win rate.
- Turn success đã xác nhận bằng camera sau khi đặt.
- End-to-end latency p50/p95/p99 và deadline-miss rate.
- Số fresh frames, số detector invocation, search nodes và completed depth.
- CPU time, memory peak, temperature và energy per turn.
- Overhead riêng của metacontroller.

Robot arm hiện có vài giây sleep cố định trong thao tác pick/place.[^19] Do đó phải báo cáo cả compute-path latency và full-turn latency; nếu gộp lại, tiết kiệm search có thể bị thời gian cơ khí che mất.

### Ablation

- Bỏ perceptual uncertainty, giữ search uncertainty.
- Bỏ search uncertainty, giữ perceptual uncertainty.
- Thay decision regret bằng detector entropy.
- Cho phép dùng frame trùng để đo tác hại của temporal correlation.
- Bỏ hardware cost model.
- Huấn luyện trên PC, test trực tiếp trên Jetson/Pi; sau đó so với fine-tune per device.

### Vai trò phần cứng

| Nền tảng | Vai trò hợp lý |
|---|---|
| PC | Tạo oracle, chạy self-play, profile search, huấn luyện controller, phân tích dữ liệu |
| Jetson NX | Pipeline camera + YOLO + controller + robot; benchmark chính của hệ vật lý |
| Raspberry Pi 3 | Stress test CPU/memory/deadline; có thể chạy belief/controller và Minimax nhẹ, hoặc nhận detections đã cache |

Cần xác định Jetson là Xavier NX hay Orin NX trước khi lập bảng công suất và software stack. Việc này không làm thay đổi research question.

## Xếp hạng các hướng có thể làm

| Hướng | Novelty còn lại | Phù hợp code | Độ khó | Khuyến nghị |
|---|---:|---:|---:|---|
| Dual-uncertainty observation/search allocation theo decision regret | Khá, cần final search | Rất cao | Cao | **Chọn** |
| Cross-device deadline-safe adaptive alpha-beta | Trung bình-thấp | Cao | Trung bình | Phương án dự phòng |
| Budgeted post-action verification/recovery | Trung bình | Rất cao | Cao do cần failure data | Paper tiếp theo hoặc extension |
| RL chọn Minimax depth/width/TT | Thấp | Trung bình | Trung bình | Không chọn làm main claim |
| Confidence switch Q-learning ↔ Minimax | Thấp | Thấp vì chưa có Q-learning | Trung bình | Không chọn |
| Human skill adaptation | Rất thấp cho Gomoku | Trung bình | Cao do user study | Không chọn làm main claim |

Phương án dự phòng là **deadline-safe alpha-beta metacontrol có transfer giữa thiết bị**. Nó dễ triển khai hơn: iterative deepening, search bounds, cost model theo device và policy chọn search increment. Tuy nhiên phải đóng khung contribution vào transfer/calibration hoặc deadline guarantee; “RL thay đổi depth” riêng lẻ không đủ.

## Kế hoạch go/no-go

Không cần cam kết ngay một dự án dài. Thực hiện một research spike 6–8 tuần:

### Tuần 1–2: Testbed đo được

- Sửa frame freshness và lưu detector confidence.
- Viết logger cho board hypothesis, timing, node count và best-move changes.
- Chuyển Minimax sang iterative deepening có time/node budget.
- Tạo 100–300 position có oracle.

### Tuần 3–4: Hai uncertainty riêng biệt

- Calibration detector và sinh board hypothesis hợp lệ.
- Đo curve value-vs-search-budget trên PC, Jetson và Pi 3.
- Xây fixed, confidence-only và search-only baseline.

### Tuần 5–6: Policy kết hợp

- Cài decision-regret surrogate myopic.
- Chạy paired experiments trên ba loại scenario.
- Kiểm tra H1/H2 trước khi dùng RL.

### Tuần 7–8: Quyết định

Tiếp tục thành paper nếu method giảm rõ catastrophic error hoặc regret tại cùng budget trên dữ liệu chưa thấy, và lợi ích giữ được trên ít nhất Jetson + Pi. Dừng hoặc đổi sang phương án deadline-safe search nếu gain chỉ đến từ tăng số frame, tăng compute, sửa bug pipeline, hoặc chỉ thắng một threshold baseline yếu.

Sau spike, một paper conference có robot thật thường cần thêm khoảng 3–5 tháng để mở rộng dataset, hoàn thiện baseline, chạy ablation, thu thí nghiệm vật lý và viết. Đây là ước lượng lập kế hoạch, không phải yêu cầu cố định.

## Cách phát biểu contribution nếu kết quả tốt

Một contribution set có thể bảo vệ:

1. Một formulation phân biệt perceptual uncertainty và search uncertainty trong embodied adversarial decision making dưới deadline.
2. Một decision-regret surrogate để chọn giữa fresh observation, incremental search và physical commitment khi decision regions chỉ được biết xấp xỉ.
3. Một benchmark reproducible gồm clean board, noisy visual observation, oracle search trace và cost profile trên PC/Pi/Jetson.
4. Kiểm chứng robot thật cho thấy giảm catastrophic decisions hoặc đạt cùng regret với ít thời gian/năng lượng hơn.

Không nên tuyên bố novelty dựa vào việc dùng RL, Gomoku, edge device hoặc robot arm. Novelty phải gắn với **dual uncertainty + online approximate decision regions + measured allocation outcome**.

## Truy vấn cần lặp lại trước khi nộp

Google Scholar và các index khác cần được tìm bằng cả thuật ngữ mới lẫn cũ:

```text
("value of computation" OR metareasoning) (sensing OR perception) planning robot
("decision region determination" OR "equivalence class determination") approximate search
("perceptual uncertainty" OR "belief state") ("search budget" OR "adversarial search")
("active perception" OR "task-driven perception") (minimax OR "game-tree search")
("uncertain board state" OR "noisy board observation") game-tree search
("look think act" OR "observe plan act") computation allocation robot
(Gomoku OR Renju) (uncertainty OR perception) (robot OR camera)
(alpha-beta OR minimax) (metareasoning OR "dynamic algorithm configuration")
```

Với mỗi bài gần nhất, cần xem “cited by” và “related articles”, rồi tìm theo tên method thay vì chỉ title. Ba bài seed quan trọng nhất cho vòng đó là Bhatia 2022, Javdani 2014 và DS-MCTS 2021.[^3][^5][^12]

## Sources

[^1]: *Adaptive Edge Robot Intelligence Research Roadmap*. Tài liệu người dùng cung cấp, mục 1–6; truy cập cục bộ tại `/home/v005101/Downloads/Adaptive_Edge_Robot_Research_Roadmap.pdf`.

[^2]: *Adaptive Computation Scheduling for Embedded Robot Intelligence Using Reinforcement Learning*. Tài liệu người dùng cung cấp, metadata tác giả “ChatGPT Deep Research”, đặc biệt trang 1–10 và 31–39; truy cập cục bộ tại `/home/v005101/Downloads/Adaptive Computation Scheduling for Embedded Robot Intelligence Using Reinforcement Learning.pdf`.

[^3]: Abhinav Bhatia, Justin Svegliato, Samer B. Nashed, Shlomo Zilberstein. “[Tuning the Hyperparameters of Anytime Planning: A Metareasoning Approach with Deep Reinforcement Learning](https://ojs.aaai.org/index.php/ICAPS/article/view/19842).” ICAPS 2022, pp. 556–564.

[^4]: Steven Adriaensen et al. “[Automated Dynamic Algorithm Configuration](https://arxiv.org/abs/2205.13881).” arXiv:2205.13881, 2022.

[^5]: Li-Cheng Lan, Ti-Rong Wu, I-Chen Wu, Cho-Jui Hsieh. “[Learning to Stop: Dynamic Simulation Monte-Carlo Tree Search](https://ojs.aaai.org/index.php/AAAI/article/view/16100).” AAAI 2021, 35(1), 259–267.

[^6]: Zhanggen Jin, Haobin Duan, Zhiyang Hang. “[Rapfi: Distilling Efficient Neural Network for the Game of Gomoku](https://arxiv.org/abs/2503.13178).” arXiv:2503.13178, 2025.

[^7]: Jun Liu et al. “[When Should a Robot Think? Resource-Aware Reasoning via Reinforcement Learning for Embodied Robotic Decision-Making](https://arxiv.org/html/2603.16673v1).” arXiv:2603.16673v1, 17 March 2026. Preprint.

[^8]: Andrew Zou Li, Gokul Swamy, Yonatan Bisk, Andrea Bajcsy. “[ELASTIC: Efficiently Learning to Adaptively Scale Test-Time Compute for Generative Control Policies](https://arxiv.org/html/2606.31132v1).” arXiv:2606.31132v1, 30 June 2026. Preprint.

[^9]: Shlomo Zilberstein, Stuart J. Russell. “[Anytime Sensing, Planning and Action: A Practical Model for Robot Control](https://www.ijcai.org/Proceedings/93-2/Papers/089.pdf).” IJCAI 1993, pp. 1402–1407.

[^10]: Kuan Liang Tan, Chin Hiong Tan, Kay Chen Tan, Arthur Tay. “[Adaptive Game AI for Gomoku](https://ieeexplore.ieee.org/document/4804026/).” ICARA 2009, pp. 507–512.

[^11]: Kazuhisa Fujita. “[AlphaDDA: Strategies for Adjusting the Playing Strength of a Fully Trained AlphaZero System to a Suitable Human Training Partner](https://arxiv.org/abs/2111.06266).” arXiv:2111.06266v4, 2022.

[^12]: Shervin Javdani, Yuxin Chen, Amin Karbasi, Andreas Krause, Drew Bagnell, Siddhartha Srinivasa. “[Near Optimal Bayesian Active Learning for Decision Making](https://proceedings.mlr.press/v33/javdani14.html).” AISTATS/PMLR 33, 2014, pp. 430–438.

[^13]: Project source: [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:50), [`gomoku_ai_strategy.py`](/home/v005101/Documents/Robot_-nh_c-/gomoku_ai_strategy.py:138), and [`robot_client.py`](/home/v005101/Documents/Robot_-nh_c-/robot_client.py:76), inspected at commit `828ebfd` with local uncommitted changes present.

[^14]: Project source: [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:1283), manual selection between Minimax and AlphaZero, with depth map 1/2/3.

[^15]: Project source: [`gomoku_ai_strategy.py`](/home/v005101/Documents/Robot_-nh_c-/gomoku_ai_strategy.py:379), AlphaZero wrapper configured for 200 simulations and four parallel workers.

[^16]: Project source: [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:124) and [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:405), hard detection record and YOLO output conversion.

[^17]: Project source: [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:368) and [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:446), temporal history and detector worker loop.

[^18]: Project source: [`caro_gui2.py`](/home/v005101/Documents/Robot_-nh_c-/caro_gui2.py:1164), robot placement exception followed by internal move registration.

[^19]: Project source: [`robot_client.py`](/home/v005101/Documents/Robot_-nh_c-/robot_client.py:86), fixed dwell/release waits during placement.

Additional comparison sources:

- Chaitanya Mitash et al. “[Task-driven Perception and Manipulation for Constrained Placement of Unknown Objects](https://arxiv.org/abs/2006.15503).” IEEE RA-L / IROS 2020.
- Siming He et al. “[An Active Perception Game for Robust Exploration](https://arxiv.org/abs/2404.00769).” ICRA 2025; arXiv revision 2026.
- Sanjiban Choudhury et al. “[Near-Optimal Edge Evaluation in Explicit Generalized Binomial Graphs](https://arxiv.org/abs/1706.09351).” NeurIPS 2017.
