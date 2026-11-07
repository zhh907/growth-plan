# 高级运维工程师 · 两年成长计划

> 目标:2026-11 → 2028-11,从零基础到高级运维工程师(SRE 方向)+ 英语无障碍
> 定位差异化:**金融行业背景 + 运维 + 英语**组合(FX/贵金属/量化业务经验)
> 创建:2026-11-07

## 核心判断

AI 时代"会执行命令"不值钱,"知道系统为什么坏、坏了怎么办、怎么设计才不坏"更值钱。
两年内直接按高级标准练,不在初级技能上停留(被替代最快的区间)。

## 阶段路线

### 阶段 0:k8s 上手(2026-11 ~ 2026-12)← 当前
- [ ] 本机 OrbStack 集群启动(orbctl start k8s)
- [ ] 核心对象:Pod / Deployment / Service / ConfigMap / Ingress
- [ ] 独立部署一个多服务应用(含滚动更新与回滚)
- 环境:macOS arm64 / 32GB / OrbStack 2.2.5 / kubectl(上下文 orbstack)

### 阶段 1:地基 —— Linux + 网络(2027 Q1)
- [ ] Linux:进程 / cgroup / namespace / systemd / 文件系统 / 性能分析(top/vmstat/iostat/ss)
- [ ] 网络:TCP/IP / DNS / iptables / 抓包(tcpdump + Wireshark)
- [ ] **证书:CKA(Certified Kubernetes Administrator)** ← 求职硬通货

### 阶段 2:工程化(2027 Q2 ~ Q3)
- [ ] CI/CD:GitLab CI 或 GitHub Actions
- [ ] GitOps:ArgoCD
- [ ] IaC:Terraform + Ansible
- [ ] 实战项目:把自己的量化/EA 相关服务部署上 k8s,做完整交付流水线

### 阶段 3:可观测性 + 稳定性(2027 Q4 ~ 2028 Q1)
- [ ] Prometheus + Grafana + Loki 全套监控告警
- [ ] SLO / 错误预算 / 故障复盘方法论
- [ ] 混沌工程入门
- [ ] **证书:CKS 或云厂商认证(AWS SAP / 阿里云 ACP)**

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
- [ ] 检验点:2027 年 CKA 全英文考试 = 第一个硬性英语验收;2028 目标能英文面试

## 文件说明

- `00-roadmap.md`:本文件,阶段完成后打勾
- `01-learning-log.md`:每学一课追加一条(新条目放最上面),格式见文件内模板
- `02-current-task.md`:正在做的事,打开文件夹先看这个

## Milestones (checkpoints — slippage must trigger a review)

| Date | Must achieve | If missed |
|---|---|---|
| 2027-01-31 | Phase 0 done: local k8s cluster fluent (Pod/Deployment/Service/Ingress, rolling update & rollback) | secondary track — steal time from agent track sparingly |
| 2027-06-30 | **CKA passed** (all-English exam; doubles as English checkpoint) | core milestone — rebook within 3 months, review study hours |
| 2027-12-31 | Phase 2 done: CI/CD + GitOps + IaC; hosting the agent track's service | convergence checkpoint with agent track |
| 2028-06-30 | Phase 3 done: full observability stack + **CKS or cloud cert** | resume-completeness review |
| 2028-11 | Senior-ops capability validated: multi-cluster/HA design, incident drills | final deadline |

> Break point today: Phase 0 step 1 (`orbctl start k8s`) — resume anytime.
