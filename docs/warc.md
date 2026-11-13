# 写入规则

`warcframe.warc.WarcWriter` 目前是一份不能用的草稿：记录分隔用的是 `\n` 而不是 WARC 要求的 `\r\n`，而且多个 worker 同时 `write_record` 时没有互斥，记录会交错。请把它修到能用，并补上 capture 流程。

## 记录类型

每个成功抓到的 URL 先写 `request`，再写 `response`。同一对记录用相同的 `WARC-Concurrent-To` 互相指向（request 指向随后的 response Record-ID，response 指向对应 request Record-ID），并用 `WARC-Target-URI` 记录规范化 URL（去掉 fragment，query 原样保留）。

第二次（以及之后）抓到同一规范化 URL 且响应正文的 sha256 与第一次完全相同，则第二次起改写 `revisit` 记录，不再重复写完整 response 正文：

- `WARC-Type: revisit`
- `WARC-Profile: http://netpreserve.org/warc/1.1/revisit/identical-payload-digest`
- `WARC-Payload-Digest: sha256:<hex>`
- `WARC-Refers-To: <第一次 response 的 Record-ID>`
- `Content-Length: 0`，后面仍要有结束用的空行

正文变化了就再写完整 response，digest 以新正文为准。

## 字符集

`/charset/mixed` 的 HTTP 头宣称 `charset=iso-8859-1`，但正文以 UTF-8 BOM 开头，并且 `<meta charset="utf-8">`。记录里的 HTTP 头必须原样保存；同时在 `WARC-Identified-Payload-Type` 写 `text/html; charset=utf-8`（以 BOM 和 meta 为准，而不是错误的头）。其它页若头和正文一致，则 Identified 类型与头一致。

## 截断

`/partial/stream` 会在声明的 Content-Length 之前断开。对应 response 必须带 `WARC-Truncated: disconnect`，`Content-Length` 以实际写入的块为准（HTTP 头加已收到的正文），不能丢弃这条记录。

## 并发

`--workers` 默认 3，多个线程/进程向同一个 warc 文件写。任何记录的字节流不能交错。文件开头先写一条 `warcinfo`（WARC-Type: warcinfo，正文可放软件名 warcframe/0.1）。

## 种子与发现

`fixtures/seeds.txt` 每行一个路径或 URL。抓取这些地址，并跟随页面里指向本 host 的链接，环要能结束。同一规范化 URL 在一次 capture 里按上面的规则最多写一次完整 response，重复遇到走 revisit。不要抓站外链接。
