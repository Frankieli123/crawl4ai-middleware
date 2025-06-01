# 更新日志

## 1.0.1 (2025-06-08)

### 改进

- 修复与Python 3.13兼容性问题，解决cgi模块缺失导致的错误
- 更新httpx依赖版本要求，确保在Python 3.13环境下正常工作
- 优化错误处理和日志输出

## 1.0.0 (2025-05-26)

### 新特性

- 初始版本发布
- 添加`create_crawl_task`和`get_crawl_result`工具
- 添加`list_saved_results`和`read_saved_result`工具
- 添加自动创建url目录的功能
- 添加错误处理和日志记录