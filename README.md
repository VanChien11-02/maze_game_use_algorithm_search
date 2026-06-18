# AI Maze Solver - Me Cung AI

Project minh hoa cac thuat toan tim duong trong me cung bang Pygame.
Ung dung cho phep chon nhom thuat toan, chon thuat toan A/B, xem tung buoc tim kiem va so sanh cac chi so thuc thi.

## Cach chay

Mo terminal tai thu muc project va chay:

```powershell
python -u main.py
```

Neu dang dung duong dan day du:

```powershell
python -u "d:\HCMUTE\trí tuệ nhân tạo\final project\maze_game_use_algorithm_search\main.py"
```

## Phim dieu khien chinh

| Phim | Chuc nang |
|---|---|
| `Space` | Pause / Resume hoac chay thuat toan dang chon |
| `Enter` | Chay lai thuat toan hien tai |
| `←` / `→` | Lui / tien tung buoc |
| `R` | Tao me cung moi |
| `Delete` | Xoa ket qua thuat toan |
| `T` | Doi toc do animation |
| `H` | Doi theme |
| `M` | Bat / tat Race Mode de so sanh realtime |
| `W/A/S/D` hoac `↑/↓/←/→` | Di chuyen player thu cong |
| `Esc` | Quay ve menu |

## Huong dan dung phim `M` - Race Mode

Phim `M` dung de bat/tat che do **Race Mode**, cho phep hai thuat toan A va B chay song song tren cung mot me cung.

### Cach dung

1. Chon **Nhom thuat toan** o panel ben phai.
2. Chon **Thuat toan A (hien thi)**.
3. Chon **Thuat toan B (tuy chon)**. Neu B la `Khong so sanh` thi Race Mode se khong co doi thu de chay.
4. Nhan phim `M` de bat Race Mode.
5. Nhan `PLAY` hoac `Space` de chay.

Khi Race Mode bat, man hinh se hien dong trang thai:

```text
RACE MODE: BFS vs DFS
```

Tren me cung:

- Agent **A** hien thi bang mau xanh la.
- Agent **B** hien thi bang mau xanh duong.
- Hai duong di duoc ve dong thoi de quan sat thuat toan nao di nhanh hon, mo rong nhieu hon hoac den dich truoc.

Trong bang **So sanh trong cung nhom**, cot B se doi tu:

```text
B final: DFS
```

sang:

```text
B live: DFS
```

Nghia la cac chi so cua ca A va B deu cap nhat realtime:

| Chi so | Y nghia |
|---|---|
| `Cost` | Do dai duong di hien tai |
| `Time` | Thoi gian uoc tinh theo tien do hien tai |
| `Memory` | Bo nho uoc tinh theo tien do hien tai |
| `Steps` | So buoc da chay / tong so buoc |
| `Visited` | So o da duyet tai thoi diem hien tai |
| `Found` | `RUN` neu dang chay, `YES` neu da tim thay dich |

Phia duoi bang co hai thanh tien do:

- Thanh A the hien tien do cua thuat toan A.
- Thanh B the hien tien do cua thuat toan B.

Nhan `M` lan nua de tat Race Mode. Khi tat Race Mode, thuat toan B se quay ve che do so sanh ket qua cuoi cung.
