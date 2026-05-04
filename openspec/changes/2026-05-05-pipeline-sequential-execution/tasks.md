# Tasks

- [ ] 新增 sequential runner 状态机。
- [ ] 新增 stage input builder，按阶段读取上游 artifact。
- [ ] 新增 stage output parser，保存对应 artifact。
- [ ] 新增 validator failure -> coder retry 逻辑。
- [ ] 新增 pipeline run trace 事件。
- [ ] 增加成功路径、失败重试、blocked 路径测试。
- [ ] 运行 `python -m pytest backend/tests -q` 并确认通过。
