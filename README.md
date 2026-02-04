# HRM Contact Export Tool

Automated tool để export danh sách liên hệ từ trna HRM system sang file Excel.

## 📋 Tính năng

- ✅ **CAS Authentication**: Tự động đăng nhập qua CAS (Central Authentication Service)
- ✅ **Session Caching**: Lưu session, không cần đăng nhập lại mỗi lần
- ✅ **Auto Re-login**: Tự động đăng nhập lại nếu session hết hạn
- ✅ **Pagination**: Tự động detect và xử lý phân trang
- ✅ **Data Export**: Export dữ liệu đầy đủ sang Excel
- ✅ **Project Filtering**: Lọc theo Project ID

## 🚀 Cài đặt

### 1. Clone/Tải project
```bash
cd employee
```

### 2. Tạo virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Cài dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình credentials
Sao chép `.env.example` → `.env` và điền thông tin:
```env
HRM_DOMAIN=trna
HRM_USERNAME=your_username
HRM_PASSWORD=your_password
```

## 📖 Cách sử dụng

### Lần đầu tiên (auto-login)
```bash
python main.py --project-id 1368
```
Script sẽ:
1. Đăng nhập vào CAS
2. Lưu session vào `.session`
3. Export dữ liệu sang `contacts.xlsx`

### Lần tiếp theo (dùng saved session)
```bash
python main.py --project-id 1368
```
Không cần login lại, tự động dùng session đã lưu.

### Force login mới
```bash
python main.py --project-id 1368 --force-login
```
Hủy session hiện tại, đăng nhập lại.

### Chỉ định file output
```bash
python main.py --project-id 1368 --out "my_contacts.xlsx"
```

### Dùng PHPSESSID trực tiếp
```bash
python main.py --project-id 1368 --phpsessid "ST-xxx"
```

## 📋 Command Options

| Option | Bắt buộc | Mặc định | Mô tả |
|--------|----------|----------|-------|
| `--project-id` | ✅ | - | Project ID để export |
| `--out` | ❌ | `contacts.xlsx` | Đường dẫn file output |
| `--phpsessid` | ❌ | - | PHPSESSID trực tiếp |
| `--force-login` | ❌ | - | Đặt lại session, login lại |
| `--sleep` | ❌ | `0.4` | Thời gian chờ giữa requests (giây) |
| `--base-url` | ❌ | Auto | Custom base URL |

## 📁 Cấu trúc Project

```
employee/
├── src/
│   ├── __init__.py          # Package init
│   ├── login.py             # CAS Authentication module
│   └── export.py            # Export logic
├── output/                  # Thư mục output (Excel files)
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── .env                     # Credentials (ignored in git)
├── .env.example            # Config template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🔑 Session Management

- Session lưu vào file `.session` (JSON format)
- `.session` **không được commit** vào git (xem `.gitignore`)
- Mỗi lần chạy sẽ:
  1. Kiểm tra `.session` có tồn tại không
  2. Nếu có → dùng saved session
  3. Nếu không → login mới
  4. Nếu hết hạn → auto re-login

## 📤 Output Files

Exported Excel files sẽ chứa:
- **Badge ID**: Mã nhân viên
- **Fullname (VN)**: Tên tiếng Việt
- **Fullname (EN)**: Tên tiếng Anh
- **Email**: Email
- **Work Phone**: Số điện thoại công việc
- **Position**: Vị trí công việc
- **Location**: Địa điểm
- **Projects/Groups**: Danh sách dự án
- **View Detail URL**: Link xem chi tiết
- **Resume URL**: Link CV
- **Project 1, 2, ...**: Các dự án (mở rộng thành cột riêng)

## 🐛 Troubleshooting

### "Cannot find table#resultTable"
Session có thể đã hết hạn:
```bash
python main.py --project-id 1368 --force-login
```

### "HTTP 500"
Project ID có thể không tồn tại hoặc không có quyền truy cập:
- Kiểm tra project ID
- Kiểm tra quyền truy cập trong HRM

### "Login failed"
Kiểm tra `.env`:
- `HRM_USERNAME` và `HRM_PASSWORD` có đúng không?
- CAS server có hoạt động không?
- Kiếm session cache: `Remove-Item .session -Force`

### "Module not found"
Cài dependencies:
```bash
pip install -r requirements.txt
```

## 🔧 Development

### Chạy lại từ đầu
```powershell
# Xóa session cache
Remove-Item .session -Force

# Đăng nhập lại
python main.py --project-id 1368
```

### Debug mode
Xem detailed output:
```bash
python main.py --project-id 1368 --sleep 1
```

## 📝 Notes

- Session có hiệu lực 24 giờ (thường)
- Mỗi lần chạy script sẽ update time last-used
- Dữ liệu được lưu dưới dạng Excel `.xlsx`
- Hỗ trợ phân trang tự động (unlimited records)
