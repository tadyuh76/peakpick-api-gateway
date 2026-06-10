# PeakPick API Gateway

API Gateway là cổng REST duy nhất cho frontend. Gateway không sở hữu database riêng; nhiệm vụ chính là route request đến các microservice phía sau và áp dụng xác thực/phân quyền cơ bản.

## Trách Nhiệm

- Nhận request từ frontend.
- Forward request đến Identity, Catalog, Order, Slot, Store Operations, Inventory, Notification và Analytics.
- Kiểm tra bearer token cho các route cần đăng nhập.
- Truyền `x-store-id` để service phía sau lọc dữ liệu theo cửa hàng.

## Chạy Local

```bash
pip install -r requirements.txt
uvicorn services.api_gateway.main:app --reload --port 8000
```

Trong hệ thống đầy đủ, nên chạy qua repo `peakpick-deployment` để Gateway có đủ service dependency.
