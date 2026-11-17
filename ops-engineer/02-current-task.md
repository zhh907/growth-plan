# Current Task

> 打开这个文件夹先看这里。完成后把状态改成 DONE 并更新 00-roadmap.md 的勾选框。

## Task: 阶段 1 地基 —— Linux + 网络[Phase 1]

**Status: IN PROGRESS — Unit 1 开课 2026-11-12(secondary track;agent 仍是主轨)**
**Phase 0: DONE 2026-11-12(~11 weeks ahead of 2027-01-31 checkpoint)**

### 阶段 1 全局图

两条腿(CKA 已于 2026-11-17 移除,学习内容不变):

- **腿 A · Linux 主机视角**:进程与隔离 / cgroup / systemd / 文件系统与 overlayfs / 性能分析
- **腿 B · 网络**:TCP/IP 与状态机 / DNS / iptables(DNAT,即 kube-proxy 真身)/ tcpdump

已见 k8s 抽象 → 底层原语:Pod 网络 = pause + netns;limits = cgroup;Service = iptables DNAT;镜像分层 = overlayfs。

### Unit 1 — Linux 隔离三件套:进程 / namespace / cgroup

目标:能从宿主视角手造一个"容器",证明容器不是魔法。

- [x] L1 进程:fork/exec、PID 1、进程树、/proc(2026-11-13 DONE,log 0009:docker stop 10.2s vs --init 0.2s;tini 双职责 = 转发信号 + 收僵尸;孤儿过继 PID 1 已验证;bash -c 末命令原地 exec 实证;PID 跳号之谜留给 L2)
- [x] L2 namespace **CLOSED 2026-11-17(log 0014)**:pid ✅ uts ✅ net ✅ mnt ✅ overlay ✅ 两本账 ✅(4 天后纸面复验 0.5/3 → 4 句重砌 → 新增一层:--mount-proc 后旧账楼内不可见 → docker top 映射题 3/3)nsenter/lsns ✅(sleep 双号实证:楼外 20 / 楼内 5;钥匙用旧账、进门看新账;= docker exec 真身)
- [ ] L3 cgroup v2:CPU / 内存 / pids 限制(2026-11-17 开课,log 0015:树/旋钮已读,`0::/` 两本账回马枪;pids.max 实验撞 subtree_control 墙,根因已定位 = v2 控制器自上而下下放,恢复点 = `echo +pids > cgroup.subtree_control`;另欠 `docker ps` 认容器真名)
- [x] 收尾实验:unshare + chroot 手工造容器(2026-11-17 DONE,log 0016:三根柱子墙/账/地板亲手拼齐,$$ = /proc/self = 7 两本账对齐;--mount-proc 记账在旧树路径的坑实证;pivot_root 加固与 cgroup 电表接线留作后续)
- [ ] L3 收尾欠账:1) cgroup.procs 写入 EOPNOTSUPP 之谜(判别实验备好未跑,log 0015 恢复点);2) pids.max fork 被拒实操;3) 手工容器接上电表(把进程搬进 cgroup)

实验台(`docker run --rm -it --privileged ubuntu:24.04 bash`);macOS 本机没有 Linux namespace/cgroup,这是第一课要建立的边界感。

### Quiz debts(下次开场重抽)

- L1 三题(2026-11-13 抽考 0.5/3):CapEff/Seccomp 指纹;cgroup `0::/` 两段含义(0 = v2 统一层级 / 路径 = 树上位置);软限 vs 硬限(自抬软限只需 < 硬限)
- L2 五题(log 0010):房间模型一句话;`unshare --pid` 为什么必须 `--fork`;ps `lookup self` 崩溃机理;`$$` vs `readlink /proc/self`;`--mount-proc` 顺带拉动了哪个 namespace
- L2 下半场两题(log 0011,优先复验"两本账"):挂载表 = 两本账里的哪本账/可见性隔离从记账那刻成立;lowerdir vs upperdir(docker 三针注入 /etc/hostname+hosts+resolv.conf 彩蛋)
- Service 三层端口:port(ClusterIP 虚拟端口)/ targetPort(容器端口)/ nodePort(节点端口)
- Q5 补:describe 括号值 = Pod IP + 容器端口;5678 = targetPort 落地值
- Q3 补:YAML 法则一原话 —— 父 = 上方第一个更浅的键

### Notes

- 报错直接贴给 Claude,附完整输出。
- 每完成一小步,更新 01-learning-log.md。
