# Current Task

> 打开这个文件夹先看这里。完成后把状态改成 DONE 并更新 00-roadmap.md 的勾选框。

## Task: 启动本地 k8s 集群并跑通第一个应用 [阶段 0]

**Status: DONE 2026-11-12(~11 weeks ahead of 2027-01-31 checkpoint)**
**Started: 2026-11-07 · 收官:Ingress + 清场完成**

### Checklist

- [x] 1. 启动集群:`orbctl start k8s`(2026-11-08;集群实际创建于 ~310 天前,本次为唤醒)
- [x] 2. 验证:`kubectl get nodes` → orbstack Ready, v1.36.5 (2026-11-08)
- [x] 3. 认识第一个对象:first-pod(nginx)完整生命周期 create→Running→exec 自证→delete(2026-11-08)
  - [x] 附:3 个追问对答案 CLOSED(2026-11-08:容器住在 OrbStack 的 k3s VM / Events=追加式事件日志 / Pod IP=cni0 内网,Mac curl 超时不可达)
- [x] 4. 部署第一个 Deployment + Service,浏览器访问(2026-11-08 完成:自愈演示验证 endpoints .15→.16 替换;localhost:30080 通;附带破案 .orbholder = kubernetes service .129)
- [x] 5. 滚动更新与回滚练习(2026-11-08 完成:watch 抓到"先 Ready 再杀旧"全程;坏镜像发布 44s 卡死期间 curl 不断流;undo 后 AGE 证明旧 RS 零牺牲;发现 config drift:undo 不回滚 yaml 文件)
- [x] 6.(新增 2026-11-08)Docker 基础单元,见 00-roadmap.md 阶段 0 新条目;拿现成 Tomcat 容器当教材
  - [x] L1 镜像分层 + 容器=进程(2026-11-09:smartpeak 581MB 千层饼考古;PID 381 vs PID 1 双视角;k8s Pod 在 docker ps 同框;开场抽考 2.5/4 创新高)
  - [x] L2 容器网络 + volume + Compose(2026-11-09 完成:bridge=vswitch/192.168.215 段;OrbStack 主进程持有全部 -p 端口,非 pstub;容器 IP 秒通而 Pod IP 被 VPN 大路由截胡进黑洞——netstat 验尸;volume 三部曲生死对照;compose 自动建网+按名 DNS;depends_on 顺序≠就绪;3 个报错全自修。开场抽考 1.5/4,错题 4 道待重抽。实验现场保留:compose 栈 18095 + l2-web 18080 + l2-data)
- [x] 7. 阶段 0 收尾:ConfigMap/Ingress + 多服务应用部署 ← **DONE 2026-11-12**
  - [x] ConfigMap 单元(2026-11-10:env/volume 双路注入 + ..data symlink 原子换指针 + 热/冷对照实验)
  - [x] yaml 结构专题课(用户主动叫停抄写:3 积木 + 2 阅读法则;8 病灶 debug 大戏横跨 yaml/k8s-schema/nginx-conf 三层,详见 log 0007)
  - [x] 多服务应用验收(2026-11-12:`/` → web frontend OK,`/api` → hello from api v1,6 站链路全绿)
  - [x] Ingress(2026-11-12:k3s 无 Traefik 验证 → 装 ingress-nginx 1.11.3,NodePort 32600;0004-ingress.yaml 路径分流 `/api`→api、`/`→web;describe 读出 endpoint 解析 Pod IP:5678)
  - [x] 清场(web-svc 已不存在、cm-dome 已删;保留 web:30081 作 NodePort vs Ingress 对照实物;Docker 实验残留决定仍挂账:compose 18095 / l2-web 18080 / l2-data 卷)

### Notes

- 报错直接贴给 Claude,附完整输出。
- 每完成一小步,更新 01-learning-log.md。
