# warcframe

把本地夹具站的抓取结果写成 WARC/1.1。站点由本仓库提供。

```
python -m warcframe site --port 8764
python -m warcframe capture --base http://127.0.0.1:8764 --seeds fixtures/seeds.txt --out <out.warc> --workers 3
python -m warcframe verify --warc <out.warc> --expect fixtures/expected/records.json
```
