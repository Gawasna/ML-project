## Closes #<issue_number>

## Thông tin dataset

| | |
|---|---|
| **Member** | @github-username |
| **Chủ đề** | |
| **Số records** | |
| **File** | `data/train/<tên_file>.jsonl` |

## Ví dụ 3 records đại diện

```jsonl
{"instruction": "...", "input": "", "output": "..."}
```

## Checklist

- [ ] Branch tên đúng format `data/<tên>-<chủ đề>`
- [ ] Đã chạy `python scripts/validate_dataset.py --file <file>` — không có lỗi
- [ ] Chỉ thay đổi file trong `data/` — không đụng code
- [ ] Số records đạt yêu cầu trong issue
