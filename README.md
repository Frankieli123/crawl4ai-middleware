# Crawl4AI MCP 服务器

这是一个MCP（模型上下文协议）服务器，用于将crawl4ai的网页抓取功能集成到支持MCP的应用程序中，如Cursor IDE。

## 功能

该服务器提供以下工具：

1. `create_crawl_task` - 创建网页抓取任务并获取任务ID
2. `get_crawl_result` - 根据任务ID获取抓取结果并保存到本地文件
3. `list_saved_results` - 列出已保存的抓取结果文件
4. `read_saved_result` - 读取已保存的抓取结果文件内容。

## 文件存储

所有抓取的网页内容会保存在服务器脚本同级目录下的 `url` 文件夹中，文件命名格式为：
`extracted_域名_任务ID_时间戳.txt`

这样可以避免因内容过大导致的显示问题，并可随时查看完整抓取结果。

## 安装依赖

```bash
pip install mcp[cli] httpx python-dotenv
```

## 配置

### 默认配置

服务器默认配置为：
- API地址：http://192.168.31.12:11235/
- API密钥：sk-3180623

### 环境变量配置

你可以通过以下两种方式配置环境变量：

1. **创建.env文件**

   在与`crawl4ai_server.py`同一目录下创建一个名为`.env`的文件，内容如下：

   ```
   CRAWL4AI_API_BASE=http://192.168.31.12:11235
   CRAWL4AI_API_KEY=sk-3180623
   OUTPUT_DIR=
   LOG_LEVEL=INFO
   ```

   **注意**：确保.env文件使用UTF-8编码保存，不要包含BOM头。

2. **设置系统环境变量**

   你也可以直接在操作系统中设置以下环境变量：
   
   - `CRAWL4AI_API_BASE` - API服务器地址
   - `CRAWL4AI_API_KEY` - API密钥
   - `OUTPUT_DIR` - 自定义输出目录（可选）
   - `LOG_LEVEL` - 日志级别（可选，默认INFO）

## 在Cursor中使用

1. 确保已安装所需依赖项
2. 修改Cursor的配置文件，路径通常为：
   - Windows: `%APPDATA%\Cursor\User\settings.json`

3. 在配置文件中添加以下内容：

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "python",
      "args": [
        "E:/APP/craw14ai-middleware/crawl4ai_server.py"
      ]
    }
  }
}
```

4. 重启Cursor以加载MCP服务器

## 使用示例

在Cursor中，你可以让AI助手使用这些工具：

1. "请帮我抓取网页 https://example.com"
2. "请获取任务ID为 abc123 的抓取结果"
3. "请列出已保存的抓取结果文件"
4. "请读取文件 extracted_example_com_abc123.txt 的内容" 