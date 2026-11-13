# verify

`fixtures/expected/records.json` 不比较 Record-ID 的具体值，只检查：

- 文件以 warcinfo 开头
- 每个种子及文档点名的页面都有 request/response 对（或 revisit）
- `/page/a` 被抓两次时，第二次是 revisit，且 digest 与第一次 response 正文 sha256 一致
- `/charset/mixed` 的 Identified-Payload-Type 含 `charset=utf-8`
- `/partial/stream` 的 response 带 WARC-Truncated: disconnect
- 文件可按 `\r\n` 边界完整拆出所有记录，没有交错残块
