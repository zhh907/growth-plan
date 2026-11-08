# Current Task

> 打开这个文件夹先看这里。完成后把状态改成 DONE 并更新 00-roadmap.md 的勾选框。

## Task: 启动本地 k8s 集群并跑通第一个应用 [阶段 0]

**Status: IN PROGRESS**
**Started: 2026-11-07 · 断点:第 4 条收尾(自愈演示 + 浏览器验证)+ 第 5 条**

### Checklist

- [x] 1. 启动集群:`orbctl start k8s`(2026-11-08;集群实际创建于 ~310 天前,本次为唤醒)
- [x] 2. 验证:`kubectl get nodes` → orbstack Ready, v1.36.5 (2026-11-08)
- [x] 3. 认识第一个对象:first-pod(nginx)完整生命周期 create→Running→exec 自证→delete(2026-11-08)
  - [x] 附:3 个追问对答案 CLOSED(2026-11-08:容器住在 OrbStack 的 k3s VM / Events=追加式事件日志 / Pod IP=cni0 内网,Mac curl 超时不可达)
- [x] 4. 部署第一个 Deployment + Service,浏览器访问(2026-11-08 完成:自愈演示验证 endpoints .15→.16 替换;localhost:30080 通;附带破案 .orbholder = kubernetes service .129)
- [x] 5. 滚动更新与回滚练习(2026-11-08 完成:watch 抓到"先 Ready 再杀旧"全程;坏镜像发布 44s 卡死期间 curl 不断流;undo 后 AGE 证明旧 RS 零牺牲;发现 config drift:undo 不回滚 yaml 文件)
- [ ] 5. 滚动更新与回滚练习
- [ ] 6.(新增 2026-11-08)Docker 基础单元,见 00-roadmap.md 阶段 0 新条目;拿现成 Tomcat 容器当教材

### Notes

- 报错直接贴给 Claude,附完整输出。
- 每完成一小步,更新 01-learning-log.md。
