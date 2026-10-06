---
name: docker-registry-network
description: GB10 上 Docker Hub 被墙 + 匿名限流，拉镜像用 mihomo 代理(7890) + skopeo 绕行方案（2026-08-30 sub2api 部署时验证）
metadata: 
  node_type: memory
  type: reference
  originSessionId: eddbe800-d9d0-49fb-b7a5-f375e363fc25
  modified: 2026-08-30T15:22:55.956Z
---

# Docker Hub 网络约束与绕行方案（GB10）

**环境事实**（2026-08-30 sub2api 部署时实测确认）：
- 直连 `registry-1.docker.io` **被墙**（curl 无响应/超时）
- Docker Hub 对匿名拉取**限流**（429 / `toomanyrequests`，IP 级 100 次/6h）
- daemon.json 已配 registry-mirrors（tencentyun + daocloud），但**只缓存常见镜像**（postgres/redis/hello-world），冷门镜像回源失败
- mihomo 代理在 `127.0.0.1:7890`（REST API `127.0.0.1:9090`，无 secret），节点 42 个，URLTest 组名 `auto`

**已生效的配置**：
- `/etc/systemd/system/docker.service.d/http-proxy.conf`：给 dockerd 配了 `HTTP_PROXY=http://127.0.0.1:7890`（daemon-reload + restart 生效）
- 注意：docker daemon 走代理拉 registry 仍不稳（可能 mirror 干扰），hello-world 能拉只是 mirror 缓存命中

**绕行方案（首选，已验证）**：skopeo 走 shell 代理 + docker load
```bash
skopeo copy --override-arch arm64 docker://<镜像>:<tag> docker-archive:/tmp/img.tar
docker load < /tmp/img.tar
docker tag <img-id> <镜像>:<tag>   # load 后是无 tag 的，要手动打 tag
```

**换节点绕过限流**：Docker Hub 限流按出口 IP。curl 走 7890 测 `https://registry-1.docker.io/v2/`，`401`=未限流，`429`=限流。用 mihomo API 切节点：
```bash
curl -s -X PUT http://127.0.0.1:9090/proxies/auto -H "Content-Type: application/json" -d '{"name":"nodeX"}'
```
2026-08-30 时 node0 未限流。URLTest 组会周期性测速自动恢复，无需手动切回。

**相关**：[[user-research-infrastructure]]、[[home-file-management-rules]]
