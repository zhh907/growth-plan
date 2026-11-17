# 高级运维工程师 · 两年成长计划

> 目标:2026-11 → 2028-11,从零基础到高级运维工程师(SRE 方向)+ 英语无障碍
> 定位差异化:**金融行业背景 + 运维 + 英语**组合(FX/贵金属/量化业务经验)
> 创建:2026-11-07

## 核心判断

AI 时代"会执行命令"不值钱,"知道系统为什么坏、坏了怎么办、怎么设计才不坏"更值钱。
两年内直接按高级标准练,不在初级技能上停留(被替代最快的区间)。

## 阶段路线

### 阶段 0:k8s 上手(2026-11 ~ 2026-12)— **DONE 2026-11-12(~11 weeks early)**
- [x] 本机 OrbStack 集群启动(orbctl start k8s)
- [x] **Docker 基础**(2026-11-08 加入):镜像与分层缓存 / 容器=被隔离的进程(呼应已见的 containerd-shim 与 pause)/ run·exec·logs·inspect / `-p` 端口映射与 bridge 网络 / volume 挂载 / Compose 多容器编排 —— 用自己现成的 Tomcat 容器当活教材
- [x] 核心对象:Pod / Deployment / Service / ConfigMap / Ingress
- [x] 独立部署一个多服务应用(含滚动更新与回滚)
- 环境:macOS arm64 / 32GB / OrbStack 2.2.5 / kubectl(上下文 orbstack)

### 阶段 1:地基 —— Linux + 网络(2027 Q1)
- [ ] Linux:进程 / cgroup / namespace / systemd / 文件系统 / 性能分析(top/vmstat/iostat/ss)
- [ ] 网络:TCP/IP / DNS / iptables / 抓包(tcpdump + Wireshark)

> 2026-11-17 决定:**CKA 证书从计划中移除**(用户决策)。学习内容不变,只去考试;能力验收改为 Phase 1 收尾的实操复盘。

### 阶段 1.5:会用层补全(2026-11-17 增补;排在网络腿之后、Phase 2 深究之前)

> 原则:先会用再深究。Phase 0 只见过"无状态 web"一种场景,这里补齐常用对象与 docker 构建技能,再进 Phase 2 拆内幕。

**docker 构建技能(先行:先有镜像,再谈部署;最重缺口:Dockerfile 从未写过):**
- [ ] Dockerfile 编写:FROM/COPY/RUN/ENTRYPOINT/CMD、层缓存与书写顺序
- [ ] 多阶段构建(multi-stage)瘦身
- [ ] 构建并推送到 registry(tag 规范)
- [ ] `--cpus` / `--memory` 启动限制(cgroup 的 docker 落地口)
- [ ] healthcheck / restart 策略 / compose healthcheck 进阶

**k8s 对象补全:**
- [ ] StatefulSet(有状态应用)/ DaemonSet(每节点一个)/ Job + CronJob(跑完即退/定时)
- [ ] PV / PVC 存储卷(从 docker volume 升级到 k8s 卷体系)
- [ ] Secret(加密版 ConfigMap)/ ConfigMap 进阶
- [ ] HPA 自动扩缩容 / resource limits 实操(接 cgroup)
- [ ] Helm 应用打包 / namespace 与 RBAC 基础

**验收方式:每个对象配一个最小实操案例(自造 fixture),跑通并写入 log——不是纸面过。**

### 阶段 2:工程化 + k8s 专家向(2027 Q2 ~ Q3)
- [ ] CI/CD:GitLab CI 或 GitHub Actions
- [ ] GitOps:ArgoCD
- [ ] IaC:Terraform + Ansible
- [ ] 实战项目:把自己的量化服务部署上 k8s,做完整交付流水线

**k8s 专家向(2026-11-17 增补,替代 CKA 的能力路线):**
- [ ] 控制面内幕:etcd(唯一状态库)/ 调度器打分 / controller reconcile 循环 / kube-proxy 与 iptables DNAT 真身(与腿 B iptables 汇合)
- [ ] CRD + Operator 开发(kubebuilder):把一个运维动作做成自定义控制器
- [ ] 插件体系:CNI 网络插件原理(flannel/Calico)/ CSI 存储
- [ ] 故障深水区排障实战:节点 NotReady / OOMKilled 定位 / CoreDNS 故障 / etcd 变慢 / 镜像拉取失败链路

### 阶段 3:可观测性 + 稳定性(2027 Q4 ~ 2028 Q1)
- [ ] Prometheus + Grafana 全套监控告警
- [ ] 日志栈:ELK(Elasticsearch/Logstash/Kibana)实操 + 与 Loki 轻量方案的选型对比(索引型 vs 标签型,资源成本与查询场景)
- [ ] SLO / 错误预算 / 故障复盘方法论
- [ ] 混沌工程入门
- [ ] 性能分析深挖:perf / 火焰图 / 压测工具链(k6 或 wrk)——从"看指标"到"定位代码级瓶颈"
- [ ] k8s 安全加固:RBAC 最小权限 / PodSecurity / 镜像扫描 / 非 root 运行(原阶段 4 部分内容提前)
- [ ] eBPF 观测初阶(可选,视机会):现代 SRE 增值方向

> 2026-11-17:CKS/云认证不再作为硬目标(同 CKA 决定),安全加固内容保留、只去考试。

### 阶段 4:高阶 + 变现验证(2028)
- [ ] 多集群 / 高可用架构设计
- [ ] 成本优化(FinOps)/ k8s 安全加固
- [ ] GPU / k8s AI 基建运维(AI 时代最陡峭的增值方向,视机会)
- [ ] 求职/接项目验证:「金融行业 + 运维」组合拳

## 贯穿全程的三个追问(每次操作必问)

1. 这条命令改了什么底层状态?
2. 坏了怎么排查?
3. 生产环境敢不敢这么做?

## 英语并行轨道(与阶段路线同步,不单独排期)

**原则:英语不单独学,绑定技术场景学 —— 用进废退。**

- [ ] 读:所有技术文档只读英文官方版(kubernetes.io、redis.io 等),禁止先看中文翻译
- [ ] 报错:终端报错直接读原文,先自己理解再查,积累到 01-learning-log.md
- [ ] 术语:每个 k8s/运维概念同时记英文术语(Pod not 容器组, Deployment not 部署)
- [ ] 写:GitHub commit message / 代码注释 / 学习日志全部英文(01-learning-log.md 已是英文)
- [ ] 听/说:每周 1~2 次英文技术视频(KubeCon 演讲、YouTube),后期尝试英文复盘
- [ ] 检验点:2028 目标能英文面试(2026-11-17 起 CKA 考试不再作为英语验收,改为日常英文输出积累)

## 文件说明

- `00-roadmap.md`:本文件,阶段完成后打勾
- `01-learning-log.md`:每学一课追加一条(新条目放最上面),格式见文件内模板
- `02-current-task.md`:正在做的事,打开文件夹先看这个

## Milestones (checkpoints — slippage must trigger a review)

| Date | Must achieve | If missed |
|---|---|---|
| 2027-01-31 | Phase 0 done: local k8s cluster fluent (Pod/Deployment/Service/Ingress, rolling update & rollback) | secondary track — steal time from agent track sparingly |
| 2027-06-30 | Phase 1 done: Linux + networking legs complete, verified by a hands-on capstone review (CKA dropped 2026-11-17) | core milestone — review study hours if missed |
| 2027-12-31 | Phase 2 done: CI/CD + GitOps + IaC; hosting the agent track's service | convergence checkpoint with agent track |
| 2028-06-30 | Phase 3 done: full observability stack + **CKS or cloud cert** | resume-completeness review |
| 2028-11 | Senior-ops capability validated: multi-cluster/HA design, incident drills | final deadline |

> Break point today (2026-11-12): **Phase 0 CLOSED**. Next decision: start Phase 1 (Linux + networking, CKA-oriented) — ops is secondary, agent track primary until its pattern tour completes.
