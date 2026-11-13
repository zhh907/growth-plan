# Current Task

> 打开这个文件夹先看这里。完成后把状态改成 DONE 并更新 00-roadmap.md 的勾选框。

## Task: 阶段 1 地基 —— Linux + 网络(CKA 导向)[Phase 1]

**Status: IN PROGRESS — Unit 1 开课 2026-11-12(secondary track;agent 仍是主轨)**
**Phase 0: DONE 2026-11-12(~11 weeks ahead of 2027-01-31 checkpoint)**

### 阶段 1 全局图

两条腿 + 一个靶子:

- **腿 A · Linux 主机视角**:进程与隔离 / cgroup / systemd / 文件系统与 overlayfs / 性能分析
- **腿 B · 网络**:TCP/IP 与状态机 / DNS / iptables(DNAT,即 kube-proxy 真身)/ tcpdump
- **靶子:CKA**(2027-06-30 硬里程碑,全英文)

已见 k8s 抽象 → 底层原语:Pod 网络 = pause + netns;limits = cgroup;Service = iptables DNAT;镜像分层 = overlayfs。

### Unit 1 — Linux 隔离三件套:进程 / namespace / cgroup

目标:能从宿主视角手造一个"容器",证明容器不是魔法。

- [x] L1 进程:fork/exec、PID 1、进程树、/proc(2026-11-13 DONE,log 0009:docker stop 10.2s vs --init 0.2s;tini 双职责 = 转发信号 + 收僵尸;孤儿过继 PID 1 已验证;bash -c 末命令原地 exec 实证;PID 跳号之谜留给 L2)
- [ ] L2 namespace:7 种隔离维度,重点 pid/net/mnt —— **下一步开课**;开场先解 PID 跳号之谜(6, 8/9 → ns_last_pid)
- [ ] L3 cgroup v2:CPU / 内存 / pids 限制
- [ ] 收尾实验:unshare + chroot 手工造容器

实验台(`docker run --rm -it --privileged ubuntu:24.04 bash`);macOS 本机没有 Linux namespace/cgroup,这是第一课要建立的边界感。

### Quiz debts(下次开场重抽)

- L1 三题(2026-11-13 抽考 0.5/3):CapEff/Seccomp 指纹;cgroup `0::/` 两段含义(0 = v2 统一层级 / 路径 = 树上位置);软限 vs 硬限(自抬软限只需 < 硬限)
- Service 三层端口:port(ClusterIP 虚拟端口)/ targetPort(容器端口)/ nodePort(节点端口)
- Q5 补:describe 括号值 = Pod IP + 容器端口;5678 = targetPort 落地值
- Q3 补:YAML 法则一原话 —— 父 = 上方第一个更浅的键

### Notes

- 报错直接贴给 Claude,附完整输出。
- 每完成一小步,更新 01-learning-log.md。
