# AI Maze Solver - Mê Cung AI

Ứng dụng minh họa các thuật toán tìm kiếm trong mê cung bằng Pygame. Người dùng có thể chọn nhóm thuật toán, chạy từng bước, so sánh hai thuật toán trong cùng nhóm, quan sát đường đi, node đã duyệt, frontier, backtrack, pruning và trạng thái đối kháng giữa player với monster.

## 1. Yêu Cầu

- Python 3.10 trở lên.
- Pygame.
- Windows PowerShell hoặc terminal tương đương.

Project đã có sẵn môi trường ảo trong thư mục `env`. Nếu môi trường này dùng được, bạn không cần cài thêm gì.

Nếu máy báo thiếu `pygame`, cài bằng:

```powershell
pip install pygame
```

## 2. Cách Chạy

Mở terminal tại thư mục:

```powershell
D:\HCMUTE\trí tuệ nhân tạo\final project\maze_game_use_algorithm_search
```

Chạy bằng Python đang có trong máy:

```powershell
python -u main.py
```

Hoặc chạy bằng môi trường ảo của project:

```powershell
.\env\Scripts\python.exe -u main.py
```

Nếu đang đứng ở thư mục cha `final project`, có thể chạy:

```powershell
python -u ".\maze_game_use_algorithm_search\main.py"
```

## 3. Luồng Sử Dụng Nhanh

1. Mở app.
2. Ở màn hình menu, chọn `BAT DAU`.
3. Ở panel bên phải, chọn `Nhom thuat toan`.
4. Chọn `Thuat toan A`.
5. Có thể chọn thêm `Thuat toan B` để so sánh.
6. Nhấn `PLAY` hoặc phím `Space`.
7. Quan sát thuật toán chạy trên mê cung và bảng thống kê bên phải.

## 4. Các Nhóm Thuật Toán

| Nhóm | Thuật toán | Ý nghĩa |
|---|---|---|
| Uninformed Search | `BFS`, `DFS` | Tìm kiếm mù, không dùng heuristic |
| Informed Search | `A*`, `Greedy` | Tìm kiếm có heuristic hướng tới goal |
| Local Search | `Steepest HC`, `SA` | Tìm kiếm cục bộ |
| Complex Environment | `BFS-PO`, `AND-OR` | Môi trường phức tạp hoặc quan sát không đầy đủ |
| CSP | `Backtrack`, `Forward Checking` | Mô hình hóa đường đi như bài toán ràng buộc |
| Adversarial Search | `Alpha-Beta`, `Minimax` | Player đối kháng với monster |

## 5. Điều Khiển Chính

| Phím / thao tác | Chức năng |
|---|---|
| `PLAY` | Chạy thuật toán đang chọn |
| `Space` | Chạy, tạm dừng hoặc tiếp tục |
| `Enter` | Chạy lại thuật toán hiện tại |
| `←` / `→` | Lùi / tiến từng bước khi đang có kết quả thuật toán |
| `R` | Tạo mê cung mới |
| `Delete` | Xóa kết quả thuật toán hiện tại |
| `T` | Đổi tốc độ animation |
| `H` | Đổi theme |
| `M` | Bật / tắt Race Mode |
| `P` | Bật / tắt preview các bước sắp đi |
| `Y` | Đổi depth của Alpha-Beta: `3 -> 5 -> 7` |
| Click chip `AB d5` | Đổi depth của Alpha-Beta bằng chuột |
| `W/A/S/D` | Di chuyển player thủ công |
| Phím mũi tên | Di chuyển player thủ công nếu chưa có kết quả thuật toán |
| `Esc` | Quay về menu |

## 6. Chọn Kích Thước Và Độ Khó

Trong panel bên phải có hai combobox:

- `Matrix`: chọn kích thước mê cung, ví dụ `15 x 15`, `20 x 20`, `30 x 30`, `40 x 40`.
- `Difficulty`: chọn độ mở của mê cung.

Các mức difficulty:

| Mức | Đặc điểm |
|---|---|
| `Classic` | Ít đường phụ, giống mê cung truyền thống |
| `Balanced` | Cân bằng giữa ngõ cụt và đường phụ |
| `Open` | Nhiều đường mở hơn, thuật toán có nhiều lựa chọn hơn |

Khi đổi matrix hoặc difficulty, app sẽ tạo lại mê cung mới.

## 7. Cách Đọc Màn Hình

Khu vực trái là mê cung.

| Thành phần | Ý nghĩa |
|---|---|
| Compass | Ô bắt đầu |
| Treasure | Ô đích |
| Player | Vị trí hiện tại của agent |
| Monster | Đối thủ trong thuật toán Alpha-Beta |
| Trail | Vết di chuyển thủ công của player |
| Visited | Các ô thuật toán đã xét |
| Path | Đường đi hiện tại hoặc đường đi cuối |
| Next | Các bước được preview sắp tới |
| Dấu X đỏ | Ô / giá trị bị loại, ví dụ pruning hoặc Forward Checking loại khỏi domain |

Panel bên phải có các phần:

- Chọn nhóm thuật toán.
- Chọn thuật toán A và thuật toán B.
- Thông tin mê cung.
- Minimap.
- Bảng so sánh chỉ số.
- Log đường đi trực quan.
- Thanh tiến độ.
- Message bar ở cuối màn hình.

## 8. Các Chỉ Số Trong Bảng So Sánh

| Chỉ số | Ý nghĩa |
|---|---|
| `Cost` | Chi phí đường đi, thường là số bước di chuyển |
| `Time` | Thời gian chạy thuật toán |
| `Memory` | Bộ nhớ ước tính hoặc đo bằng `tracemalloc` |
| `Steps` | Số bước thuật toán đã sinh ra |
| `Visited` | Số ô đã duyệt / đã xét |
| `Found` | `YES` nếu tìm thấy goal, `NO` nếu thất bại, `RUN` nếu đang chạy |

## 9. Race Mode

Race Mode dùng để so sánh hai thuật toán trong cùng một nhóm theo thời gian thực.

Cách dùng:

1. Chọn một nhóm thuật toán.
2. Chọn `Thuat toan A`.
3. Chọn `Thuat toan B`.
4. Nhấn `M` để bật Race Mode.
5. Nhấn `PLAY` hoặc `Space`.

Khi Race Mode bật:

- Agent `A` chạy theo thuật toán A.
- Agent `B` chạy theo thuật toán B.
- Hai thanh tiến độ cập nhật song song.
- Bảng so sánh hiển thị số liệu live của cả hai thuật toán.

Nhấn `M` lần nữa để tắt Race Mode.

## 10. Forward Checking Trong Nhóm CSP

`Forward Checking` là thuật toán CSP chính trong project hiện tại.

Ý tưởng:

```text
Gán bước hiện tại -> kiểm tra trước domain của bước tiếp theo
Nếu domain tương lai rỗng -> loại nhánh sớm và quay lui
```

Trong project:

```text
Xi = vị trí ở bước thứ i
Domain[Xi] = các ô hàng xóm hợp lệ chưa đi qua
Constraint = không đi vào tường, không lặp ô, các bước phải kề nhau
```

Log của Forward Checking có các thông tin:

| Trường | Ý nghĩa |
|---|---|
| `var` | Biến đang gán, ví dụ `X5` |
| `value` | Ô được chọn cho biến đó |
| `removed` | Số giá trị bị loại khỏi domain tương lai |
| `next_domain` | Số lựa chọn còn lại cho bước tiếp theo |
| `h` | Khoảng cách Manhattan tới goal |

Dấu X đỏ trên mê cung cho biết các ô bị Forward Checking loại khỏi domain.

## 11. Alpha-Beta Và Monster

`Alpha-Beta` là thuật toán đối kháng:

```text
MAX = Player, muốn tới treasure
MIN = Monster, muốn bắt player
```

Mỗi turn được tách thành hai step:

```text
Turn n | MAX | Player chọn nước đi
Turn n | MIN | Monster phản ứng
```

Log Alpha-Beta có các thông tin:

| Trường | Ý nghĩa |
|---|---|
| `MAX` | Pha player chọn nước đi |
| `MIN` | Pha monster chọn nước đi |
| `score` | Điểm heuristic của trạng thái |
| `nodes` | Số node đã xét trong cây tìm kiếm |
| `prunes` | Số lần cắt nhánh alpha-beta |
| `cache` | Số lần dùng lại trạng thái từ transposition table |
| `Monster` | Vị trí hiện tại của monster |

Alpha-Beta có cơ chế:

- Phạt player nếu đi lại ô cũ.
- Phát hiện vòng lặp.
- Cache trạng thái để giảm tính toán lại.
- Cắt nhánh bằng alpha-beta pruning.

## 12. Depth Của Alpha-Beta

Depth là số nước đi mà Alpha-Beta nhìn trước.

Project hỗ trợ:

```text
Depth 3: nhanh, nhìn ngắn
Depth 5: cân bằng, khuyên dùng khi demo
Depth 7: nhìn xa hơn, chậm hơn
```

Cách đổi depth:

- Nhấn `Y`.
- Hoặc click chip `AB d5` ở góc trên panel.

Depth càng cao thì thuật toán duyệt nhiều node hơn. Vì vậy depth cao có thể thông minh hơn nhưng chạy chậm hơn.

## 13. Theme Và Preview

Nhấn `H` để đổi theme:

- `Stone Maze`
- `Dungeon`
- `Neon`
- `Space`

Nhấn `P` để bật / tắt preview đường sắp đi.

Preview giúp thấy trước vài bước kế tiếp của thuật toán. Khi cần quan sát đường đi sạch hơn, có thể tắt preview bằng `P`.

## 14. Cấu Trúc Thư Mục

```text
maze_game_use_algorithm_search/
├── main.py
├── config.py
├── README.md
├── assets/
├── core/
│   ├── game.py
│   ├── maze.py
│   └── monster.py
├── generation/
│   └── maze_generator.py
├── ui/
│   ├── renderer.py
│   ├── menu.py
│   └── combobox.py
└── algorithms/
    ├── uninformed/
    ├── informed/
    ├── local/
    ├── complex_env/
    ├── csp/
    └── adversarial/
```

## 15. Lỗi Thường Gặp

### Thiếu Pygame

Nếu gặp lỗi:

```text
ModuleNotFoundError: No module named 'pygame'
```

Chạy:

```powershell
pip install pygame
```

Hoặc dùng Python trong môi trường ảo:

```powershell
.\env\Scripts\python.exe -u main.py
```

### Chạy Sai Thư Mục

Nếu app không tìm thấy asset hoặc import lỗi, hãy đảm bảo terminal đang ở:

```powershell
D:\HCMUTE\trí tuệ nhân tạo\final project\maze_game_use_algorithm_search
```

Sau đó chạy lại:

```powershell
python -u main.py
```

### Đường Dẫn Có Dấu Tiếng Việt

Nếu PowerShell xử lý đường dẫn không ổn, hãy đặt đường dẫn trong dấu ngoặc kép:

```powershell
python -u "D:\HCMUTE\trí tuệ nhân tạo\final project\maze_game_use_algorithm_search\main.py"
```

## 16. Gợi Ý Khi Demo

- Dùng `Matrix 20 x 20` hoặc `30 x 30` để dễ quan sát.
- Dùng `Difficulty Balanced`.
- Với Alpha-Beta, dùng `Depth 5`.
- Bật Race Mode khi so sánh hai thuật toán cùng nhóm.
- Dùng phím `→` để đi từng bước khi cần giải thích chi tiết.
- Với CSP Forward Checking, chú ý các dấu X đỏ vì đó là phần thể hiện domain bị loại.
- Với Alpha-Beta, chú ý log `MAX/MIN`, `nodes`, `prunes`, `cache` để giải thích cơ chế cắt nhánh.
