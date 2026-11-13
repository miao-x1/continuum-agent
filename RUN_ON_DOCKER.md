# Continuum Docker 与评测

解压后进入本目录，在有 Docker 的机器上运行：

```sh
docker compose build
docker compose up -d
```

服务默认只监听本机 127.0.0.1:8765。首次启动前，通过环境变量设置
`CONTINUUM_PROVIDER`、`CONTINUUM_MODEL`、`CONTINUUM_API_KEY` 和
`CONTINUUM_BASE_URL`。不要把真实密钥写回本压缩包。

评测需要主机上的 Python 3.12、Docker、`datasets`，以及两个基准各自的官方评分器。
从本目录执行：

```sh
python -m pip install datasets
docker build -t continuum:benchmark .
PYTHONPATH=backend python -m continuum.benchmark swebench --limit 1 --output runs/swe-smoke.jsonl
PYTHONPATH=backend python -m continuum.benchmark featurebench --limit 1 --output runs/feature-smoke.jsonl
```

Windows PowerShell 中先运行 `$env:PYTHONPATH='backend'`，然后用
`py -3.12 -m continuum.benchmark ...`。去掉 `--limit 1` 可运行全量任务。
预测文件交给官方 `swebench eval verified` 或 `fb eval --split fast` 评分。
当前项目还没有在本机完成真实 Docker 构建和端到端评测验证。
